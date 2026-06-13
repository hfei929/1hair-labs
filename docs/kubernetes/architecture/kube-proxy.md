---

title: Kubernetes Kube-Proxy 工作原理详解：Service 流量转发的核心组件
description: 深入理解 Kubernetes Kube-Proxy 工作原理，包括 Service、Endpoint、iptables、IPVS、流量转发机制以及生产环境常见故障排查。
keywords:

  - Kubernetes Kube Proxy
  - Kube Proxy
  - Kubernetes Service
  - Kubernetes网络
  - Kubernetes流量转发
  - Kubernetes架构原理
tags:
  - Kubernetes
  - Kube Proxy
  - Kubernetes网络
author: HairLabs

---

# Kubernetes Kube-Proxy 工作原理详解：Service 流量转发的核心组件

## 文章摘要

在 Kubernetes 中，每个 Pod 都拥有独立 IP 地址，但 Pod 可能随时重建、迁移甚至销毁。

为了让业务能够稳定访问后端 Pod，Kubernetes 引入了 Service 资源。

而真正负责实现 Service 流量转发的核心组件，就是 Kube-Proxy。

本文将详细讲解 Kube-Proxy 的工作原理、iptables 与 IPVS 模式、Service 转发机制以及生产环境中的常见问题。

---

## 学习目标

阅读完本文后，你将掌握：

* Kube-Proxy 的作用
* Service 为什么存在
* ClusterIP 如何工作
* Endpoint 与 EndpointSlice 的关系
* iptables 模式原理
* IPVS 模式原理
* 流量转发全过程
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

## 什么是 Kube-Proxy？

很多新手都会认为：

```text
Service = 负载均衡
```

实际上：

```text
Service
只是规则

Kube-Proxy
才是真正执行规则的人
```

如果把 Kubernetes 集群看作一个酒店：

| 角色     | Kubernetes |
| ------ | ---------- |
| 酒店总机号码 | Service    |
| 前台接线员  | Kube-Proxy |
| 房间     | Pod        |

客户拨打：

```text
8888
```

总机号码不会变。

但具体接到哪个房间：

```text
101
102
103
```

由前台负责转接。

Kube-Proxy 的职责也是如此。

---

## 为什么需要 Service？

假设有三个 Nginx Pod：

```text
Pod-A
10.244.1.10

Pod-B
10.244.2.15

Pod-C
10.244.3.20
```

问题来了：

如果 Pod-B 被删除：

```text
10.244.2.15
```

就不存在了。

业务访问将失败。

---

### Pod IP 不稳定

Kubernetes 中：

```text
Pod 可随时重建

Pod IP 可随时变化
```

因此：

```text
不能直接依赖 Pod IP
```

---

### Service 提供稳定入口

例如：

```yaml
kind: Service
```

创建后：

```text
10.96.0.100
```

这个地址基本不会变化。

用户访问：

```text
10.96.0.100
```

即可访问后端 Pod。

---

## Kube-Proxy 在 Kubernetes 中的位置

```text
             Client
                │
                ▼

        Service ClusterIP

                │
                ▼

           Kube-Proxy

                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼

     Pod1      Pod2      Pod3
```

---

## Kube-Proxy 的核心职责

主要负责：

* 监听 Service 变化
* 监听 Endpoint 变化
* 维护转发规则
* 实现负载均衡
* 转发 Service 流量

简单来说：

> Kube-Proxy 负责把访问 Service 的流量转发到正确的 Pod。

---

## Kube-Proxy 如何工作？

### 第一步：监听 API Server

Kube-Proxy 持续 Watch：

```text
Service

Endpoint

EndpointSlice
```

资源。

---

### 第二步：发现 Service

例如：

```yaml
kind: Service

spec:
  clusterIP: 10.96.0.100
```

---

### 第三步：发现 Pod

对应 Endpoint：

```text
10.244.1.10

10.244.2.15

10.244.3.20
```

---

### 第四步：生成转发规则

Kube-Proxy 自动生成：

```text
iptables
```

或者：

```text
IPVS
```

规则。

---

### 第五步：流量转发

用户访问：

```text
10.96.0.100
```

流量自动转发到：

```text
Pod-A
```

或者：

```text
Pod-B
```

或者：

```text
Pod-C
```

---

## Endpoint 是什么？

很多人容易忽略 Endpoint。

实际上：

```text
Service
并不知道 Pod
```

它只知道：

```text
Endpoint
```

---

例如：

Service：

```yaml
selector:
  app: nginx
```

系统自动生成：

