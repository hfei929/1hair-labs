---
title: Kubernetes 服务资源详解：Service、Ingress、Gateway API 一文读懂
description: 深入理解 Kubernetes 服务资源体系，包括 Service、EndpointSlice、Ingress、IngressClass、Gateway API 的作用、关系以及最佳实践。
keywords:
  - Kubernetes Service
  - Kubernetes Ingress
  - Gateway API
  - EndpointSlice
  - Kubernetes服务发现
  - Kubernetes网络
tags:
  - Kubernetes
  - Service
  - Networking
author: HairLabs | 一根头发丝的宽度
---

# Kubernetes 服务资源详解：Service、Ingress、Gateway API 一文读懂

## 文章摘要

在 Kubernetes 中，Pod 是应用运行的载体，但 Pod IP 并不固定。

当 Pod 重建、扩容或迁移节点时，其 IP 地址可能发生变化。

为了让应用能够被稳定访问，Kubernetes 提供了一套完整的服务资源体系。

本文将从资源对象的角度，系统讲解 Service、EndpointSlice、Ingress、IngressClass 以及 Gateway API 的作用与关系。

---

## 学习目标

阅读完本文后，你将掌握：

- Kubernetes 服务资源体系
- Service 的作用
- EndpointSlice 的作用
- Ingress 的作用
- IngressClass 的作用
- Gateway API 的定位
- 服务发现流程
- 对外访问流程

---

## 适用人群

本文适合：

- Kubernetes 初学者
- Linux 运维工程师
- DevOps 工程师
- 云原生学习者
- Kubernetes 面试准备人员

---

## 什么是服务资源？

服务资源（Service Resources）主要解决两个问题：

### 服务发现（Service Discovery）

找到目标 Pod。

---

### 流量访问（Traffic Access）

让用户能够访问应用。

---

例如：

```text
Browser

↓

Ingress

↓

Service

↓

Pod
```

---

或者：

```text
Pod-A

↓

Service

↓

Pod-B
```

---

服务资源就是实现这些能力的核心对象。

---

## Kubernetes 服务资源体系

整体结构如下：

```text
Ingress

↓

Service

↓

EndpointSlice

↓

Pod
```

---

在较新的架构中：

```text
Gateway

↓

HTTPRoute

↓

Service

↓

EndpointSlice

↓

Pod
```

---

## Service

Service 是 Kubernetes 最基础的服务资源。

---

作用：

```text
提供稳定访问入口
```

---

例如：

```text
Pod-A
10.244.1.10

Pod-B
10.244.2.15

Pod-C
10.244.3.20
```

---

Service：

```text
10.96.0.100
```

---

客户端只访问：

```text
10.96.0.100
```

即可。

---

### Service 类型

常见类型：

| 类型 | 作用 |
|--------|--------|
| ClusterIP | 集群内部访问 |
| NodePort | 节点端口访问 |
| LoadBalancer | 云负载均衡 |
| ExternalName | 外部服务映射 |

---

生产环境最常见：

```text
ClusterIP
```

---

## EndpointSlice

很多人知道 Service。

却不知道真正记录 Pod 地址的是：

```text
EndpointSlice
```

---

查看：

```bash
kubectl get endpointslice
```

---

例如：

```text
10.244.1.10

10.244.2.15

10.244.3.20
```

---

这些才是真正的后端地址。

---

### 为什么需要 EndpointSlice？

早期 Kubernetes 使用：

```text
Endpoints
```

对象。

---

当集群规模变大：

```text
数百

数千

数万 Pod
```

时。

---

Endpoints 对象会变得非常庞大。

---

因此引入：

```text
EndpointSlice
```

进行拆分管理。

---

### EndpointSlice 优势

- 更高扩展性
- 更低 API 压力
- 更适合大规模集群

---

## Ingress

Ingress 是 Kubernetes 最常见的南北向流量入口资源。

---

作用：

```text
HTTP

HTTPS

域名访问
```

管理。

---

例如：

```text
www.example.com
```

---

转发：

```text
web-service
```

---

或者：

```text
api.example.com
```

---

转发：

```text
api-service
```

---

## Ingress 能做什么？

支持：

### 域名路由

```text
user.example.com

order.example.com
```

---

### 路径路由

```text
/api

/admin

/web
```

---

### HTTPS

TLS 证书管理。

---

### 负载均衡

请求分发。

---

