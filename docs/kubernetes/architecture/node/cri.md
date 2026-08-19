---
title: Kubernetes CRI 工作原理详解：Kubelet 是如何创建容器的？
description: 深入理解 Kubernetes CRI（Container Runtime Interface）工作原理，包括 Docker、Containerd、CRI-O、OCI、runc 以及 Kubernetes 容器运行机制。
keywords:
  - Kubernetes CRI
  - Container Runtime Interface
  - Containerd
  - CRI-O
  - Docker
  - Kubernetes架构原理
tags:
  - Kubernetes
  - CRI
  - Container Runtime
author: HairLabs ｜ 一根头发丝的宽度
---

# Kubernetes CRI 工作原理详解：Kubelet 是如何创建容器的？

## 文章摘要

很多 Kubernetes 初学者都会认为：

> Kubernetes 负责创建容器。

实际上并不是。

真正创建容器的是容器运行时（Container Runtime）。

而 Kubernetes 与容器运行时之间的桥梁，就是 CRI（Container Runtime Interface）。

本文将深入讲解 CRI 的设计目的、工作原理，以及 Docker、Containerd、CRI-O、OCI、runc 之间的关系。

---

## 学习目标

阅读完本文后，你将掌握：

- 什么是 CRI
- Kubernetes 如何创建容器
- Kubelet 与 CRI 的关系
- Docker 与 Kubernetes 的关系
- Containerd 工作原理
- CRI-O 工作原理
- OCI 标准
- Kubernetes 1.24 为什么移除 Docker

---

## 适用人群

本文适合：

- Kubernetes 初学者
- Linux 运维工程师
- DevOps 工程师
- 云原生学习者
- Kubernetes 面试准备人员

---

## 为什么需要 CRI？

先思考一个问题：

当我们创建 Pod：

```bash
kubectl apply -f nginx.yaml
```

最终：

```text
nginx Pod Running
```

已经运行起来。

那么：

```text
到底是谁创建了容器？
```

很多新人会回答：

```text
Kubernetes
```

其实并不准确。

---

真正的过程是：

```text
Kubelet

↓

CRI

↓

Container Runtime

↓

Container
```

---

因此：

> Kubernetes 并不直接创建容器。

而是通过 CRI 调用容器运行时来完成。

---

## 什么是 CRI？

CRI 全称：

```text
Container Runtime Interface
```

中文通常翻译为：

```text
容器运行时接口
```

---

CRI 本质上是一套标准接口。

类似于：

```text
USB 接口
```

---

USB 定义：

```text
如何连接设备
```

而：

```text
键盘
鼠标
U盘
```

则是具体实现。

---

同样：

```text
CRI
```

定义：

```text
如何创建容器
如何删除容器
如何查询容器状态
```

---

而：

```text
Containerd

CRI-O
```

则是具体实现。

---

## Kubernetes 创建容器全过程

创建 Deployment：

```bash
kubectl apply -f nginx.yaml
```

---

流程：

```text
Deployment

↓

Controller Manager

↓

Pod

↓

Scheduler

↓

Node

↓

Kubelet

↓

CRI

↓

Container Runtime

↓

Container
```

---

这里最关键的一步：

```text
Kubelet

↓

CRI

↓

Container Runtime
```

---

因为：

```text
Kubelet不会创建容器
```

---

它只负责：

```text
下达命令
```

---

## Kubelet 与 CRI 的关系

可以理解为：

```text
Kubelet
=
项目经理
```

---

CRI：

```text
翻译官
```

---

Container Runtime：

```text
施工队
```

---

例如：

```text
创建Nginx容器
```

---

Kubelet：

```text
我要一个Nginx
```

---

CRI：

```text
翻译成标准接口调用
```

---

Container Runtime：

```text
真正执行创建
```

---

## 什么是 Container Runtime？

容器运行时负责：

- 拉取镜像
- 创建容器
- 启动容器
- 停止容器
- 删除容器

例如：

```text
nginx:latest
```

镜像下载。

---

创建：

```text
Namespace

Cgroup

网络

存储
```

最终启动进程。

---

## Docker 与 Kubernetes 的关系

这是最容易被误解的问题。

很多新人认为：

```text
Kubernetes = Docker
```

实际上：

```text
Kubernetes ≠ Docker
```

---

关系如下：

```text
Kubernetes
负责管理

Docker
负责运行
```

---

类似于：

```text
主管
↓

员工
```

关系。

---

## Docker 架构

传统架构：

```text
Kubelet

↓

Docker Engine

↓

Containerd

↓

runc

↓

Container
```

---

可以发现：

Docker 本身并不直接创建容器。

---

实际上：

```text
Containerd
```

才是真正工作的组件。

---

## 为什么 Kubernetes 移除 Docker？

Kubernetes 1.24 开始：

```text
Dockershim
移除
```

---

很多人误以为：

```text
Kubernetes 不支持 Docker
```

