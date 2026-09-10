---
title: Kubernetes 服务资源：Service 到底虚拟出了什么，Ingress 和 Gateway API 差在哪
description: 拆解 Kubernetes 服务资源：ClusterIP 只是 iptables 规则里的一个记号、真正转发流量的是 kube-proxy、记录后端地址的是 EndpointSlice、Ingress 是 L7 的流量入口、Gateway API 把入口拆成 GatewayClass/Gateway/HTTPRoute 三个角色。并串起一条从 DNS 到 Pod 的完整流量链路。
authors:
  - hfei
date: 2026-09-09
categories:
  - Kubernetes
tags:
  - Kubernetes
  - Service
  - Ingress
  - EndpointSlice
  - Gateway API
  - kube-proxy
  - 云原生
---

# Kubernetes 服务资源：Service 到底虚拟出了什么，Ingress 和 Gateway API 差在哪

## Service 不是负载均衡器，是一个"稳定的名字"

Pod 的 IP 会变：重建、扩容、迁移，IP 都可能换。Service 解决的是"**用一个稳定的地址找到一群会变的 Pod**"。

关键要先想通一件事：ClusterIP 那个 IP 本身不承载任何流量，它只是 iptables/IPVS 规则里的一个"记号"，真正把流量送到 Pod 的是 kube-proxy。[Kube-Proxy 详解](../network/kube-proxy.md) 和 [ClusterIP 为什么 ping 不通](../network/clusterip-link-deep.md) 把这条转发链路拆到了规则级别，这里只给结论：

- Service 的 selector 选出后端 Pod；
- kube-proxy watch Service 和 Pod 变化，在每台节点上维护转发规则；
- 请求打到 ClusterIP，被规则 DNAT 到某个后端 Pod。

所以"Service 挂了"通常是"kube-proxy 没同步规则"或"selector 没选中任何 Pod"，而不是 Service 对象本身出了事。

## Service 四种类型

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  type: ClusterIP          # 默认
  selector:
    app: nginx
  ports:
    - port: 80             # Service 端口
      targetPort: 8080     # Pod 端口
```

| type | 作用 | 典型场景 |
|---|---|---|
| ClusterIP | 集群内稳定 IP | 集群内互访（默认） |
| NodePort | 在每节点开一个固定端口 | 调试、少量对外 |
| LoadBalancer | 调云厂商 LB | 云上生产对外 |
| ExternalName | CNAME 到外部域名 | 对接集群外服务 |

四种类型的 YAML 差别很小，但行为差异很大：

```yaml
# NodePort：在每节点开一个固定端口（30000-32767）
apiVersion: v1
kind: Service
metadata:
  name: nginx-np
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080   # 不写则自动分配
```

```yaml
# LoadBalancer：调云厂商 LB 分配一个外部 IP
apiVersion: v1
kind: Service
metadata:
  name: nginx-lb
spec:
  type: LoadBalancer
  selector:
    app: nginx
  ports:
    - port: 80
      targetPort: 8080
```

```yaml
# ExternalName：没有 selector，直接把名字 CNAME 到外部
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: db.example.com
```

LoadBalancer 在裸金属上没云厂商支持时会一直 `Pending`，这时候用 MetalLB 这类方案补齐。NodePort 的流量路径里有个著名的 SNAT 问题——外部流量经过 NodePort 时源 IP 会被改写，[SNAT 三种场景](../network/snat-three-scenarios.md) 里有完整实测。

### headless Service 与 externalTrafficPolicy

两个容易被忽略的配置：

```yaml
spec:
  clusterIP: None               # headless：不给 ClusterIP，直接暴露 Pod IP
  externalTrafficPolicy: Local  # 外部流量只发给本节点的 Pod，保留源 IP
