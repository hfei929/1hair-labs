# Kubernetes Etcd

## 概述

Etcd 是 Kubernetes 的分布式键值存储，保存了集群的所有状态数据。它是高可用集群的基石，提供强一致性、高可用和容灾能力。

## 核心特性

### 1. 强一致性（Strong Consistency）
- 基于 Raft 共识算法
- 同一时刻只有一个 Leader
- 所有数据修改必须通过 Leader
- 保证数据一致性

### 2. Watch 机制
- 客户端可以监听 Key 的变化
- Kubernetes Controller、Scheduler 都通过 Watch 机制获得资源更新通知
- 比轮询查询高效得多

### 3. 事务支持
- 支持多个操作的原子事务
- 确保数据的一致性

## Etcd 数据结构

### 键值存储
Etcd 中的所有 Kubernetes 资源都存储为键值对：

```
/registry/pods/default/my-pod
/registry/services/default/my-service
/registry/deployments/default/my-deployment
/registry/nodes/worker-1
```

### 版本号（Revision）
每次修改都会产生新的 revision，支持时间点恢复。

## Etcd 集群架构

### 单实例（开发测试）
```
Etcd 单实例
    ↓
API Server 单点
```

### 高可用集群（生产推荐）
```
┌─────────────┬─────────────┬─────────────┐
│ Etcd 1      │ Etcd 2      │ Etcd 3      │
│ (Leader)    │ (Follower)  │ (Follower)  │
└──────┬──────┴──────┬──────┴──────┬──────┘
       │             │             │
       └─────────────┴─────────────┘
            (Raft 共识)
              ↓
        API Server 读写
```

## Etcd 高可用与容灾

### Quorum 原理
- 3 个实例：可容忍 1 个故障
- 5 个实例：可容忍 2 个故障
- 推荐使用奇数个实例

### 备份与恢复

```bash
# 备份
etcdctl --endpoints=127.0.0.1:2379 snapshot save backup.db

# 恢复
etcdctl snapshot restore backup.db \
  --data-dir=/var/lib/etcd-new
```

## 关键配置参数

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `--initial-cluster` | 集群节点列表 | node1,node2,node3 |
| `--snapshot-count` | 触发快照的操作数 | 10000 |
| `--heartbeat-interval` | Leader 心跳间隔 | 100ms |
| `--election-timeout` | 选举超时 | 1000ms |

## 常见问题

**Q：Etcd 发生脑裂（Split Brain）怎么办？**
A：Raft 算法保证脑裂时只有多数派继续运行，少数派自动停止，确保数据一致性。

**Q：如何扩容 Etcd 集群？**
A：通过 `etcdctl member add` 添加新成员，但建议使用 Kubeadm 等工具自动化处理。

**Q：Etcd 故障对集群的影响？**
A：
- 1 个故障：集群继续运行
- Etcd 完全故障：API Server 无法读写，集群不可用
- 数据损坏：需要从备份恢复
