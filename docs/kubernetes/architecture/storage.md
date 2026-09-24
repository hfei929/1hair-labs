---
title: Kubernetes 存储资源详解：PV、PVC、StorageClass、VolumeSnapshot 一次讲透
description: 深入理解 Kubernetes 存储资源体系，包括 PV、PVC、StorageClass、VolumeSnapshot 的作用、关系以及生产环境最佳实践。
keywords:
  - Kubernetes存储
  - PV
  - PVC
  - StorageClass
  - VolumeSnapshot
  - Kubernetes存储资源
tags:
  - Kubernetes
  - Storage
  - PV
author: HairLabs | 一根头发丝的宽度
---

# Kubernetes 存储资源详解：PV、PVC、StorageClass、VolumeSnapshot 一次讲透

## 文章摘要

Pod 是 Kubernetes 中运行应用的最小单元。

但 Pod 本身是临时资源。

当 Pod 删除、迁移或者重建后，容器内部的数据通常会丢失。

因此 Kubernetes 提供了一套完整的存储资源体系，实现数据持久化。

本文将系统讲解 PV、PVC、StorageClass、VolumeSnapshot 的作用、关系以及实际应用场景。

---

## 学习目标

阅读完本文后，你将掌握：

- Kubernetes 存储体系结构
- PV 的作用
- PVC 的作用
- StorageClass 的作用
- VolumeSnapshot 的作用
- 动态存储供应机制
- 存储资源之间的关系
- 生产环境最佳实践

---

## 适用人群

本文适合：

- Kubernetes 初学者
- Linux 运维工程师
- DevOps 工程师
- 云原生学习者
- Kubernetes 面试准备人员

---

## 为什么需要存储资源？

先看一个例子：

```yaml
apiVersion: v1
kind: Pod
```

运行：

```text
MySQL Pod
```

---

数据库写入：

```text
10000 条数据
```

---

如果 Pod 被删除：

```bash
kubectl delete pod mysql
```

---

重新创建后：

```text
数据全部丢失
```

---

原因：

```text
Pod ≠ 持久化存储
```

---

因此 Kubernetes 引入：

```text
存储资源体系
```

来解决数据持久化问题。

---

## Kubernetes 存储体系

整体架构：

```text
Pod

↓

PVC

↓

PV

↓

StorageClass

↓

Storage System
```

---

例如：

```text
Pod

↓

PVC

↓

PV

↓

Ceph
```

---

或者：

```text
Pod

↓

PVC

↓

PV

↓

NFS
```

---

## 什么是 PV？

PV 全称：

```text
PersistentVolume
```

中文：

```text
持久卷
```

---

简单理解：

```text
PV
=
磁盘
```

---

例如：

```text
100GB SSD

500GB SATA

1TB 云盘
```

---

在 Kubernetes 中：

PV 表示实际存储资源。

---

查看：

```bash
kubectl get pv
```

---

典型输出：

```text
NAME      CAPACITY

pv-001    100Gi
```

---

## 什么是 PVC？

PVC 全称：

```text
PersistentVolumeClaim
```

中文：

```text
持久卷声明
```

---

简单理解：

```text
PVC
=
用盘申请单
```

---

开发人员通常不会关心：

```text
哪块磁盘
```

---

只关心：

```text
我要100GB存储
```

---

例如：

```yaml
resources:
  requests:
    storage: 100Gi
```

---

PVC 创建后：

```text
系统自动寻找合适PV
```

进行绑定。

---

## 为什么需要 PVC？

如果直接让 Pod 使用 PV：

```text
开发人员需要知道具体磁盘
```

---

维护复杂。

---

因此 Kubernetes 采用：

```text
申请模式
```

---

类似：

```text
用户申请住房

↓

系统分配房间
```

---

而不是：

```text
用户直接指定房间
```

---

## PV 与 PVC 的关系

可以理解为：

```text
PV
=
房子
```

---

```text
PVC
=
租房申请
```

---

流程：

```text
PVC

↓

匹配

↓

PV
```

---

最终：

```text
Bound
```

绑定成功。

---

查看：