```

- **headless**（`clusterIP: None`）：DNS 查询直接返回所有 Pod IP，配合 StatefulSet 给每个 Pod 稳定 DNS 名（[工作负载资源](workloads.md)）；
- **externalTrafficPolicy: Local**：NodePort/LoadBalancer 场景下，流量只路由到同节点的 Pod，避免跨节点二次转发，也保留了客户端源 IP（代价是流量不均）。

## kube-proxy：iptables 还是 IPVS

Service 规则最终由 kube-proxy 落地，它有两种模式：

| 模式 | 实现 | 特点 |
|---|---|---|
| iptables | 逐条 DNAT 规则 | 成熟稳定，规则多了性能下降 |
| IPVS | 内核 LVS | 大规模 Service 性能更好，支持更多负载均衡算法 |

```bash
kubectl -n kube-system get ds kube-proxy -o yaml | grep -i mode
# mode: iptables  或  mode: ipvs
```

iptables 模式下规则是链式匹配，几千个 Service 后转发延迟会明显上升；IPVS 用哈希表，规模上去后优势明显。这条转发链路的细节在 [Kube-Proxy 详解](../network/kube-proxy.md)。

## EndpointSlice：真正记录后端地址的

Service 自己不存 Pod 地址。真正记录"这个 Service 背后有哪些 Pod IP"的是 EndpointSlice（早期叫 Endpoints）：

```bash
kubectl get endpointslice
NAME          ADDRESSTYPE   PORTS   ENDPOINTS                 AGE
nginx-abc12   IPv4          8080    10.244.1.5,10.244.2.9     3d
```

kube-proxy 实际消费的就是 EndpointSlice 里的这些 IP。为什么从 Endpoints 拆成 EndpointSlice？单个 Endpoints 对象在超大规模 Service（几万 Pod）下会膨胀到几 MB，watch 一次成本很高；切成多个 Slice（默认每个 100 个地址）后按需增量同步，这也是大规模集群控制 API Server 压力的一部分。

Pod 没就绪时会被从 EndpointSlice 里摘掉（就绪探针）。所以"Service 不通"要查的就三样：selector 对不对、EndpointSlice 里有没有就绪地址、kube-proxy 规则有没有同步。

## Ingress：南北向的 L7 入口

Service 是 L4 的，Ingress 是 L7 的（HTTP/HTTPS）：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - www.example.com
      secretName: example-tls       # TLS 证书
  rules:
    - host: www.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

`pathType` 有三种：`Prefix`（前缀匹配，最常用）、`Exact`（精确匹配）、`ImplementationSpecific`（交给 controller 自己定义）。多个 path 命中时，**最长前缀优先**，所以 `/api` 写在 `/` 前面。

Ingress 只是"路由声明"，真正干活的是 Ingress Controller（nginx-ingress、traefik 等），证书终止也发生在这一层。链路细节在 [Ingress 详解](../network/ingress.md)。

`ingressClassName` 指向 IngressClass，用来指定"这条规则由哪个 controller 处理"——集群里装了多个 ingress controller 时，这个字段就是分拣器。

## Gateway API：Ingress 的下一代，但还没完全接班

Gateway API 把"入口"拆成三个角色：

- **GatewayClass**：实现（谁提供能力）；
- **Gateway**：部署（入口实例）；
- **HTTPRoute**：路由（怎么转发）。

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: web
spec:
  parentRefs:
    - name: web-gateway
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: web
          port: 80
```

相比 Ingress 的优势：更细的流量治理（按 header 路由、权重分流、跨命名空间引用），并且把"基础设施团队管 Gateway、业务团队管 Route"的职责边界画清楚了。代价是生态还在追赶，很多 controller 支持不完整。短期不必急着迁移，新项目值得关注。

## 排错：流量不通的三段式排查

```bash
kubectl get svc,endpointslice,ingress       # 看对象在不在、就绪没有
kubectl describe svc <svc>                  # 看 Events 和 Endpoints
kubectl -n kube-system logs <kube-proxy>    # 看转发规则有没有同步
```

- DNS 解析不到 → 查 CoreDNS（[Service 域名解析](../network/service-dns-to-clusterip.md)）；
- 解析到了但连不通 → 查 EndpointSlice 有没有就绪地址、kube-proxy 规则；
- 通了但源 IP 不对 → 查 `externalTrafficPolicy` 和 [SNAT](../network/snat-three-scenarios.md)。

## 一条完整流量路径串起来

```mermaid
flowchart LR
    A["用户请求<br/>www.example.com"] --> B["DNS 解析"]
    B --> C["Ingress Controller"]
    C --> D["Service<br/>ClusterIP"]
    D --> E["kube-proxy<br/>iptables/IPVS"]
    E --> F["EndpointSlice<br/>就绪 Pod"]
    F --> G["Pod"]
```

这条链路上每一段本站都有对应拆解：[DNS → ClusterIP](../network/service-dns-to-clusterip.md)、[ClusterIP 链路](../network/clusterip-link-deep.md)、[一行 curl 的完整旅程](../network/curl-full-link.md)。

## 推荐阅读

- [Kube-Proxy 详解](../network/kube-proxy.md) — Service 流量转发的核心组件
- [ClusterIP 为什么 ping 不通](../network/clusterip-link-deep.md) — iptables 链路级拆解
- [CoreDNS：Service 域名怎么解析成 ClusterIP](../network/service-dns-to-clusterip.md) — 服务发现的第一步
- [Ingress 详解](../network/ingress.md) — 域名、HTTPS 与流量入口
- [SNAT 三种场景](../network/snat-three-scenarios.md) — NodePort 的源地址改写
- [一行 curl 的完整旅程](../network/curl-full-link.md) — 从 DNS 到 conntrack 的全链路