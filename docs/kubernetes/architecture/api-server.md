---
title: Kubernetes API Server 详解：K8S 集群的统一入口
description: 深入理解 Kubernetes API Server 工作原理，包括认证、鉴权、准入控制、ETCD 存储、Watch 机制以及 Pod 创建完整流程，帮助初学者快速掌握 Kubernetes 控制平面的核心组件。
keywords:
  - Kubernetes API Server
  - K8S API Server
  - Kubernetes架构原理
  - Kubernetes控制平面
  - Kubernetes组件解析
  - Kubernetes入门教程
tags:
  - Kubernetes
  - Kubernetes架构
  - API Server
author: 一根头发丝的宽度

---

# Kubernetes API Server 详解：K8S 集群的统一入口

## 文章摘要

API Server 是 Kubernetes 控制平面最核心的组件，也是整个集群的统一入口。无论是 kubectl、Scheduler、Controller Manager、Kubelet 还是第三方平台，几乎所有操作最终都会通过 API Server 完成。

本文将从架构位置、核心职责、工作流程、Watch 机制以及生产环境实践等多个角度，全面解析 Kubernetes API Server 的工作原理。

---

## 学习目标

阅读完本文后，你将掌握：

* API Server 在 Kubernetes 中的定位
* API Server 为什么是集群统一入口
* API Server 的核心职责
* Pod 创建的完整流程
* Watch 机制工作原理
* API Server 高可用架构设计
* 常见故障排查思路

---

## 适用人群

本文适合以下读者：

* Kubernetes 初学者
* Linux 运维工程师
* 云计算学习者
* DevOps 工程师
* 准备 Kubernetes 面试的工程师

---

## 什么是 API Server？

如果把 Kubernetes 集群看成一家大型公司：

| 公司角色   | Kubernetes 组件      |
| ------ | ------------------ |
| 员工提交申请 | Kubectl            |
| 前台接待中心 | API Server         |
| 调度部门   | Scheduler          |
| 行政管理部门 | Controller Manager |
| 一线执行人员 | Kubelet            |
| 档案室    | ETCD               |

那么：**API Server 就是整个公司的前台接待中心。**

任何人想要查询信息、提交申请、修改资料，都必须先经过前台。

在 Kubernetes 中也是如此：

* 创建 Pod
* 删除 Deployment
* 查看 Node
* 修改 ConfigMap
* 查询日志

这些操作最终都会发送给 API Server。

> 可以简单理解为：API Server 是 Kubernetes 集群的大门。

---

## API Server 在 Kubernetes 中的位置

```text
                用户
                  │
                  ▼
            kubectl/UI
                  │
                  ▼
          ┌────────────────┐
          │   API Server   │
          └───────┬────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼

 Scheduler   Controller   Kubelet
              Manager

                  │
                  ▼
                ETCD
```

从架构图中可以看到：

API Server 位于整个 Kubernetes 集群的中心位置。

所有组件都围绕它工作。

---

## 为什么需要 API Server？

很多初学者会产生疑问：

为什么 Scheduler 不直接访问 ETCD？

为什么 Kubelet 不直接修改集群数据？

原因其实很简单：

### 如果没有 API Server

```text
Scheduler ─┐
Kubelet ───┼──► ETCD
Controller ┘
```

可能会导致：

* 数据一致性难以保证
* 权限管理困难
* 安全风险增加
* 组件耦合严重
* 升级维护复杂

---

### 引入 API Server 后

```text
所有组件
     │
     ▼
API Server
     │
     ▼
  ETCD
```

所有组件只需要与 API Server 通信。

而 API Server 负责：

* 权限控制
* 数据校验
* 资源管理
* 数据持久化

这样整个系统就更加安全和稳定。

---

## API Server 的核心职责

API Server 并不仅仅是一个接口服务。

它承担着 Kubernetes 控制平面的多项核心工作。

---

### 1. 接收所有请求

例如：

```bash
kubectl get pod
```

或者：

```bash
kubectl apply -f nginx.yaml
```

这些命令都会发送到 API Server。

---

### 2. 身份认证（Authentication）

认证解决的问题：

> 你是谁？

常见认证方式：

* Client Certificate
* Token
* ServiceAccount
* OIDC

认证通过后才能继续访问集群。

---

### 3. 权限鉴权（Authorization）

鉴权解决的问题：

> 你能做什么？

例如：

用户 A：

```text
允许查看 Pod
```

用户 B：

```text
允许删除 Deployment
```

Kubernetes 主要通过 RBAC 实现权限控制。

---

### 4. 准入控制（Admission Control）

资源真正写入前：

API Server 会进行最后检查。

例如：

```yaml
resources:
  limits:
    cpu: "1"
```

如果超出资源限制：

```text
拒绝创建
```

某些 Admission Controller 还会：

* 自动添加标签
* 自动注入 Sidecar
* 自动增加安全策略

---

### 5. 数据持久化

所有检查通过后：

API Server 将资源写入 ETCD。

```text
API Server
      │
      ▼
    ETCD
```

ETCD 保存着整个 Kubernetes 集群的状态信息。

---

### 6. 提供统一查询接口

例如：

```bash
kubectl get nodes
```

实际过程：

```text
kubectl
   │
   ▼
API Server
   │
   ▼
 ETCD
```

