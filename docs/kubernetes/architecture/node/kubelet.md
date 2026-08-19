---

title: Kubernetes Kubelet 工作原理详解：Node 节点上的核心管家
description: 深入理解 Kubernetes Kubelet 工作原理，包括 Pod 创建流程、节点注册、状态上报、健康检查、容器生命周期管理以及生产环境常见故障排查。
keywords:
  - Kubernetes Kubelet
  - K8S Kubelet
  - Kubernetes节点管理
  - Pod创建流程
  - Kubernetes架构原理
  - Kubernetes组件解析
tags:
  - Kubernetes
  - Kubelet
  - Kubernetes架构
author: HairLabs

---

# Kubernetes Kubelet 工作原理详解：Node 节点上的核心管家

## 文章摘要

Kubelet 是运行在每个 Kubernetes 节点上的核心组件。

如果说 Scheduler 负责决定 Pod 应该运行在哪个节点，那么 Kubelet 则负责真正创建、监控和维护这些 Pod。

本文将从节点注册、Pod 创建流程、状态上报、健康检查以及故障排查等多个角度，全面解析 Kubelet 的工作原理。

---

## 学习目标

阅读完本文后，你将掌握：

* Kubelet 的作用和职责
* Kubelet 在 Kubernetes 中的位置
* Pod 创建完整流程
* Kubelet 与 Container Runtime 的关系
* 节点心跳机制
* Pod 健康检查原理
* 常见 Kubelet 故障排查方法

---

## 适用人群

本文适合：

* Kubernetes 初学者
* Linux 运维工程师
* DevOps 工程师
* 云计算学习者
* Kubernetes 面试准备人员

---

## 什么是 Kubelet？

如果把 Kubernetes 集群比作一家物流公司：

| 角色    | Kubernetes组件      |
| ----- | ----------------- |
| 调度中心  | Scheduler         |
| 仓库    | Node              |
| 仓库管理员 | Kubelet           |
| 工人    | Container Runtime |
| 包裹    | Pod               |

Scheduler 决定：

```text
这个订单交给哪个仓库
```

而真正执行工作的：

```text
仓库管理员
```

也就是：

```text
Kubelet
```

---

## Kubelet 在 Kubernetes 中的位置

```text
               API Server
                    │
                    ▼

               Scheduler

                    │
                    ▼

             Pod绑定节点

                    │
                    ▼

┌─────────────────────────────┐
│           Node01            │
│                             │
│         Kubelet             │
│             │               │
│             ▼               │
│       Containerd            │
│             │               │
│             ▼               │
│          Pod运行            │
└─────────────────────────────┘
```

Kubelet 运行在每个 Worker Node 上。

每个节点都必须有自己的 Kubelet。

---

## Kubelet 的核心职责

Kubelet 主要负责：

* 向集群注册节点
* 创建 Pod
* 管理容器生命周期
* 执行健康检查
* 上报节点状态
* 上报 Pod 状态
* 挂载存储卷
* 获取 Secret 和 ConfigMap

简单来说：

> Kubelet 负责把 Kubernetes 配置变成实际运行的容器。

---

## Kubelet 启动后做什么？

当 Kubelet 服务启动后：

```bash
systemctl start kubelet
```

首先会向 API Server 注册自己。

---

### 节点注册

Kubelet：

```text
我是 Node01
```

向 API Server 发起注册请求。

API Server 创建：

```yaml
kind: Node
```

资源对象。

此时：

```bash
kubectl get nodes
```

可以看到：

```text
node01 Ready
```

---

## Pod 创建完整流程

这是理解 Kubelet 最重要的一部分。

---

### 第一步：创建 Deployment

用户执行：

```bash
kubectl apply -f nginx.yaml
```

---

### 第二步：Controller 创建 Pod

Deployment Controller 创建 Pod 对象。

---

### 第三步：Scheduler 完成调度

Scheduler 选择：

```text
node01
```

并写入：

```yaml
spec:
  nodeName: node01
```

---

### 第四步：Kubelet 发现任务

Node01 上的 Kubelet 一直在 Watch API Server。

发现：

```text
有新的 Pod 分配给我
```

---

### 第五步：获取 Pod 配置

Kubelet 获取：

```yaml
镜像名称
环境变量
挂载卷
网络配置
资源限制
```

等信息。

---

### 第六步：调用 Container Runtime

例如：

```text
containerd
```

或者：

```text
CRI-O
```

Kubelet 并不会直接创建容器。

而是通过 CRI 调用运行时。

```text
Kubelet
    │
    ▼
Container Runtime
    │
    ▼
Container
```

---

### 第七步：拉取镜像

例如：

```text
nginx:latest
```

如果本地不存在：

```text
自动拉取
```

---

### 第八步：创建容器

Container Runtime：

```text
创建 Namespace

创建 Cgroup

创建网络

挂载存储
```

最终启动容器。

---

### 第九步：状态上报

Kubelet 向 API Server 汇报：

```text
Pod Running
```

