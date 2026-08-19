---

title: Kubernetes Scheduler 工作原理详解：Pod 是如何选择节点的？
description: 深入理解 Kubernetes Scheduler 工作原理，包括调度流程、Filter 与 Score 机制、NodeSelector、Affinity、Taint/Toleration 以及 Pod Pending 故障排查。
keywords:
  - Kubernetes Scheduler
  - K8S Scheduler
  - Kubernetes调度器
  - Pod Pending
  - Kubernetes调度原理
  - Kubernetes架构解析
tags:
  - Kubernetes
  - Scheduler
  - Kubernetes架构
author: HairLabs | 一根头发丝的宽度

---

# Kubernetes Scheduler 工作原理详解：Pod 是如何选择节点的？

## 文章摘要

在 Kubernetes 中，当一个 Pod 被创建后，并不会立即运行，而是先进入 Pending 状态。

此时 Kubernetes Scheduler 会根据节点资源、调度策略、亲和性规则以及污点容忍等条件，为 Pod 选择一个最合适的节点运行。

本文将详细讲解 Scheduler 的工作原理、调度流程以及生产环境中常见的调度问题。

---

## 学习目标

阅读完本文后，你将掌握：

* Scheduler 在 Kubernetes 中的作用
* Pod Pending 的真正原因
* Scheduler 完整调度流程
* Filter 和 Score 机制
* NodeSelector 与 Node Affinity
* Taint 和 Toleration
* 常见调度故障排查方法

---

## 适用人群

本文适合：

* Kubernetes 初学者
* Linux 运维工程师
* DevOps 工程师
* 云计算学习者
* Kubernetes 面试准备人员

---

## 什么是 Scheduler？

如果把 Kubernetes 集群比作一家物流公司：

| 角色   | 对应组件        |
| ---- | ----------- |
| 客户下单 | 创建 Pod      |
| 调度中心 | Scheduler   |
| 仓库   | Worker Node |
| 配送员  | Kubelet     |

当一个新的订单（Pod）出现时：

调度中心需要决定：

> 这个订单应该由哪个仓库负责处理？

这就是 Scheduler 的职责。

---

## Scheduler 在 Kubernetes 中的位置

```text
                 用户
                   │
                   ▼

          kubectl apply

                   │
                   ▼

             API Server

                   │
                   ▼

                 ETCD

                   │
                   ▼

             Scheduler

                   │
                   ▼

          ┌────────┬────────┐
          ▼        ▼        ▼
   
       Node01   Node02   Node03
```

Scheduler 不直接管理容器。

它只负责：

> 为 Pod 选择运行节点。

---

## Scheduler 解决什么问题？

假设集群有三个节点：

```text
Node01
CPU: 8 Core
Memory: 16 GB

Node02
CPU: 4 Core
Memory: 8 GB

Node03
CPU: 16 Core
Memory: 32 GB
```

此时创建一个 Pod：

```yaml
resources:
  requests:
    cpu: "2"
    memory: "2Gi"
```

Scheduler 需要回答：

* 哪个节点资源足够？
* 哪个节点负载最低？
* 哪个节点最符合调度策略？

最终选出最优节点。

---

## Pod 为什么会 Pending？

很多新手第一次接触 Kubernetes 时都会看到：

```bash
kubectl get pod
```

```text
NAME      READY   STATUS
nginx     0/1     Pending
```

其实：

```text
Pending
=
Scheduler 尚未完成调度
```

或者：

```text
Scheduler 找不到合适节点
```

因此：

> Pod Pending 不一定是容器问题，而往往是调度问题。

---

## Scheduler 工作流程

整个调度过程可以分为两个阶段：

### 第一阶段：过滤（Filter）

先排除不能运行 Pod 的节点。

### 第二阶段：评分（Score）

再从剩余节点中选择最优节点。

---

## 第一阶段：Filter

假设集群有：

```text
Node01
Node02
Node03
```

Scheduler 首先进行筛选。

---

### 检查资源是否足够

例如：

Pod 需要：

```yaml
cpu: 8
memory: 16Gi
```

而 Node02：

```text
CPU: 4
Memory: 8Gi
```

显然无法满足。

直接淘汰。

---

### 检查节点状态

如果节点：

```text
NotReady
```

直接排除。

---

### 检查 NodeSelector

Pod：

```yaml
nodeSelector:
  disk: ssd
```

节点：

```text
Node01
disk=ssd

Node02
disk=hdd
```

Node02 被淘汰。

---

### 检查污点（Taint）

节点：

```bash
kubectl describe node node01
```

```text
NoSchedule
```

Pod 没有对应容忍：

```yaml
tolerations:
```

则无法调度。

---

## 第二阶段：Score

经过过滤：

```text
Node01
Node03
```

都符合要求。

Scheduler 开始打分。

---

### 资源利用率

例如：

```text
Node01
CPU 使用率 30%

Node03
CPU 使用率 90%
```

通常：

Node01 得分更高。

---

### Pod 分布均衡

