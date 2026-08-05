---
title: Kubernetes CSI 工作原理详解：Kubernetes 是如何对接存储系统的？
description: 深入理解 Kubernetes CSI（Container Storage Interface）工作原理，包括 CSI 架构、Volume 生命周期、NFS、Ceph、Longhorn、云盘存储以及生产环境最佳实践。
keywords:
  - Kubernetes CSI
  - Container Storage Interface
  - Kubernetes存储
  - CSI Driver
  - PV PVC
  - StorageClass
tags:
  - Kubernetes
  - CSI
  - Storage
author: HairLabs | 一根头发丝的宽度
---

# Kubernetes CSI 工作原理详解：Kubernetes 是如何对接存储系统的？

## 文章摘要

在 Kubernetes 中，Pod 是临时资源。

当 Pod 被删除或重新创建时，容器内部的数据通常也会随之丢失。

因此 Kubernetes 需要一种统一的方式来对接各种存储系统。

这就是 CSI（Container Storage Interface）存在的意义。

本文将详细讲解 CSI 的设计目标、工作原理、Volume 生命周期以及 Kubernetes 如何通过 CSI 对接 NFS、Ceph、Longhorn、云盘等存储系统。

---

## 学习目标

阅读完本文后，你将掌握：

- 什么是 CSI
- 为什么 Kubernetes 需要 CSI
- CSI 的工作原理
- CSI Driver 是什么
- Volume 生命周期
- 动态存储供应机制
- Kubernetes 如何对接存储系统
- 常见 CSI 插件介绍

---

## 适用人群

本文适合：

- Kubernetes 初学者
- Linux 运维工程师
- DevOps 工程师
- 云原生学习者
- Kubernetes 面试准备人员

---

## 为什么需要 CSI？

先思考一个问题。

创建一个 Pod：

```yaml
apiVersion: v1
kind: Pod
```

运行后：

```text
nginx Pod
```

内部写入数据：

```text
/data/test.txt
```

---

如果 Pod 被删除：

```bash
kubectl delete pod nginx
```

然后重新创建。

---

会发现：

```text
test.txt
消失了
```

---

原因很简单：

```text
容器文件系统
≠
持久化存储
```

---

因此 Kubernetes 需要：

```text
持久化存储
```

能力。

---

## Kubernetes 为什么不直接管理存储？

因为存储系统种类太多。

例如：

```text
NFS

Ceph

GlusterFS

Longhorn

AWS EBS

阿里云ESSD

腾讯云CBS
```

---

如果 Kubernetes 为每种存储都单独开发代码：

```text
维护成本极高
```

---

因此 Kubernetes 采用：

```text
统一接口
```

方案。

这就是 CSI。

---

## 什么是 CSI？

CSI 全称：

```text
Container Storage Interface
```

中文：

```text
容器存储接口
```

---

它本质上是一套标准规范。

类似：

```text
USB接口
```

---

USB 定义：

```text
如何连接设备
```

---

而：

```text
键盘
鼠标
U盘
```

是具体实现。

---

同样：

```text
CSI
```

定义：

```text
如何创建存储

如何挂载存储

如何删除存储
```

---

而：

```text
NFS CSI

Ceph CSI

Longhorn CSI
```

则是具体实现。

---

## CSI 在 Kubernetes 中的位置

架构如下：

```text
Pod

↓

Kubelet

↓

CSI Driver

↓

Storage System
```

---

例如：

```text
Pod

↓

Kubelet

↓

Ceph CSI

↓

Ceph Cluster
```

---

或者：

```text
Pod

↓

Kubelet

↓

NFS CSI

↓

NFS Server
```

---

## CSI Driver 是什么？

很多新人容易混淆。

---

CSI：

```text
标准接口
```

---

CSI Driver：

```text
具体实现
```

---

例如：

```text
CSI
```

类似：

```text
打印机接口
```

---

而：

```text
HP打印机

Canon打印机
```

则是：

```text
CSI Driver
```

---

真正工作的组件。

---

## Kubernetes 存储创建流程

假设创建：

```yaml
kind: PersistentVolumeClaim
```

---

流程：

```text
PVC

↓

StorageClass

↓

CSI Driver

↓

Storage System

↓

创建Volume
```

---

最终：

```text
Volume Ready
```

---

整个过程自动完成。

---

## 什么是 Volume？

简单理解：

```text
Volume
=
磁盘
```

---

例如：

```text
10GB

20GB

100GB
```

---

Volume 创建后：

```text
挂载到 Pod
```

使用。

---

## Volume 生命周期

CSI 主要管理：

### Create Volume

创建磁盘。

---

### Attach Volume

挂载到节点。

---

### Mount Volume

挂载到容器。