```text
Endpoint
```

内容：

```text
10.244.1.10

10.244.2.15

10.244.3.20
```

Kube-Proxy 根据这些信息完成转发。

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

原因：

当 Pod 数量达到数千个时：

```text
Endpoint
```

对象过于庞大。

---

EndpointSlice 会拆分：

```text
Slice1

Slice2

Slice3
```

提升性能。

---

## iptables 模式

这是最经典的模式。

查看：

```bash
kubectl -n kube-system get cm kube-proxy -o yaml
```

---

配置：

```yaml
mode: iptables
```

---

工作流程：

```text
Client
   │
   ▼

ClusterIP

   │
iptables规则

   ▼

Pod
```

---

### 优点

* 简单稳定
* 部署方便
* 社区成熟

---

### 缺点

当 Service 数量很多时：

```text
iptables规则急剧增长
```

性能下降。

---

## IPVS 模式

生产环境更推荐。

配置：

```yaml
mode: ipvs
```

---

工作流程：

```text
Client
   │
   ▼

Virtual Service

   │

IPVS

   ▼

Real Server
```

---

### 优点

* 转发效率更高
* 支持更多调度算法
* 大规模集群性能更好

---

### 支持的算法

例如：

```text
Round Robin
```

轮询。

---

```text
Least Connection
```

最少连接。

---

```text
Source Hash
```

源地址哈希。

---

## 流量转发全过程

假设：

```text
Service
10.96.0.100
```

对应：

```text
Pod1

Pod2

Pod3
```

---

访问：

```bash
curl 10.96.0.100
```

过程：

```text
Client

↓

Service

↓

iptables/IPVS

↓

Pod

↓

返回结果
```

整个过程中：

```text
Service 本身不会转发流量
```

真正工作的是：

```text
Kube-Proxy
```

---

## Kube-Proxy 与 CNI 的区别

很多新人容易混淆。

| 组件         | 职责         |
| ---------- | ---------- |
| Kube-Proxy | Service 转发 |
| CNI        | Pod 网络通信   |

---

例如：

```text
Pod-A
访问
Pod-B
```

属于：

```text
CNI
```

负责。

---

例如：

```text
访问 Service
```

属于：

```text
Kube-Proxy
```

负责。

---

## 生产环境常见故障

### Service 无法访问

检查：

```bash
kubectl get svc
```

---

### Endpoint 为空

查看：

```bash
kubectl get endpoints
```

可能发现：

```text
<none>
```

说明没有匹配到 Pod。

---

### Selector 配置错误

例如：

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

### Kube-Proxy 异常

查看：

```bash
kubectl get pod -n kube-system
```

---

### iptables 规则缺失

查看：

```bash
iptables -t nat -L
```

---

### IPVS 规则异常

查看：

```bash
ipvsadm -Ln
```

---

## 运维排查命令

查看 Kube-Proxy：

```bash
kubectl get pod -n kube-system | grep kube-proxy
```

查看日志：

```bash
kubectl logs -n kube-system kube-proxy-xxxxx
```

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

---

## 面试常见问题

### Kube-Proxy 的作用是什么？

负责 Service 流量转发。

---

### Service 自己会转发流量吗？

不会。

由 Kube-Proxy 实现。

---

### Kube-Proxy 常见模式有哪些？

* iptables
* IPVS

---

### 为什么推荐 IPVS？

性能更好，适合大规模集群。

---

### Kube-Proxy 会直接转发网络包吗？

不会。

它通过维护 Linux 内核规则实现流量转发。

---

## FAQ

### 每个节点都需要 Kube-Proxy 吗？

通常需要。

因为每个节点都可能访问 Service。

---

### 删除 Kube-Proxy 会怎样？

已有规则短时间可能继续工作。

但后续 Service 更新将失效。

---

### Kube-Proxy 会直接访问 ETCD 吗？

不会。

通过 API Server 获取资源信息。

---

## 总结

Kube-Proxy 是 Kubernetes Service 网络模型的核心组件。

它负责：

* 监听 Service
* 监听 Endpoint
* 维护转发规则
* 实现负载均衡

可以记住一句话：

> Service 提供稳定入口，Kube-Proxy 负责真正把流量转发到后端 Pod。

---

## 相关阅读

* [Kubernetes Kubelet 工作原理](kubelet.md)
* [Kubernetes Service 详解](services.md)
* [Kubernetes CNI 工作原理](cni.md)
* [Kubernetes Ingress 工作原理]()
* [Kubernetes 网络模型详解]()