Scheduler 希望：

```text
Node01 10 Pods
Node02 12 Pods
Node03 50 Pods
```

变成：

```text
Node01 20 Pods
Node02 20 Pods
Node03 20 Pods
```

避免热点节点。

---

### 镜像本地缓存

如果节点已经存在镜像：

```text
nginx:latest
```

则得分可能更高。

减少拉取时间。

---

## 最终调度结果

例如：

```text
Node01 90分
Node03 75分
```

Scheduler 选择：

```text
Node01
```

然后更新 Pod：

```yaml
spec:
  nodeName: node01
```

写回 API Server。

---

## Kubelet 如何接手？

Scheduler 完成工作后：

```text
Pod
↓
绑定 Node01
```

Kubelet 通过 Watch 机制发现：

```text
有新任务
```

然后：

```text
拉取镜像
创建容器
启动 Pod
```

最终：

```bash
kubectl get pod
```

```text
Running
```

---

## NodeSelector

最简单的调度方式。

给节点打标签：

```bash
kubectl label node node01 disk=ssd
```

Pod：

```yaml
nodeSelector:
  disk: ssd
```

Scheduler 只能选择：

```text
disk=ssd
```

的节点。

---

## Node Affinity（节点亲和性）

NodeSelector 的增强版。

例如：

```yaml
affinity:
  nodeAffinity:
```

可以实现：

* 必须运行在哪些节点
* 优先运行在哪些节点

比 NodeSelector 更灵活。

---

## Pod Affinity（Pod 亲和性）

希望 Pod 之间靠近部署。

例如：

```text
Web Pod
API Pod
```

尽量部署到同一节点。

减少网络延迟。

---

## Pod Anti-Affinity（反亲和性）

希望 Pod 分散部署。

例如：

```text
MySQL 主节点
MySQL 从节点
```

不能部署到同一节点。

避免单点故障。

---

## Taint 与 Toleration

这是生产环境经常使用的机制。

---

### Taint（污点）

给节点设置：

```bash
kubectl taint nodes node01 gpu=true:NoSchedule
```

表示：

```text
普通 Pod 禁止进入
```

---

### Toleration（容忍）

Pod：

```yaml
tolerations:
- key: gpu
```

允许调度到该节点。

---

## Scheduler 与 ETCD 的关系

很多人误以为：

```text
Scheduler
↓
ETCD
```

实际上：

```text
Scheduler
↓
API Server
↓
ETCD
```

Scheduler 不直接访问 ETCD。

所有数据交互都通过 API Server。

---

## 生产环境常见调度故障

### CPU 不足

查看：

```bash
kubectl describe pod nginx
```

出现：

```text
Insufficient cpu
```

表示节点资源不足。

---

### 内存不足

```text
Insufficient memory
```

---

### 节点 NotReady

```bash
kubectl get nodes
```

```text
NotReady
```

无法参与调度。

---

### 污点阻止调度

```text
node had taints
```

需要添加 Toleration。

---

### NodeSelector 不匹配

```text
node(s) didn't match Pod node selector
```

检查标签配置。

---

## 运维排查命令

查看 Scheduler：

```bash
kubectl get pod -n kube-system | grep scheduler
```

查看日志：

```bash
kubectl logs -n kube-system kube-scheduler-master01
```

查看 Pod 调度事件：

```bash
kubectl describe pod nginx
```

重点关注：

```text
Events
```

部分。

---

## 面试常见问题

### Scheduler 的作用是什么？

负责为 Pod 选择运行节点。

---

### Scheduler 如何选择节点？

通过：

* Filter
* Score

两阶段完成调度。

---

### Pod Pending 一定是资源不足吗？

不是。

还可能是：

* 污点限制
* 标签不匹配
* 节点异常
* 亲和性规则冲突

---

### Scheduler 会直接创建容器吗？

不会。

Scheduler 只负责选择节点。

容器由 Kubelet 创建。

---

## FAQ

### Scheduler 和 Kubelet 的区别？

Scheduler 负责选择节点。

Kubelet 负责运行容器。

---

### Scheduler 可以有多个实例吗？

可以。

生产环境通常部署多个实例实现高可用。

---

### Scheduler 宕机会怎样？

已有 Pod 不受影响。

新的 Pod 无法调度。

---

## 总结

Scheduler 是 Kubernetes 的调度中心。

它负责：

* 资源筛选
* 节点打分
* Pod 绑定
* 调度策略执行

理解 Scheduler 的核心关键在于记住：

> Scheduler 不负责运行容器，它只负责决定 Pod 应该运行在哪台节点上。

当 Pod 长时间处于 Pending 状态时，第一时间就应该检查 Scheduler 的调度结果和事件信息。

---

## 相关阅读

* [Kubernetes API Server 工作原理](api-server.md)
* [Kubernetes Controller Manager 工作原理](controller-manager.md)
* [Kubernetes Kubelet 工作原理](../node/kubelet.md)
* [Kubernetes ETCD 工作原理](etcd.md)