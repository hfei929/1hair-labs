---

title: Kubernetes Service 详解：ClusterIP、NodePort、LoadBalancer 一次讲透
description: 深入理解 Kubernetes Service 工作原理，包括 ClusterIP、NodePort、LoadBalancer、ExternalName、Endpoint、Service 发现机制以及生产环境最佳实践。
keywords:

  - Kubernetes Service
  - ClusterIP
  - NodePort
  - LoadBalancer
  - Kubernetes服务发现
  - Kubernetes网络
tags:
  - Kubernetes
  - Service
  - Kubernetes网络
author: HairLabs

---

# Kubernetes Service 详解：ClusterIP、NodePort、LoadBalancer 一次讲透

## 文章摘要

在 Kubernetes 中，Pod 是应用运行的最小单位，但 Pod 的 IP 地址并不固定，可能因为重建、扩缩容或节点故障而发生变化。

为了让应用拥有稳定的访问入口，Kubernetes 引入了 Service 资源。

本文将详细讲解 Service 的设计目的、工作原理、四种常见 Service 类型以及生产环境中的使用场景。

---

## 学习目标

阅读完本文后，你将掌握：

* 为什么需要 Service
* Service 的工作原理
* ClusterIP 机制
* NodePort 机制
* LoadBalancer 机制
* ExternalName 机制
* Endpoint 与 EndpointSlice
* 服务发现原理
* 常见故障排查方法

---

## 适用人群

本文适合：

* Kubernetes 初学者
* Linux 运维工程师
* DevOps 工程师
* 云计算学习者
* Kubernetes 面试准备人员

---

## 为什么需要 Service？

假设我们部署一个 Deployment：

```yaml
replicas: 3
```

系统创建：

```text
nginx-abc
10.244.1.10

nginx-def
10.244.2.15

nginx-ghi
10.244.3.20
```

此时用户访问：

```text
10.244.1.10
```

似乎没有问题。

---

### Pod 重建问题

如果某个 Pod 被删除：

```bash
kubectl delete pod nginx-abc
```

系统重新创建：

```text
nginx-jkl
10.244.5.12
```

原 IP 已失效。

---

### Pod 扩容问题

扩容：

```yaml
replicas: 5
```

又新增：

```text
10.244.4.18
10.244.5.20
```

客户端根本不知道这些变化。

---

因此：

> 不能直接依赖 Pod IP 对外提供服务。

---

## Service 是什么？

可以把 Service 理解成：

> 一组 Pod 的固定访问入口。

例如：

```text
Service
10.96.0.100
```

后端对应：

```text
Pod-A
Pod-B
Pod-C
```

用户始终访问：

```text
10.96.0.100
```

无需关心 Pod 如何变化。

---

## Service 在 Kubernetes 中的位置

```text
Client
   │
   ▼

Service

   │
   ▼

Endpoint

   │
   ▼

Pod-A
Pod-B
Pod-C
```

整个过程中：

* Service 提供稳定入口
* Endpoint 记录后端 Pod
* Kube-Proxy 实现转发

---

## Service 的核心组成

一个 Service 主要包含：

### ClusterIP

Service 虚拟 IP。

例如：

```text
10.96.0.100
```

---

### Selector

选择后端 Pod。

例如：

```yaml
selector:
  app: nginx
```

---

### Port

Service 暴露端口。

例如：

```yaml
port: 80
```

---

### TargetPort

Pod 实际端口。

例如：

```yaml
targetPort: 8080
```

---

## ClusterIP 类型

这是默认类型。

创建：

```yaml
apiVersion: v1
kind: Service

spec:
  type: ClusterIP
```

---

生成：

```text
10.96.0.100
```

---

访问流程：

```text
Client

↓

ClusterIP

↓

Kube-Proxy

↓

Pod
```

---

### 使用场景

适用于：

* 微服务通信
* 数据库访问
* 内部 API 调用

---

### 特点

```text
只能集群内部访问
```

---

## NodePort 类型

允许从集群外部访问。

创建：

```yaml
spec:
  type: NodePort
```

---

生成：

```text
30080
```

---

访问方式：

```text
NodeIP:30080
```

例如：

```text
192.168.1.10:30080
```

---

访问流程：

```text
Browser

↓

NodePort

↓

Service

↓

Pod
```

---

### 优点

简单直接。

---

### 缺点

端口管理混乱。

不适合大规模生产环境。

---

## LoadBalancer 类型

云平台最常见。

例如：

```yaml
spec:
  type: LoadBalancer
```

---

创建后：

```text
公网LB

↓

Service

↓

Pod
```

---

云平台自动生成：

```text
公网IP
```

例如：

```text
1.2.3.4
```

---

### 常见平台

* 阿里云 SLB
* 腾讯云 CLB
* AWS ELB
* Azure Load Balancer