## IngressClass

很多人忽略这个资源。

---

作用：

```text
指定Ingress由谁处理
```

---

例如：

```text
nginx
```

---

或者：

```text
traefik
```

---

或者：

```text
apisix
```

---

IngressClass 类似：

```text
驱动选择器
```

---

例如：

```yaml
ingressClassName: nginx
```

---

表示：

```text
由 Nginx Ingress Controller 处理
```

---

## Gateway API

这是 Kubernetes 未来重点发展的方向。

---

可以理解为：

```text
Ingress 下一代标准
```

---

相比 Ingress：

支持更复杂流量治理。

---

主要资源：

### GatewayClass

定义实现。

---

### Gateway

定义入口。

---

### HTTPRoute

定义路由规则。

---

关系：

```text
GatewayClass

↓

Gateway

↓

HTTPRoute

↓

Service
```

---

## Service 与 Ingress 的区别

很多面试都会问。

| 项目 | Service | Ingress |
|--------|--------|--------|
| 作用 | 服务发现 | 流量入口 |
| 工作层级 | L4 | L7 |
| 访问对象 | Pod | Service |
| HTTPS | 不负责 | 支持 |

---

简单记忆：

```text
Service 找到 Pod

Ingress 找到 Service
```

---

## Gateway API 与 Ingress 的区别

| 项目 | Ingress | Gateway API |
|--------|--------|--------|
| 功能 | 基础 | 强大 |
| 扩展性 | 一般 | 很强 |
| 路由能力 | 有限 | 丰富 |
| 多团队管理 | 较弱 | 优秀 |

---

未来趋势：

```text
Gateway API
```

逐步替代部分 Ingress 场景。

---

## 服务发现流程

Pod 访问：

```text
mysql.default.svc.cluster.local
```

---

流程：

```text
Pod

↓

CoreDNS

↓

Service

↓

EndpointSlice

↓

Pod
```

---

整个过程无需关心 Pod IP。

---

## 用户访问流程

访问：

```text
https://www.example.com
```

---

流程：

```text
Browser

↓

DNS

↓

Ingress

↓

Service

↓

EndpointSlice

↓

Pod
```

---

这是生产环境最常见流量路径。

---

## 生产环境最佳实践

### 内部访问使用 ClusterIP

默认推荐。

---

### 对外访问统一走 Ingress

避免大量 NodePort。

---

### 使用 EndpointSlice

不要依赖旧 Endpoints。

---

### 新项目关注 Gateway API

未来发展方向。

---

## 常见故障排查

查看 Service：

```bash
kubectl get svc
```

---

查看 EndpointSlice：

```bash
kubectl get endpointslice
```

---

查看 Ingress：

```bash
kubectl get ingress
```

---

查看 IngressClass：

```bash
kubectl get ingressclass
```

---

查看 Gateway：

```bash
kubectl get gateway
```

---

查看 HTTPRoute：

```bash
kubectl get httproute
```

---

## 面试常见问题

### Service 的作用是什么？

提供稳定访问入口。

---

### EndpointSlice 的作用是什么？

维护后端 Pod 地址。

---

### Ingress 的作用是什么？

管理 HTTP/HTTPS 流量入口。

---

### IngressClass 是什么？

指定 Ingress Controller。

---

### Gateway API 是什么？

下一代 Kubernetes 流量管理标准。

---

## FAQ

### 没有 Service 可以访问 Pod 吗？

可以。

但不推荐。

---

### Ingress 可以直接访问 Pod 吗？

不能。

通常通过 Service。

---

### Gateway API 会取代 Ingress 吗？

短期不会。

长期可能逐步替代部分场景。

---

## 总结

Kubernetes 服务资源体系负责实现服务发现与流量访问。

其中：

- Service 提供稳定访问入口
- EndpointSlice 管理后端地址
- Ingress 管理 HTTP/HTTPS 流量
- IngressClass 指定控制器
- Gateway API 提供下一代流量治理能力

可以记住一句话：

> Service 连接 Pod，Ingress 连接用户，而 Gateway API 正在定义 Kubernetes 流量管理的未来。

---

## 相关阅读

- [Kubernetes Service 工作原理]()
- [Kubernetes Ingress 工作原理]()
- [Kubernetes Kube-Proxy 工作原理]()
- [Kubernetes CNI 工作原理]()
- [Kubernetes Gateway API 实战]()