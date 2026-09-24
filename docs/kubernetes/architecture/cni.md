---

title: Kubernetes CNI 工作原理详解：Pod 网络通信是如何实现的？
description: 深入理解 Kubernetes CNI 工作原理，包括 Pod 网络模型、Overlay 网络、Underlay 网络、Calico、Flannel、VXLAN、BGP 以及生产环境常见网络故障排查。
keywords:

  - Kubernetes CNI
  - Kubernetes网络
  - Pod网络
  - Calico
  - Flannel
  - VXLAN
  - Kubernetes架构原理
tags:
  - Kubernetes
  - CNI
  - Kubernetes网络
author: HairLabs

---

# Kubernetes CNI 工作原理详解：Pod 网络通信是如何实现的？

## 文章摘要

在 Kubernetes 中，每个 Pod 都拥有独立 IP 地址，并且能够直接与集群中的其他 Pod 通信。

这种看似简单的网络能力，实际上是由 CNI（Container Network Interface）实现的。

本文将详细讲解 Kubernetes 网络模型、CNI 工作机制、Calico 与 Flannel 的实现原理，以及生产环境中常见的网络故障排查方法。

---

## 学习目标

阅读完本文后，你将掌握：

* 什么是 CNI
* Kubernetes 网络模型
* Pod IP 如何分配
* Pod 通信过程
* Overlay 与 Underlay 网络区别
* Calico 工作原理
* Flannel 工作原理
* VXLAN 与 BGP
* 网络故障排查思路

---

## 适用人群

本文适合：

* Kubernetes 初学者
* Linux 运维工程师
* DevOps 工程师
* 云计算学习者
* Kubernetes 面试准备人员

---

## 什么是 CNI？

CNI 全称：

```text
Container Network Interface
```

中文通常翻译为：

```text
容器网络接口
```

它并不是一个具体产品。

而是一套规范。

类似于：

```text
USB
```

是一种接口标准。

而：

```text
U盘
键盘
鼠标
```

都是具体实现。

---

在 Kubernetes 中：

```text
CNI
↓
Calico
Flannel
Cilium
Weave
```

都是基于这套标准实现的网络插件。

---

## Kubernetes 为什么需要 CNI？

先思考一个问题：

假设有两个 Pod：

```text
Pod-A
10.244.1.10

Pod-B
10.244.2.15
```

它们位于不同节点：

```text
Node01
Node02
```

那么：

```text
Pod-A 如何找到 Pod-B？
```

Linux 并不会天然知道这些网络。

因此 Kubernetes 需要额外网络方案。

这就是 CNI 存在的意义。

---

## Kubernetes 网络模型

Kubernetes 官方定义了一个非常重要的原则：

### Pod 与 Pod 之间可以直接通信

```text
Pod-A
      ↔
Pod-B
```

无需 NAT。

---

### Node 与 Pod 可以直接通信

```text
Node
  ↔
 Pod
```

无需额外代理。

---

### Pod IP 全局唯一

整个集群：

```text
10.244.1.10

10.244.2.15

10.244.3.20
```

不能重复。

---

这三条原则构成了 Kubernetes 网络模型基础。

---

## Pod 创建时发生了什么？

假设创建：

```yaml
kind: Pod
```

Scheduler 已经完成调度。

---

### Kubelet 接收任务

Kubelet 调用：

```text
CRI
```

创建容器。

---

### 调用 CNI

同时调用：

```text
CNI Plugin
```

例如：

```text
Calico
```

---

### 创建网络设备

Linux 创建：

```text
veth pair
```

类似网线。

---

结构：

```text
Pod
 │
veth
 │
Node
```

---

### 分配 IP

例如：

```text
10.244.1.10
```

分配给 Pod。

---

### 添加路由

更新：

```text
Route Table
```

使其他节点能够访问该 Pod。

---

最终：

```text
Pod Running
```

并具备网络能力。

---

## 什么是 veth Pair？

这是 Linux 网络虚拟化核心技术。

可以理解成：

```text
一根虚拟网线
```

两端分别连接：

```text
Pod
↔
Node
```

---

结构如下：

```text
Pod Namespace

eth0
 │
vethA
 │
vethB
 │
Node Namespace
```

---

所有 Kubernetes 网络插件最终都离不开 veth Pair。

---

## Overlay 网络是什么？

这是目前最常见方案。

例如：

```text
Flannel VXLAN
```

---

网络结构：

```text
Node01
 Pod-A

     ↓

VXLAN Tunnel

     ↓

Node02
 Pod-B
```

---

数据包：

```text
原始数据包

↓

封装

↓

跨节点传输

↓

解封装
```

---

优点：

* 部署简单
* 对网络要求低
* 云环境兼容性好

---

缺点：

* 存在封装开销
* 性能略低

