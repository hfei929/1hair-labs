# Kubernetes Controller Manager

## 概述

Controller Manager 运行多个控制器（Controller），每个控制器负责一类资源的状态管理。通过"观察-分析-执行"的反复循环，确保集群的实际状态向期望状态收敛。

## 控制循环原理

观察（Watch）→ 分析（对比期望与实际）→ 执行（修正操作）→ 重复

## 主要控制器

| 控制器 | 职责 |
|--------|------|
| Deployment Controller | 管理 Deployment，控制副本数 |
| StatefulSet Controller | 管理有状态应用 |
| DaemonSet Controller | 确保每个 Node 运行一个 Pod |
| Job & CronJob Controller | 管理任务和定时任务 |
| Service Controller | 创建和管理 Service 对应的 Endpoint |
| Node Controller | 监控节点状态，处理故障驱逐 |
| PersistentVolume Controller | 管理存储卷生命周期 |

## 工作机制

- **Leader Election**：高可用部署中，多个实例通过 Lease 选举，只有一个活跃
- **Work Queue**：缓存待处理资源，支持重试和退避

## 常见问题

**Q：Deployment 副本数一直不对？**
A：检查节点资源、污点容忍度、资源 Request/Limit，查看 Controller Manager 日志。
