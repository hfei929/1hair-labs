# Kubernetes Scheduler

## 概述

Scheduler 是 Kubernetes 的调度器，负责监听新创建的 Pod，并根据一系列调度算法为 Pod 选择最合适的 Node 进行部署。

## 核心职责

1. **监听未调度的 Pod**：通过 Watch API Server，发现新创建但未指定 Node 的 Pod
2. **资源评估**：评估集群中各个 Node 的资源状态
3. **执行调度算法**：通过一系列过滤和评分函数选择最合适的 Node
4. **绑定 Pod 到 Node**：将选择结果写回 API Server

## 调度算法流程

预选阶段（Predicate）→ 优选阶段（Priority）→ 选择评分最高的 Node → 绑定（Binding）

## 影响调度决策的因素

| 因素 | 说明 |
|------|------|
| **资源请求** | CPU、内存 Request 和 Limit |
| **节点选择器** | nodeSelector、affinity |
| **污点与容忍度** | Taint 和 Toleration |
| **优先级与抢占** | PriorityClass |
| **亲和性** | Pod 亲和性、反亲和性 |

## 常见问题

**Q：Pod 一直 Pending 怎么办？**
A：使用 `kubectl describe pod` 查看 Events，常见原因：资源不足、选择器不匹配、污点不兼容。
