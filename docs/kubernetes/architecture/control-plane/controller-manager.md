---

title: Kubernetes Controller Manager 工作原理详解：集群自动化运维的核心引擎
description: 深入理解 Kubernetes Controller Manager 工作原理，包括 Deployment Controller、Node Controller、Job Controller、ReplicaSet Controller 等核心控制器的工作机制。
keywords:
  - Kubernetes Controller Manager
  - K8S Controller
  - Kubernetes控制器
  - Deployment Controller
  - ReplicaSet Controller
  - Kubernetes架构原理
tags:
  - Kubernetes
  - Controller Manager
  - Kubernetes架构
author: HairLabs | 一根头发丝的宽度

---

# Kubernetes Controller Manager 工作原理详解：集群自动化运维的核心引擎

## 文章摘要

如果说 API Server 是 Kubernetes 的统一入口，Scheduler 是 Kubernetes 的调度中心，那么 Controller Manager 就是 Kubernetes 自动化能力的核心来源。

它负责持续监控集群状态，并努力让实际状态始终保持与用户期望状态一致。

本文将详细解析 Controller Manager 的组成结构、核心控制器以及 Kubernetes 自动修复能力背后的工作原理。

---

## 学习目标

阅读完本文后，你将掌握：

* Controller Manager 的作用
* 什么是控制器（Controller）
* 声明式管理思想
* Deployment Controller 工作原理
* ReplicaSet Controller 工作原理
* Node Controller 工作原理
* Job Controller 工作原理
* Kubernetes 自动修复机制

---

## 适用人群

本文适合：

* Kubernetes 初学者
* Linux 运维工程师
* DevOps 工程师
* 云计算学习者
* Kubernetes 面试准备人员

---

## 什么是 Controller Manager？

很多刚接触 Kubernetes 的同学都会有一个疑问：

为什么我删除一个 Pod 后，它又自动出现了？

例如：

```bash
kubectl delete pod nginx-xxxxx
```

几秒钟后：

```bash
kubectl get pod
```

发现：

```text
nginx-yyyyy Running
```

Pod 又被重新创建了。

为什么？

答案就是：

> Controller Manager 发现实际状态与期望状态不一致，于是自动进行了修复。

---

## Kubernetes 的声明式管理思想

在传统运维中：

```text
我要启动一个 Nginx
```

管理员需要：

```text
安装软件
启动服务
检查状态
处理故障
```

属于命令式管理。

---

而 Kubernetes 更倾向于：

```yaml
replicas: 3
```

意思是：

```text
我希望有 3 个 Pod
```

至于如何实现：

```text
创建 Pod
补充 Pod
重建 Pod
迁移 Pod
```

全部由 Kubernetes 完成。

这种模式称为：

> 声明式管理（Declarative Management）

---

## Controller Manager 在 Kubernetes 中的位置

```text
                用户
                  │
                  ▼

             API Server

                  │
                  ▼

         Controller Manager

                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼

 Deployment   Node      Job
 Controller Controller Controller

                  │
                  ▼

               ETCD
```

Controller Manager 通过 Watch API Server 持续监听资源变化。

---

## 什么是 Controller？

Controller 中文通常翻译为：

```text
控制器
```

实际上可以理解为：

```text
自动运维程序
```

每种资源背后都有对应控制器。

例如：

| 资源             | 控制器                       |
| -------------- | ------------------------- |
| Deployment     | Deployment Controller     |
| ReplicaSet     | ReplicaSet Controller     |
| Node           | Node Controller           |
| Job            | Job Controller            |
| ServiceAccount | ServiceAccount Controller |

---

## Controller 的工作模式

所有 Controller 都遵循同一个逻辑：

```text
观察（Observe）

    ↓

比较（Compare）

    ↓

修复（Reconcile）
```

又称：

```text
Reconcile Loop
```

即：

```text
调谐循环
```

这是 Kubernetes 最核心的设计思想之一。

---

## Deployment Controller 工作原理

这是日常使用最频繁的控制器。

例如：

```yaml
apiVersion: apps/v1
kind: Deployment

spec:
  replicas: 3
```

用户期望：

```text
3 个 Pod
```

---

### 当前状态正常

```text
期望状态：3

实际状态：3
```

无需操作。

---

### 某个 Pod 异常

例如：

```text
Pod1 Running

Pod2 Running

Pod3 删除
```

此时：

```text
期望状态：3

实际状态：2
```

Deployment Controller 检测到差异。

---

### 自动修复

于是创建新的 Pod：

```text
Pod4 Running
```

最终：

```text
期望状态：3

实际状态：3
```

恢复一致。

---