查询结果再返回给用户。

---

## Watch 机制：Kubernetes 高性能的关键

很多人认为 Scheduler 会不断轮询 ETCD：

```text
每秒查询一次
```

实际上并不是。

Kubernetes 使用的是 Watch 机制。

---

### 什么是 Watch？

组件向 API Server 注册监听：

```text
如果资源变化
立即通知我
```

例如：

```text
Scheduler
      │
      ▼
 Watch Pod
```

当新的 Pod 被创建：

```text
API Server
      │
      ▼
立即通知 Scheduler
```

Scheduler 立刻开始调度。

---

### Watch 的优势

相比轮询：

```text
每秒查询一次
```

Watch 机制：

* 响应速度更快
* 网络开销更小
* CPU 消耗更低

因此 Kubernetes 即使管理数千节点依然能够高效运行。

---

## Pod 创建完整流程

下面通过最常见的场景理解 API Server 的工作过程。

执行：

```bash
kubectl apply -f nginx.yaml
```

---

### 第一步：请求发送到 API Server

```text
kubectl
    │
    ▼
API Server
```

---

### 第二步：认证

检查用户身份是否合法。

```text
Authentication
```

---

### 第三步：鉴权

检查用户是否有权限创建资源。

```text
Authorization
```

---

### 第四步：准入控制

检查资源是否符合规范。

```text
Admission Control
```

---

### 第五步：写入 ETCD

```text
Pod Object
      │
      ▼
    ETCD
```

此时 Pod 仅仅是一条记录。

容器尚未启动。

---

### 第六步：Scheduler 发现新 Pod

```text
Pending
```

开始寻找合适节点。

---

### 第七步：绑定节点

例如：

```text
worker01
```

Scheduler 将结果写回 API Server。

---

### 第八步：Kubelet 创建容器

Kubelet 通过 Watch 发现任务。

然后调用容器运行时：

```text
containerd
```

创建容器。

---

### 第九步：Pod 运行成功

最终状态：

```text
Running
```

用户执行：

```bash
kubectl get pod
```

即可看到 Pod 正常运行。

---

## API Server 默认端口

默认监听端口：

```text
6443
```

查看方式：

```bash
ss -lntp | grep 6443
```

---

## API Server 高可用架构

生产环境不会只部署一个 API Server。

典型架构如下：

```text
              VIP
               │
               ▼

    API Server 01
    API Server 02
    API Server 03

               │
               ▼

              ETCD
```

常见负载均衡方案：

* HAProxy
* Keepalived
* Nginx
* 云厂商 SLB

---

## 生产环境中的常见故障

### API Server 无法访问

表现：

```bash
kubectl get nodes
```

返回：

```text
connection refused
```

---

### 新资源无法创建

表现：

```bash
kubectl apply
```

执行失败。

---

### Scheduler 停止调度

新 Pod 长时间保持：

```text
Pending
```

---

### Node 状态异常

Kubelet 无法向 API Server 汇报状态。

导致节点显示：

```text
NotReady
```

---

## 运维排查命令

查看组件状态：

```bash
kubectl get pod -n kube-system
```

查看 API Server 日志：

```bash
kubectl logs -n kube-system kube-apiserver-master01
```

健康检查：

```bash
curl -k https://127.0.0.1:6443/healthz
```

正常返回：

```text
ok
```

查看指标：

```bash
curl -k https://127.0.0.1:6443/metrics
```

---

## 面试常见问题

### Kubernetes 的统一入口是什么？

API Server。

---

### 哪个组件直接访问 ETCD？

API Server。

---

### Scheduler 如何获取 Pod 信息？

通过 API Server Watch 机制。

---

### API Server 默认端口是多少？

6443。

---

### API Server 宕机会怎样？

控制平面基本停止工作。

新的资源无法创建和调度。

---

## FAQ

### API Server 和 ETCD 有什么关系？

ETCD 负责存储数据，API Server 负责管理和访问数据。

API Server 是唯一直接操作 ETCD 的 Kubernetes 核心组件。

---

### API Server 为什么如此重要？

因为 Kubernetes 中几乎所有组件都依赖 API Server 进行通信。

---

### 可以关闭 API Server 吗？

不可以。

API Server 是控制平面的核心服务。

---

### 为什么 Kubernetes 使用 Watch 机制？

为了减少轮询带来的性能损耗，提高资源变化的响应速度。

---

## 总结

API Server 是 Kubernetes 控制平面的核心枢纽。

它承担了：

* 集群统一入口
* 身份认证
* 权限控制
* 准入管理
* 数据持久化
* Watch 事件分发

等关键职责。

对于 Kubernetes 来说：

> 所有资源管理操作，本质上都是在和 API Server 打交道。

掌握 API Server 的工作原理，是深入理解 Kubernetes 架构的第一步。

---

## 相关阅读

* [Kubernetes Scheduler 工作原理](scheduler.md)
* [Kubernetes Controller Manager 工作原理](controller-manager.md)
* [Kubernetes Kubelet 工作原理](./kubelet.md)
* [Kubernetes ETCD 工作原理](etcd.md)
* [Kubernetes CNI 网络模型解析](cni.md)
* [Kubernetes CSI 存储架构解析](csi.md)
