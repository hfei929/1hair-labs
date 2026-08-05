---
title: Kubernetes Node 与运行时专题
description: 从 Worker Node、kubelet、CRI、containerd 到 Pod 生命周期，系统梳理 Kubernetes 节点层与容器运行时相关内容。
---

# Node 与运行时专题

Node 与运行时是 Kubernetes 最接近“实际执行层”的部分。这里的文章聚焦“容器到底是怎样在节点上被创建、管理和销毁的”。

## 主题范围

- Worker Node 架构：理解节点在集群中的职责
- Pod 生命周期：从 Pending 到 Running 的完整过程
- kubelet SyncLoop：kubelet 如何持续调谐 Pod 状态
- CRI 与 containerd：kubelet 和运行时之间如何协作
- 容器运行时的执行链路：从 CRI 到 runc 到 Linux 内核

## 推荐阅读

- [Worker Node 架构原理](../worker-node.md)
- [Kubernetes Pod 生命周期源码解析](../pod-lifecycle.md)
- [Kubelet SyncLoop 工作原理](../kubelet-syncloop.md)
- [CRI gRPC 调用详解](../cri-grpc-deep.md)
- [containerd 创建容器全过程](../containerd-from-cri-to-runc.md)