其实并不是。

---

真正原因：

```text
Docker 架构多了一层
```

---

路径：

```text
Kubelet

↓

Docker

↓

Containerd

↓

runc
```

---

而直接使用：

```text
Containerd
```

则变成：

```text
Kubelet

↓

Containerd

↓

runc
```

---

更简单。

性能更好。

维护成本更低。

---

## 什么是 Containerd？

目前 Kubernetes 默认推荐。

---

架构：

```text
Kubelet

↓

CRI

↓

Containerd

↓

runc

↓

Container
```

---

主要职责：

- 镜像管理
- 容器管理
- Snapshot 管理
- Runtime 调用

---

目前绝大多数生产环境使用：

```text
Containerd
```

---

## 什么是 CRI-O？

另一种运行时。

专门为 Kubernetes 设计。

---

架构：

```text
Kubelet

↓

CRI-O

↓

OCI Runtime

↓

Container
```

---

特点：

```text
轻量

专注Kubernetes
```

---

Red Hat OpenShift 广泛使用。

---

## 什么是 OCI？

OCI 全称：

```text
Open Container Initiative
```

中文：

```text
开放容器标准
```

---

主要定义：

### 镜像标准

例如：

```text
nginx
redis
mysql
```

镜像格式。

---

### Runtime 标准

定义：

```text
如何运行容器
```

---

OCI 的作用：

```text
保证兼容性
```

---

## 什么是 runc？

很多人没听过。

但几乎所有容器都会经过它。

---

架构：

```text
Containerd

↓

runc

↓

Linux Namespace

↓

Linux Cgroup
```

---

runc 负责：

```text
最终创建Linux进程
```

---

因此：

> 容器本质上还是 Linux 进程。

---

## CRI 工作流程

创建 Pod：

```text
Kubelet

↓

CreatePod

↓

CRI

↓

Containerd

↓

Pull Image

↓

Create Container

↓

Start Container

↓

Running
```

---

整个过程中：

```text
CRI
```

负责统一接口。

---

## CRI 与 OCI 的区别

很多面试题喜欢考。

| 项目 | CRI | OCI |
|--------|--------|--------|
| 作用 | Kubernetes接口 | 容器标准 |
| 面向对象 | Kubelet | Runtime |
| 定义内容 | API接口 | 镜像与运行时 |
| 使用场景 | Kubernetes | 所有容器平台 |

---

简单记忆：

```text
CRI
连接Kubernetes

OCI
规范容器
```

---

## 生产环境最佳实践

### 优先使用 Containerd

当前主流选择。

---

### 不再新部署 Docker Runtime

新集群没有必要。

---

### 定期检查 Runtime 状态

查看：

```bash
systemctl status containerd
```

---

### 保持版本兼容

升级 Kubernetes 前确认：

```text
Containerd版本
```

兼容。

---

## 常见故障排查

### Pod 一直 ContainerCreating

查看：

```bash
kubectl describe pod nginx
```

---

### Runtime 异常

查看：

```bash
systemctl status containerd
```

---

### 镜像拉取失败

查看：

```bash
crictl pull nginx
```

---

### Kubelet 无法连接 Runtime

查看：

```bash
journalctl -u kubelet -f
```

---

## 运维排查命令

查看 Runtime：

```bash
crictl info
```

---

查看容器：

```bash
crictl ps
```

---

查看镜像：

```bash
crictl images
```

---

查看 Pod：

```bash
crictl pods
```

---

查看 Containerd：

```bash
ctr containers list
```

---

## 面试常见问题

### CRI 的作用是什么？

Kubelet 与容器运行时之间的标准接口。

---

### Kubernetes 会直接创建容器吗？

不会。

由容器运行时创建。

---

### Kubernetes 为什么移除 Docker？

因为直接使用 Containerd 更简单。

---

### 当前主流 Runtime 是什么？

Containerd。

---

### runc 的作用是什么？

最终创建 Linux 容器进程。

---

## FAQ

### Docker 还能用吗？

可以。

但不再是 Kubernetes 推荐方案。

---

### Containerd 和 Docker 谁更底层？

Containerd。

---

### 没有 CRI 能运行 Kubernetes 吗？

不能。

Kubelet 必须依赖容器运行时。

---

## 总结

CRI 是 Kubernetes 与容器运行时之间的桥梁。

它负责：

- 统一容器接口
- 解耦 Kubernetes 与 Runtime
- 支持多种容器运行时

可以记住一句话：

> Kubelet 负责管理容器，而真正创建容器的是 Container Runtime，CRI 则是两者之间的翻译官。

---

## 相关阅读

- [Kubernetes Kubelet 工作原理](kubelet.md)
- [Kubernetes ETCD 工作原理](../control-plane/etcd.md)
- [Kubernetes Pod 生命周期详解](pod-lifecycle.md)
- [Containerd 工作原理]()
- [OCI 容器标准详解]()