---

## Underlay 网络是什么？

直接利用物理网络。

例如：

```text
Calico BGP
```

---

结构：

```text
Pod-A

↓

交换机

↓

Pod-B
```

---

无需 VXLAN。

无需隧道。

---

优点：

* 性能高
* 延迟低

---

缺点：

* 网络规划复杂
* 对交换机环境要求较高

---

## Calico 工作原理

目前生产环境使用最多。

---

### IP 分配

Calico 为每个 Pod 分配：

```text
独立 IP
```

---

### 路由同步

节点之间通过：

```text
BGP
```

交换路由信息。

---

例如：

```text
Node01
10.244.1.0/24

Node02
10.244.2.0/24
```

双方互相学习路由。

---

### 通信过程

```text
Pod-A

↓

Node01

↓

BGP Route

↓

Node02

↓

Pod-B
```

---

无需 NAT。

无需代理。

---

## Flannel 工作原理

历史上非常流行。

适合入门学习。

---

### VXLAN 模式

节点之间建立：

```text
VXLAN Tunnel
```

---

通信过程：

```text
Pod-A

↓

Node01

↓

VXLAN

↓

Node02

↓

Pod-B
```

---

相比 Calico：

部署更简单。

但性能略低。

---

## Calico 与 Flannel 对比

| 项目    | Calico | Flannel |
| ----- | ------ | ------- |
| 性能    | 高      | 中       |
| 网络策略  | 支持     | 不支持     |
| BGP   | 支持     | 不支持     |
| VXLAN | 支持     | 支持      |
| 生产环境  | 推荐     | 小规模适用   |

---

## Network Policy 是什么？

很多人认为：

```text
Pod 默认隔离
```

实际上：

```text
Pod 默认全互通
```

---

例如：

```text
Pod-A
↓
Pod-B
```

默认允许访问。

---

通过：

```yaml
kind: NetworkPolicy
```

实现：

```text
允许谁访问

拒绝谁访问
```

---

该能力通常由：

```text
Calico
Cilium
```

实现。

---

## CNI 与 Kube-Proxy 的区别

很多新人容易混淆。

| 组件         | 作用         |
| ---------- | ---------- |
| CNI        | Pod 网络     |
| Kube-Proxy | Service 转发 |

---

例如：

```text
Pod-A
↓
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
Client
↓
Service
↓
Pod
```

属于：

```text
Kube-Proxy
```

负责。

---

## 生产环境常见故障

### Pod 无法跨节点通信

检查：

```bash
ip route
```

---

### CoreDNS 无法解析

查看：

```bash
kubectl get pod -n kube-system
```

---

### Calico 异常

查看：

```bash
kubectl get pod -n kube-system | grep calico
```

---

### Flannel 异常

查看：

```bash
kubectl get pod -n kube-system | grep flannel
```

---

### Network Policy 阻断流量

查看：

```bash
kubectl get networkpolicy -A
```

---

## 运维排查命令

查看节点路由：

```bash
ip route
```

查看网络接口：

```bash
ip link
```

查看 Pod IP：

```bash
kubectl get pod -o wide
```

查看 Calico：

```bash
calicoctl node status
```

查看网络策略：

```bash
kubectl get networkpolicy -A
```

---

## 面试常见问题

### CNI 的作用是什么？

负责 Kubernetes Pod 网络通信。

---

### CNI 是 Kubernetes 自带的吗？

不是。

需要安装网络插件。

---

### Kubernetes 默认支持哪些 CNI？

官方只定义标准。

具体实现由第三方插件完成。

---

### Calico 和 Flannel 有什么区别？

Calico 功能更强，生产环境更常见。

Flannel 更简单。

---

### CNI 与 Kube-Proxy 的区别？

CNI 负责 Pod 网络。

Kube-Proxy 负责 Service 转发。

---

## FAQ

### Kubernetes 不安装 CNI 可以运行吗？

节点可以加入集群。

但 Pod 无法正常通信。

---

### 为什么 Pod 都有独立 IP？

这是 Kubernetes 网络模型要求。

---

### 生产环境推荐什么 CNI？

目前最常见：

* Calico
* Cilium

---

## 总结

CNI 是 Kubernetes 网络体系的基础。

它负责：

* Pod IP 分配
* Pod 网络创建
* 路由维护
* 网络策略实现

可以记住一句话：

> Kubelet 创建 Pod，CNI 赋予 Pod 网络能力，Kube-Proxy 负责 Service 流量转发。

---

## 相关阅读

* [Kubernetes Kubelet 工作原理]()
* [Kubernetes Kube-Proxy 工作原理]()
* [Kubernetes Service 详解]()
* [Kubernetes NetworkPolicy 详解]()
* [Kubernetes Ingress 工作原理]()