---

### 优点

简单易用。

---

### 缺点

通常需要额外费用。

---

## ExternalName 类型

用于映射外部服务。

例如：

```yaml
kind: Service

spec:
  type: ExternalName
```

---

配置：

```yaml
externalName: mysql.example.com
```

---

效果：

```text
service-name

↓

mysql.example.com
```

---

### 使用场景

* 外部数据库
* 外部缓存
* SaaS 服务

---

## Endpoint 是什么？

很多人以为：

```text
Service
直接关联
Pod
```

实际上：

```text
Service

↓

Endpoint

↓

Pod
```

---

查看：

```bash
kubectl get endpoints
```

例如：

```text
10.244.1.10

10.244.2.15

10.244.3.20
```

---

这些才是真正的后端地址。

---

## EndpointSlice

Kubernetes 新版本推荐：

```text
EndpointSlice
```

替代：

```text
Endpoint
```

---

原因：

当 Pod 达到数千个时：

```text
Endpoint
```

对象会非常大。

---

EndpointSlice 将其拆分为多个对象：

```text
Slice-1

Slice-2

Slice-3
```

提升性能。

---

## Service 服务发现机制

在 Kubernetes 中：

```text
不推荐记 IP
```

而推荐：

```text
DNS 名称
```

---

例如：

```text
mysql.default.svc.cluster.local
```

---

Pod 内部：

```bash
curl http://mysql
```

即可访问。

---

CoreDNS 负责解析：

```text
mysql

↓

10.96.0.100
```

---

## Service 与 Kube-Proxy 的关系

容易混淆的概念：

### Service

负责：

```text
定义规则
```

---

### Kube-Proxy

负责：

```text
执行规则
```

---

可以理解为：

```text
Service
=
交通规则

Kube-Proxy
=
交警
```

---

## Headless Service

特殊 Service：

```yaml
clusterIP: None
```

---

特点：

```text
没有 ClusterIP
```

---

DNS 返回：

```text
Pod-A IP

Pod-B IP

Pod-C IP
```

---

常见场景：

* StatefulSet
* MySQL 集群
* Redis 集群
* Kafka 集群

---

## 生产环境最佳实践

### 内部服务

优先使用：

```text
ClusterIP
```

---

### 云平台对外服务

优先使用：

```text
LoadBalancer
```

---

### K8S 生产入口

推荐：

```text
Ingress
```

统一暴露服务。

---

### StatefulSet

推荐：

```text
Headless Service
```

---

## 常见故障排查

### Service 无法访问

查看：

```bash
kubectl get svc
```

---

### Endpoint 为空

查看：

```bash
kubectl get endpoints
```

出现：

```text
<none>
```

通常是 Selector 配置错误。

---

### Pod 标签不匹配

Service：

```yaml
selector:
  app: nginx
```

Pod：

```yaml
labels:
  app: web
```

导致无法关联。

---

### DNS 解析失败

查看：

```bash
kubectl get pod -n kube-system
```

确认：

```text
CoreDNS
```

是否正常。

---

## 运维排查命令

查看 Service：

```bash
kubectl get svc -A
```

查看 Endpoint：

```bash
kubectl get endpoints -A
```

查看 EndpointSlice：

```bash
kubectl get endpointslice -A
```

查看 Service 详情：

```bash
kubectl describe svc nginx
```

测试 DNS：

```bash
nslookup mysql
```

---

## 面试常见问题

### 为什么需要 Service？

解决 Pod IP 不稳定问题。

---

### Service 会转发流量吗？

不会。

由 Kube-Proxy 完成。

---

### ClusterIP 和 NodePort 的区别？

ClusterIP 仅内部访问。

NodePort 支持外部访问。

---

### Headless Service 有什么作用？

直接返回 Pod IP。

常用于 StatefulSet。

---

### Endpoint 和 EndpointSlice 有什么区别？

EndpointSlice 更适合大规模集群。

---

## FAQ

### Pod 可以不通过 Service 通信吗？

可以。

直接使用 Pod IP。

但不推荐。

---

### Service IP 会变化吗？

通常不会。

---

### Service 删除后会怎样？

ClusterIP 消失。

业务访问中断。

---

## 总结

Service 是 Kubernetes 服务发现体系的核心资源。

它负责：

* 提供稳定访问入口
* 屏蔽 Pod IP 变化
* 实现负载均衡
* 提供服务发现能力

可以记住一句话：

> Pod 负责运行应用，Service 负责让应用能够被稳定访问。

---

## 相关阅读

* [Kubernetes Kube-Proxy 工作原理]()
* [Kubernetes CNI 工作原理]()
* [Kubernetes Ingress 工作原理]()
* [Kubernetes CoreDNS 工作原理]()
* [Kubernetes StatefulSet 详解]()
