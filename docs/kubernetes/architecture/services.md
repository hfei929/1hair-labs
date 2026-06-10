# Kubernetes 服务资源

## 概述

服务资源（Service）是 Kubernetes 将一组 Pod 汇聚化为一个网络端点的方法。Service 提供了一个稳定的 IP 地址和 DNS 名称，客户端或上流 Pod 就可以通过 Service 访问后端 Pod。

## 服务的下游本质

Service 简化了 Pod 发现和负载均衡是量。它流量转发到后端 Pod 的是事 Kube Proxy 负责。

## 服务类型

### 1. ClusterIP（默认）
只在集群内不可连接。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

### 2. NodePort
流量从Node 的一个特定端口上进入。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: NodePort
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30000
```

### 3. LoadBalancer
宜于云环境。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: LoadBalancer
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

## 常见问题

**Q：Service IP 无法访问？**
A：查看：Endpoint 是否正常、资源选择器是否匹配、Kube Proxy 是否正常运行。