```bash
kubectl get pvc
```

---

状态：

```text
Bound
```

表示已关联存储。

---

## 什么是 StorageClass？

随着集群规模扩大。

手工创建 PV 非常麻烦。

---

因此 Kubernetes 引入：

```text
StorageClass
```

---

简单理解：

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

不同性能等级。

---

用户只需要：

```yaml
storageClassName: fast
```

---

系统自动创建对应存储。

---

## 动态存储供应

这是现代 Kubernetes 最常见模式。

---

用户创建：

```yaml
kind: PVC
```

---

系统自动：

```text
StorageClass

↓

CSI Driver

↓

Storage System

↓

创建PV
```

---

整个过程无需管理员干预。

---

流程：

```text
PVC

↓

StorageClass

↓

CSI

↓

PV

↓

Pod
```

---

## 什么是 VolumeSnapshot？

生产环境非常重要。

---

作用：

```text
存储快照
```

---

类似：

```text
VM 快照
```

---

例如：

```text
MySQL 数据盘
```

---

创建快照：

```text
Snapshot-001
```

---

出现问题时：

```text
快速恢复
```

---

常用于：

- 数据备份
- 数据恢复
- 测试环境克隆

---

## 存储资源关系图

最常见链路：

```text
Pod

↓

PVC

↓

PV

↓

StorageClass

↓

CSI Driver

↓

Storage System
```

---

其中：

```text
Pod
使用存储

PVC
申请存储

PV
提供存储

StorageClass
定义存储类型

CSI
实现存储接入
```

---

## 常见存储类型

### NFS

最简单。

适合实验环境。

---

### Ceph

生产环境常见。

支持：

```text
块存储

文件存储

对象存储
```

---

### Longhorn

轻量级云原生存储。

---

### 云盘

例如：

```text
AWS EBS

阿里云 ESSD

腾讯云 CBS
```

---

## 存储资源如何选择？

| 场景 | 推荐 |
|--------|--------|
| 实验环境 | NFS |
| 小型集群 | Longhorn |
| 中大型集群 | Ceph |
| 公有云 | 云厂商 CSI |

---

## 生产环境最佳实践

### 优先使用 StorageClass

避免手工创建大量 PV。

---

### 数据库使用独立 PVC

避免共享存储。

---

### 定期创建快照

保护核心数据。

---

### 验证恢复流程

备份不是目的。

恢复成功才是目的。

---

### 监控存储容量

避免磁盘耗尽。

---

## 常见故障排查

查看 PV：

```bash
kubectl get pv
```

---

查看 PVC：

```bash
kubectl get pvc
```

---

查看 StorageClass：

```bash
kubectl get sc
```

---

查看快照：

```bash
kubectl get volumesnapshot
```

---

查看详情：

```bash
kubectl describe pvc mysql-pvc
```

---

## 面试常见问题

### PV 和 PVC 的区别？

PV 提供存储。

PVC 申请存储。

---

### StorageClass 的作用？

定义存储模板并支持动态创建存储。

---

### PVC 为什么一直 Pending？

通常没有匹配到可用 PV。

---

### Kubernetes 如何实现动态存储？

StorageClass + CSI。

---

### VolumeSnapshot 的作用？

存储快照与恢复。

---

## FAQ

### 一个 PVC 能绑定多个 PV 吗？

不能。

---

### 一个 PV 能绑定多个 PVC 吗？

通常不能。

---

### 删除 PVC 会删除数据吗？

取决于回收策略。

---

## 总结

Kubernetes 存储体系通过多个资源对象实现数据持久化。

其中：

- PV 提供存储资源
- PVC 申请存储资源
- StorageClass 定义存储模板
- VolumeSnapshot 提供快照能力

可以记住一句话：

> Pod 负责运行应用，PVC 负责申请存储，PV 负责提供存储，而 StorageClass 负责自动化管理存储。

## 相关阅读

- [Kubernetes API Server 工作原理]()
- [Kubernetes ETCD 工作原理]()
- [Kubernetes Kubelet 工作原理]()
- [Kubernetes CSI 工作原理]()ß