---

### Unmount Volume

卸载。

---

### Delete Volume

删除磁盘。

---

流程如下：

```text
Create

↓

Attach

↓

Mount

↓

Use

↓

Unmount

↓

Delete
```

---

## CSI 与 Kubelet 的关系

这里非常重要。

---

真正负责挂载存储的是：

```text
Kubelet
```

---

CSI Driver 负责：

```text
调用存储系统
```

---

例如：

```text
创建云盘
```

---

CSI Driver：

```text
向云平台申请磁盘
```

---

Kubelet：

```text
将磁盘挂载到Pod
```

---

## 动态存储供应

这是 CSI 最大优势之一。

---

传统模式：

```text
管理员先创建磁盘
```

---

然后：

```text
用户申请使用
```

---

过程繁琐。

---

CSI 支持：

```text
动态创建
```

---

用户提交：

```yaml
kind: PVC
```

---

系统自动：

```text
创建Volume
```

---

无需人工干预。

---

## StorageClass 的作用

StorageClass 可以理解为：

```text
存储模板
```

---

例如：

```text
SSD

SATA

NVMe
```

---

用户只需要：

```yaml
storageClassName: fast
```

---

系统自动创建对应存储。

---

## 常见 CSI 插件

### NFS CSI

最简单。

适合实验环境。

---

架构：

```text
Pod

↓

NFS CSI

↓

NFS Server
```

---

### Ceph CSI

生产环境常见。

支持：

```text
块存储

文件存储

对象存储
```

---

### Longhorn CSI

轻量级云原生存储。

---

适合：

```text
中小规模集群
```

---

### AWS EBS CSI

AWS 官方插件。

---

### 阿里云 Disk CSI

阿里云官方实现。

---

### 腾讯云 CBS CSI

腾讯云官方实现。

---

## CSI 与 CRI 的区别

面试经常考。

| 项目 | CRI | CSI |
|--------|--------|--------|
| 作用 | 容器接口 | 存储接口 |
| 对接对象 | Container Runtime | Storage System |
| 使用场景 | 创建容器 | 创建存储 |
| 代表实现 | Containerd | Ceph CSI |

---

简单记忆：

```text
CRI 管容器

CSI 管存储
```

---

## 生产环境最佳实践

### 优先使用 CSI

不要使用已废弃的 In-Tree 插件。

---

### 使用 StorageClass

避免手工创建 PV。

---

### 监控存储容量

关注：

```text
Volume使用率
```

---

### 定期测试恢复

验证：

```text
快照

备份

恢复
```

流程。

---

## 常见故障排查

### PVC 一直 Pending

查看：

```bash
kubectl describe pvc
```

---

通常原因：

```text
StorageClass不存在
```

---

### Volume 挂载失败

查看：

```bash
kubectl describe pod
```

---

### CSI Driver 异常

查看：

```bash
kubectl get pod -A
```

确认 CSI 组件状态。

---

### 存储容量不足

查看：

```bash
kubectl get pv
```

---

## 运维排查命令

查看 PVC：

```bash
kubectl get pvc
```

---

查看 PV：

```bash
kubectl get pv
```

---

查看 StorageClass：

```bash
kubectl get sc
```

---

查看 CSI Driver：

```bash
kubectl get csidriver
```

---

查看挂载情况：

```bash
kubectl describe pod nginx
```

---

## 面试常见问题

### CSI 的作用是什么？

统一 Kubernetes 与存储系统之间的接口。

---

### CSI Driver 是什么？

具体存储插件实现。

---

### CSI 与 StorageClass 的关系？

StorageClass 通过 CSI 创建存储。

---

### CSI 与 CRI 的区别？

CRI 管容器。

CSI 管存储。

---

### Kubernetes 自带存储吗？

不提供。

通过 CSI 对接外部存储。

---

## FAQ

### 不安装 CSI 可以使用 Kubernetes 吗？

可以。

但无法使用动态存储。

---

### CSI 一定需要 PV 和 PVC 吗？

绝大多数场景需要。

---

### CSI 支持本地磁盘吗？

支持。

例如：

```text
Local PV
```

方案。

---

## 总结

CSI 是 Kubernetes 存储体系的核心接口标准。

它负责：

- 创建存储
- 删除存储
- 挂载存储
- 动态供应存储

可以记住一句话：

> CRI 负责让 Kubernetes 管理容器，而 CSI 负责让 Kubernetes 管理存储。

---

## 相关阅读

- [Kubernetes CRI 工作原理](node/cri.md)
- [Kubernetes PV 与 PVC 详解]()
- [Kubernetes StorageClass 详解]()
- [Kubernetes StatefulSet 工作原理]()
- [Ceph CSI 实战部署]()