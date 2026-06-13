---
title: Kubernetes API 资源详解：一文读懂 Kubernetes 所有资源对象
description: 深入理解 Kubernetes API 资源体系，包括 Pod、Deployment、Service、ConfigMap、Secret、Ingress、PV、PVC 等核心资源对象及其关系。
keywords:
  - Kubernetes API资源
  - Kubernetes资源对象
  - Kubernetes架构
  - Deployment
  - Service
  - Pod
tags:
  - Kubernetes
  - API
  - 架构原理
author: HairLabs ｜ 一根头发丝的宽度
---

# Kubernetes API 资源详解：一文读懂 Kubernetes 所有资源对象

## 文章摘要

很多人学习 Kubernetes 时会接触大量资源对象：

- Pod
- Deployment
- Service
- Ingress
- ConfigMap
- Secret
- PVC
- StatefulSet

但往往学到后面越来越混乱。

实际上 Kubernetes 本质上是一个以 API 资源为核心的声明式管理平台。

本文将从整体视角讲解 Kubernetes 资源体系，帮助你建立完整的 Kubernetes 资源认知框架。

---

## 学习目标

阅读完本文后，你将掌握：

- 什么是 Kubernetes API
- 什么是资源对象（Resource）
- Kubernetes 资源分类
- API Group 机制
- Namespace 作用
- 常见资源关系图
- Kubernetes 资源生命周期

---

## 适用人群

本文适合：

- Kubernetes 初学者
- 运维工程师
- DevOps 工程师
- 云原生学习者
- Kubernetes 面试准备人员

---

## Kubernetes 到底是什么？

很多人认为：

```text
Kubernetes 是容器编排平台
```

这句话没有错。

但从架构角度来看：

```text
Kubernetes
=
API Server
+
大量资源对象
+
控制器
```

---

实际上：

Kubernetes 所有功能最终都表现为：

```text
资源对象（Resource）
```

例如：

```yaml
kind: Pod
```

---

```yaml
kind: Deployment
```

---

```yaml
kind: Service
```

---

本质上：

```text
都是 Kubernetes API 资源
```

---

## 什么是 Kubernetes API？

API 可以理解为：

```text
Kubernetes 的操作入口
```

---

例如：

创建 Pod：

```bash
kubectl apply -f pod.yaml
```

---

实际上：

```text
kubectl

↓

API Server

↓

ETCD
```

---

所有资源最终都会经过：

```text
API Server
```

管理。

---

## 什么是 Resource（资源对象）？

资源对象可以理解为：

```text
Kubernetes 中的一切管理单元
```

---

例如：

### 工作负载

```text
Pod
Deployment
StatefulSet
DaemonSet
Job
CronJob
```

---

### 网络资源

```text
Service
Ingress
NetworkPolicy
```

---

### 存储资源

```text
PV
PVC
StorageClass
```

---

### 配置资源

```text
ConfigMap
Secret
```

---

### 集群资源

```text
Node
Namespace
```

---

这些都是 API 资源。

---

## Kubernetes 资源统一结构

几乎所有资源都长这样：

```yaml
apiVersion: apps/v1
kind: Deployment

metadata:
  name: nginx

spec:
```

---

主要包含四部分：

### apiVersion

资源版本。

例如：

```yaml
apps/v1
```

---

### kind

资源类型。

例如：

```yaml
Deployment
```

---

### metadata

资源元数据。

例如：

```yaml
name:
namespace:
labels:
annotations:
```

---

### spec

期望状态。

例如：

```yaml
replicas: 3
```

---

## Kubernetes 的核心思想

Kubernetes 采用：

```text
声明式管理
```

模式。

---

例如：

```yaml
replicas: 3
```

表示：

```text
希望有3个Pod
```

---

而不是：

```text
创建3个Pod
```

---

区别很大。

---

用户负责：

```text
描述目标状态
```

---

Controller 负责：

```text
让现实状态接近期望状态
```

---

## Kubernetes 资源分类

为了便于理解，可以分成六大类。

---

## 第一类：工作负载资源

负责：

```text
运行应用
```

---

主要包括：

| 资源 | 作用 |
|--------|--------|
| Pod | 最小运行单元 |
| Deployment | 无状态应用 |
| StatefulSet | 有状态应用 |
| DaemonSet | 每节点运行 |
| Job | 一次性任务 |
| CronJob | 定时任务 |

---

## 第二类：服务发现资源

负责：

```text
网络访问
```

---

包括：

| 资源 | 作用 |
|--------|--------|
| Service | 服务发现 |
| Ingress | 流量入口 |
| EndpointSlice | 后端地址管理 |

---

## 第三类：存储资源

负责：

