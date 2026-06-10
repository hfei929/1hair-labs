# Kubernetes 工作负载资源

## 概述

工作负载资源是 Kubernetes 中用来管理 Pod 的资源类型。它们根据应用特性的不同，披着不同的面孔、各司其职。

## 三大策略

### 1. Replicated Workloads（副本控制）
保持一定数量的 Pod 副本一直运行。

- **Deployment**：无状态应用（推荐）
- **ReplicaSet**：控制副本数（通常不直接使用）

### 2. Daemon Workloads（常驻任务）
在每个节点上运行一个 Pod 副本。

- **DaemonSet**：日志收集、监控代理、网络插件等

### 3. Stateful Workloads（有状态应用）
管理有状态的应用（数据库、缓存等）。

- **StatefulSet**：ZooKeeper、Kafka、MySQL 等

## 主要工作负载

### Deployment（应用部署）
- 支持副本控制、灰度更新、回滚
- 无状态应用的最佳选择
- 自动维护 ReplicaSet

### StatefulSet（有状态分布式应用）
- 稳定的身份（Pod 名称、DNS）
- 有序启停
- 持久化存储
- 网络身份

## 常见问题

**Q：Deployment 有什么优势？**
A：支持滚动更新、回滚、自动扩容、自愈机制等。

**Q：StatefulSet 需要什么前提？**
A：是的。StatefulSet 每个 Pod 需要一个独一的身份、存储卷、DNS 名称等。
