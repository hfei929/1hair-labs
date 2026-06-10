# Kubernetes 网络资源

## 概述

Kubernetes 网络资源管理 Pod 与 Pod 之间、Pod 与外部世界的流量。

## 三个属粒

### 1. Pod-to-Pod 网络
Pod 可以自由空间互相一上的 Pod 通达。CNI 插件负责实现。

### 2. Pod-to-Service 网络
Pod 可以通过 Service ClusterIP 访问后端 Pod。

### 3. External-to-Service 网络
外部世界可以通过 NodePort、LoadBalancer、Ingress 访问 Service。

## NetworkPolicy

### 概衡
NetworkPolicy 是 Kubernetes 的网络防火墙，定义 Pod 之间的流量控制。

### 入站流量控制
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - protocol: TCP
      port: 8080
```

## 常见问题

**Q：NetworkPolicy 不起作用？**
A：检查：
1. CNI 插件是否支持 NetworkPolicy（Flannel 不支持）
2. NetworkPolicy 的 podSelector 是否遥配
3. Pod 是否有正确的 label

**Q：不同 Namespace Pod 无法通信？**
A：这样是正常的。不同 Namespace 是模拟的隔离，Pod 互通信需要使用包含 Namespace 信息的 DNS 名称。
