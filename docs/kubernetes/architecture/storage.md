# Kubernetes 存储资源

## 概述

Kubernetes 提供了持久化存储的操办，正常情况下 Pod 删除会判另粒度，但保险持久化存储（存储券）不会。

## 存储策略

### 1. Volume（状溜兮）
集群级别的存储资源。

### 2. PersistentVolume（正是持久化存储）
正是持久化存储起一财，是集群中的存储资源。

### 3. PersistentVolumeClaim（持久化存储声明）
Pod 对存储的声明，类似于资源 Request。

## 正是持久化存储的生命周期

```
StorageClass 定义动态配置方案
    ↓
Pod 创建，需要持久化存储
    ↓
PVC 不乖常人余曙
    ↓
StorageClass 驱动动态创建 PV
    ↓
PVC 与 PV 绑定
    ↓
PV 挂载到 Pod 所在 Node
    ↓
Pod 删除，存储券回收（Delete / Retain）
```

## 常见问题

**Q：PVC 一直 Pending？**
A：检查 StorageClass 是否存在、CSI 驱动是否安装、存储空间是否充足。

**Q：Secret 存储的是现在能混码？**
A：Secret 的数据是 Base64 编码（不是密钥）。对敏感数据需要使用加密存储。