```text
持久化存储
```

---

包括：

| 资源 | 作用 |
|--------|--------|
| PV | 存储卷 |
| PVC | 存储申请 |
| StorageClass | 存储模板 |

---

## 第四类：配置资源

负责：

```text
配置管理
```

---

包括：

| 资源 | 作用 |
|--------|--------|
| ConfigMap | 普通配置 |
| Secret | 敏感配置 |

---

## 第五类：安全资源

负责：

```text
权限控制
```

---

包括：

| 资源 | 作用 |
|--------|--------|
| ServiceAccount | 服务身份 |
| Role | 权限 |
| RoleBinding | 权限绑定 |
| ClusterRole | 集群权限 |

---

## 第六类：集群资源

负责：

```text
管理整个集群
```

---

包括：

| 资源 | 作用 |
|--------|--------|
| Node | 节点 |
| Namespace | 命名空间 |
| ResourceQuota | 资源配额 |

---

## Kubernetes 资源关系图

一个典型业务：

```text
Namespace
    │

Deployment
    │

ReplicaSet
    │

Pod
    │

Service
    │

Ingress
```

---

再加上存储：

```text
Pod
 │
PVC
 │
PV
 │
StorageClass
```

---

这就是 Kubernetes 最常见的资源关系链路。

---

## 什么是 API Group？

随着 Kubernetes 资源越来越多。

出现了：

```yaml
apps/v1
batch/v1
networking.k8s.io/v1
```

---

这就是：

```text
API Group
```

机制。

---

例如：

### apps

```yaml
Deployment
StatefulSet
DaemonSet
```

---

### batch

```yaml
Job
CronJob
```

---

### networking

```yaml
Ingress
NetworkPolicy
```

---

用于资源分类管理。

---

## Namespace 的作用

Namespace 可以理解为：

```text
逻辑隔离空间
```

---

例如：

```text
default

kube-system

monitoring

dev

prod
```

---

同一个资源名称：

```text
nginx
```

---

可以同时存在于：

```text
dev
```

和：

```text
prod
```

中。

---

## 查看所有 API 资源

查看支持资源：

```bash
kubectl api-resources
```

---

查看 API 版本：

```bash
kubectl api-versions
```

---

查看资源详情：

```bash
kubectl explain deployment
```

---

查看字段：

```bash
kubectl explain deployment.spec
```

---

## 常见资源生命周期

以 Deployment 为例：

创建：

```yaml
kind: Deployment
```

---

提交：

```bash
kubectl apply
```

---

保存：

```text
ETCD
```

---

控制器处理：

```text
Deployment Controller
```

---

生成：

```text
ReplicaSet
```

---

最终创建：

```text
Pod
```

---

流程：

```text
Deployment

↓

ReplicaSet

↓

Pod
```

---

## 生产环境最佳实践

### 尽量使用声明式管理

推荐：

```bash
kubectl apply
```

---

避免：

```bash
kubectl run
```

长期维护。

---

### 使用 Namespace 隔离环境

例如：

```text
dev

test

prod
```

---

### 使用 Labels 管理资源

方便筛选。

---

### 资源统一 Git 管理

实现 GitOps。

---

## 常见故障排查

查看资源：

```bash
kubectl get all
```

---

查看详细信息：

```bash
kubectl describe pod nginx
```

---

查看 YAML：

```bash
kubectl get pod nginx -o yaml
```

---

查看事件：

```bash
kubectl get events
```

---

## 面试常见问题

### Kubernetes 中什么是资源对象？

Kubernetes 管理的基本单位。

---

### Pod 是资源吗？

是。

---

### Deployment 是资源吗？

是。

---

### Kubernetes 核心管理对象是什么？

API Resource。

---

### Namespace 的作用是什么？

资源隔离。

---

### Deployment 和 Pod 的关系？

Deployment 管理 Pod。

---

## FAQ

### Kubernetes 有多少资源对象？

内置资源超过 60 种。

安装 CRD 后更多。

---

### 为什么所有资源都有 YAML？

因为 Kubernetes 采用声明式管理。

---

### API Version 为什么会变化？

用于兼容新旧版本。

---

## 总结

Kubernetes 本质上是一个资源驱动的平台。

无论是：

- Pod
- Deployment
- Service
- Ingress
- PVC

本质上都是 Kubernetes API 资源。

可以记住一句话：

> 学会 Kubernetes，本质上就是学会管理 Kubernetes 的各种资源对象。

---

## 相关阅读

- [Kubernetes 工作负载资源详解]
- [Kubernetes 服务资源详解]
- [Kubernetes 存储资源详解]
- [Kubernetes 网络资源详解]
- [Kubernetes 安全资源详解]