用户查看：

```bash
kubectl get pod
```

即可看到：

```text
Running
```

---

## Kubelet 与 Container Runtime 的关系

很多新手容易混淆：

```text
Kubelet
=
创建容器
```

实际上并不是。

---

### Kubelet

负责：

```text
管理
调度执行
状态监控
```

---

### Container Runtime

负责：

```text
创建容器
停止容器
删除容器
```

---

关系如下：

```text
Kubelet
    │
    ▼

CRI

    │
    ▼

Containerd
CRI-O

    │
    ▼

Container
```

---

## Kubelet 的心跳机制

为什么：

```bash
kubectl get nodes
```

能够实时看到：

```text
Ready
NotReady
```

状态？

原因就是 Kubelet 的心跳机制。

---

### 定期汇报状态

Kubelet 会持续向 API Server 发送：

```text
CPU

Memory

Disk

Network
```

等节点信息。

---

### 正常状态

```text
Node Ready
```

---

### 网络故障

如果 API Server 长时间收不到心跳：

```text
Node Ready
      ↓
Node NotReady
```

---

### Controller Manager 接管

Node Controller 发现：

```text
NotReady
```

后开始驱逐 Pod。

实现故障恢复。

---

## Pod 健康检查

Kubelet 负责执行：

```yaml
livenessProbe
readinessProbe
startupProbe
```

---

### Liveness Probe

检测：

```text
容器是否活着
```

失败后：

```text
重启容器
```

---

### Readiness Probe

检测：

```text
是否可以接收流量
```

失败后：

```text
从 Service 后端移除
```

---

### Startup Probe

检测：

```text
应用是否启动完成
```

适用于：

```text
Java
数据库
大型应用
```

启动时间较长场景。

---

## Kubelet 如何管理 Pod 生命周期？

Pod 生命周期：

```text
Pending

↓

ContainerCreating

↓

Running

↓

Succeeded

Failed
```

整个过程中：

Kubelet 持续监控状态变化。

---

## Kubelet 与 ETCD 的关系

很多人误认为：

```text
Kubelet
    ↓
ETCD
```

实际上：

```text
Kubelet
    ↓
API Server
    ↓
ETCD
```

Kubelet 不会直接访问 ETCD。

所有数据交互都通过 API Server。

---

## 生产环境常见问题

### Pod 一直 ContainerCreating

查看：

```bash
kubectl describe pod nginx
```

可能出现：

```text
ImagePullBackOff
```

或者：

```text
FailedMount
```

---

### Node NotReady

查看：

```bash
systemctl status kubelet
```

确认服务是否正常。

---

### 镜像拉取失败

查看：

```bash
journalctl -u kubelet
```

可能出现：

```text
ErrImagePull
```

---

### 磁盘空间不足

Kubelet 会触发：

```text
DiskPressure
```

节点状态。

---

### 内存不足

触发：

```text
MemoryPressure
```

系统可能开始驱逐 Pod。

---

## 运维排查命令

查看服务状态：

```bash
systemctl status kubelet
```

查看日志：

```bash
journalctl -u kubelet -f
```

查看节点：

```bash
kubectl get nodes
```

查看节点详情：

```bash
kubectl describe node node01
```

查看 Pod 事件：

```bash
kubectl describe pod nginx
```

---

## 面试常见问题

### Kubelet 的作用是什么？

负责管理节点上的 Pod 和容器。

---

### Kubelet 会直接创建容器吗？

不会。

由 Container Runtime 创建。

---

### Kubelet 如何获取任务？

通过 Watch API Server 获取资源变化。

---

### Node NotReady 是谁发现的？

Controller Manager 发现。

但状态由 Kubelet 上报。

---

### Kubelet 会直接访问 ETCD 吗？

不会。

所有数据通过 API Server。

---

## FAQ

### 每个节点都需要 Kubelet 吗？

需要。

没有 Kubelet 就无法运行 Pod。

---

### Kubelet 宕机会怎样？

已经运行的容器可能继续运行。

但节点状态无法更新。

新的 Pod 无法创建。

---

### Docker 被移除后 Kubelet 还能工作吗？

可以。

当前主流运行时：

* Containerd
* CRI-O

---

## 总结

Kubelet 是 Kubernetes 节点上的核心管理组件。

它负责：

* 节点注册
* Pod 创建
* 容器管理
* 状态上报
* 健康检查

如果说：

```text
Controller Manager 决定应该有什么

Scheduler 决定放在哪里

Kubelet 决定如何真正运行起来
```

那么 Kubelet 就是 Kubernetes 工作负载最终落地执行的关键组件。

---

## 相关阅读

* [Kubernetes API Server 工作原理](../control-plane/api-server.md)
* [Kubernetes Controller Manager 工作原理](../control-plane/controller-manager.md)
* [Kubernetes Scheduler 工作原理](../control-plane/scheduler.md)
* [Kubernetes CRI 工作原理](cri.md)
* [Kubernetes Pod 生命周期详解]()
