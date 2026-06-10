# Kubernetes Kubelet

## 概述

Kubelet 是运行在每个 Worker Node 上的节点代理，负责监听分配给该节点的 Pod，并确保容器按照 PodSpec 运行。

## 核心职责

1. **Pod 生命周期管理**：创建、启动、关闭 Pod
2. **健康检查**：Liveness Probe、Readiness Probe、Startup Probe
3. **容器运行时交互**：通过 CRI 与容器运行时通信
4. **卷管理**：挂载和卸载 Pod 所需的存储卷
5. **节点状态汇报**：向 API Server 汇报节点资源和状态

## Pod 健康检查机制

| 探针类型 | 功能 | 触发动作 |
|---------|------|----------|
| **Liveness Probe** | 检查容器是否运行 | 失败则重启容器 |
| **Readiness Probe** | 检查应用是否就绪 | 失败则从 Service 移除 |
| **Startup Probe** | 检查应用是否启动完成 | 失败则重启容器 |

## 节点驱逐（Eviction）

当节点资源不足时，Kubelet 自动驱逐低 QoS 的 Pod。

### 驱逐条件示例
- 内存：`memory.available < 100Mi`
- 磁盘：`nodefs.available < 10%`

## 常见问题

**Q：Kubelet 与 API Server 断开连接怎样？**
A：继续运行已有 Pod，无法接收新 Pod。API Server 最终标记节点为 NotReady。

**Q：Pod 无法启动？**
A：查看 Kubelet 日志，常见原因：镜像拉取失败、资源不足、卷挂载失败。