## ReplicaSet Controller 工作原理

很多人认为 Deployment 直接管理 Pod。

实际上：

```text
Deployment
      ↓
ReplicaSet
      ↓
Pod
```

真正负责维护 Pod 数量的是：

```text
ReplicaSet Controller
```

例如：

```yaml
replicas: 5
```

ReplicaSet Controller 会持续确保：

```text
永远存在 5 个 Pod
```

---

## Node Controller 工作原理

负责管理节点状态。

例如：

```bash
kubectl get nodes
```

```text
worker01 Ready
worker02 Ready
worker03 Ready
```

---

### Node 掉线

如果：

```text
worker02
```

突然断网。

Node Controller 会持续检测心跳。

---

### 节点异常

超过默认时间后：

```text
Ready
    ↓
NotReady
```

---

### Pod 驱逐

持续故障：

```text
Node NotReady
```

Node Controller 会：

```text
驱逐 Pod
重新调度
```

确保业务恢复。

---

## Job Controller 工作原理

适用于一次性任务。

例如：

```yaml
kind: Job
```

执行：

```text
数据库备份
日志归档
数据同步
```

---

### 任务失败

例如：

```text
Job Failed
```

Job Controller 会根据策略：

```text
重新执行
```

直到：

```text
Completed
```

或者达到重试次数。

---

## ServiceAccount Controller

负责自动创建：

```text
ServiceAccount
```

例如：

```text
default
```

用户创建 Namespace 后：

```bash
kubectl create ns test
```

系统自动生成：

```text
default ServiceAccount
```

背后就是该控制器完成的。

---

## Controller Manager 如何工作？

工作流程如下：

```text
API Server

     ↓

Watch Resource

     ↓

Compare

     ↓

Reconcile

     ↓

Update Resource

     ↓

API Server
```

整个过程不断循环。

因此：

```text
Kubernetes 并不是事件驱动

而是持续调谐
```

---

## Controller Manager 与 Scheduler 的区别

很多新人容易混淆。

| 组件                 | 职责     |
| ------------------ | ------ |
| Controller Manager | 保持状态一致 |
| Scheduler          | 选择运行节点 |
| Kubelet            | 创建容器   |

例如：

```text
Deployment 创建 Pod
```

Controller Manager：

```text
发现需要 Pod
```

Scheduler：

```text
决定放哪台机器
```

Kubelet：

```text
真正启动容器
```

---

## 生产环境常见问题

### Pod 被删除又自动恢复

通常是：

```text
Deployment
ReplicaSet
```

控制器重新创建。

---

### Node NotReady

检查：

```bash
kubectl get nodes
```

以及：

```bash
journalctl -u kubelet
```

---

### Job 一直重试

查看：

```bash
kubectl describe job
```

关注：

```text
BackoffLimit
```

配置。

---

## 运维排查命令

查看 Controller Manager：

```bash
kubectl get pod -n kube-system | grep controller
```

查看日志：

```bash
kubectl logs -n kube-system kube-controller-manager-master01
```

查看集群事件：

```bash
kubectl get events -A
```

---

## 面试常见问题

### Controller Manager 的作用是什么？

负责让实际状态始终接近期望状态。

---

### Kubernetes 自动修复是谁实现的？

Controller Manager。

---

### 删除 Pod 为什么会自动恢复？

ReplicaSet Controller 检测到副本数量不足。

---

### Controller Manager 会直接创建容器吗？

不会。

容器由 Kubelet 创建。

---

## FAQ

### Controller 和 Controller Manager 有什么区别？

Controller 是具体控制器。

Controller Manager 是多个控制器的管理进程。

---

### Controller Manager 宕机会怎样？

已有业务正常运行。

但自动扩缩容、自动修复等功能会失效。

---

### Controller Manager 会直接访问 ETCD 吗？

不会。

所有数据交互都通过 API Server。

---

## 总结

Controller Manager 是 Kubernetes 自动化运维能力的核心。

它通过持续运行的 Reconcile Loop：

* 发现问题
* 分析问题
* 自动修复问题

从而让集群始终保持在用户期望状态。

可以记住一句话：

> Scheduler 决定 Pod 去哪里，Kubelet 负责运行 Pod，而 Controller Manager 负责确保 Pod 应该存在。

---

## 相关阅读

* [Kubernetes API Server 工作原理](control-plane/api-server.md)
* [Kubernetes Scheduler 工作原理](control-plane/scheduler.md)
* [Kubernetes Kubelet 工作原理](node/kubelet.md)
* [Kubernetes ETCD 工作原理](control-plane/etcd.md)
* [Kubernetes Deployment 工作原理]()
