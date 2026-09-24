---
title: Kubernetes 安全资源详解：RBAC、ServiceAccount、Secret、Pod Security 一文讲透
description: 深入理解 Kubernetes 安全资源体系，包括 ServiceAccount、RBAC、Secret、Pod Security、Admission Controller 等核心安全机制。
keywords:
  - Kubernetes安全
  - Kubernetes RBAC
  - ServiceAccount
  - Secret
  - Pod Security
  - Kubernetes权限管理
tags:
  - Kubernetes
  - Security
  - RBAC
author: HairLabs | 一根头发丝的宽度
---

# Kubernetes 安全资源详解：RBAC、ServiceAccount、Secret、Pod Security 一文讲透

## 文章摘要

随着 Kubernetes 在生产环境中的广泛应用，安全问题越来越重要。

如果没有合理的权限控制和安全策略，任何拥有集群访问权限的人都可能误删业务资源，甚至获取敏感数据。

本文将从资源对象和安全体系的角度，系统讲解 Kubernetes 的核心安全资源，帮助你建立完整的 Kubernetes 安全认知框架。

---

## 学习目标

阅读完本文后，你将掌握：

- Kubernetes 安全体系组成
- ServiceAccount 的作用
- RBAC 权限模型
- Secret 的作用
- Pod Security 的作用
- Admission Controller 的作用
- Kubernetes 安全最佳实践

---

## 适用人群

本文适合：

- Kubernetes 初学者
- Linux 运维工程师
- DevOps 工程师
- 云原生学习者
- Kubernetes 面试准备人员

---

## 为什么 Kubernetes 需要安全机制？

假设有一个 Kubernetes 集群：

```text
生产环境
```

---

如果没有任何权限控制：

```text
任何用户
```

都可以执行：

```bash
kubectl delete pod --all
```

---

甚至：

```bash
kubectl delete namespace prod
```

---

后果可想而知。

---

因此 Kubernetes 提供了一套完整的安全体系。

---

## Kubernetes 安全体系

整体架构如下：

```text
用户

↓

Authentication
（身份认证）

↓

Authorization
（权限授权）

↓

Admission
（准入控制）

↓

API Server

↓

Kubernetes资源
```

---

同时还包括：

```text
ServiceAccount

RBAC

Secret

Pod Security

NetworkPolicy
```

---

共同构成 Kubernetes 安全体系。

---

## ServiceAccount

ServiceAccount（服务账号）是 Kubernetes 中最基础的身份资源。

---

很多人熟悉：

```text
User
```

用户账号。

---

但 Pod 也需要身份。

---

例如：

```text
Prometheus

↓

访问 API Server
```

---

此时就需要：

```text
ServiceAccount
```

提供身份。

---

查看：

```bash
kubectl get sa
```

---

默认存在：

```text
default
```

服务账号。

---

### ServiceAccount 的作用

主要用于：

```text
Pod 身份认证
```

---

例如：

```text
Prometheus

ArgoCD

Metrics Server

Dashboard
```

都依赖 ServiceAccount。

---

## 什么是 RBAC？

RBAC 全称：

```text
Role Based Access Control
```

中文：

```text
基于角色的访问控制
```

---

这是 Kubernetes 当前最主流的权限管理机制。

---

简单理解：

```text
用户

↓

角色

↓

权限
```

---

而不是：

```text
用户

↓

直接权限
```

---

这样更容易管理。

---

## RBAC 核心资源

主要包括：

```text
Role

RoleBinding

ClusterRole

ClusterRoleBinding
```

---

## Role

作用：

```text
定义权限
```

---

例如：

允许查看 Pod：

```text
get

list

watch
```

---

但禁止删除。

---

Role 只在：

```text
Namespace
```

范围内生效。

---

## RoleBinding

作用：

```text
绑定权限
```

---

例如：

```text
开发人员

↓

Role
```

---

建立关联。

---

Role 定义权限。

---

RoleBinding 分配权限。

---

## ClusterRole

作用：

```text
集群级权限
```

---

例如：

查看所有节点：

```bash
kubectl get nodes
```

---

这属于：

```text
ClusterRole
```

管理范围。

---

## ClusterRoleBinding

作用：

```text
绑定集群级权限
```

---

关系如下：

```text
ClusterRole

↓

ClusterRoleBinding

↓

User / ServiceAccount
```

---

## Secret

Secret 是 Kubernetes 最常用的安全资源之一。

---

作用：

```text
存储敏感信息
```

---

例如：

```text
数据库密码

API Token

TLS证书

访问密钥
```

---

不推荐直接写入：

```yaml
Deployment
```

配置文件。

---

而应使用：

```text
Secret
```

统一管理。

---

查看：

```bash
kubectl get secret
```

---

## Secret 的常见类型

### Opaque

通用类型。

---

### TLS

证书管理。

---

### Docker Registry

镜像仓库认证。

---

### ServiceAccount Token

服务账号认证。

---

## Pod Security

仅有权限控制还不够。

---

例如：

有人创建：

```yaml
privileged: true
```

---

或者：

```yaml
hostNetwork: true
```

---

可能影响整个节点安全。

---

因此 Kubernetes 提供：

```text
Pod Security
```

机制。

---

作用：

```text
限制 Pod 权限
```

---

## Pod Security 三种级别

### Privileged

限制最少。

---

### Baseline

基础安全要求。

---

### Restricted

最高安全等级。

---

生产环境推荐：

```text
Restricted
```

---

## Admission Controller

准入控制器。

---

工作位置：

```text
用户

↓

API Server

↓

Admission Controller

↓

ETCD
```

---

作用：

```text
资源创建前检查
```

---

例如：

禁止：

```yaml
privileged: true
```

Pod。

---

或者：

```text
必须设置资源限制
```

---

都是 Admission Controller 的职责。

---

## NetworkPolicy 也是安全资源

虽然归类于网络资源。

---

但本质上：

```text
网络隔离
```

也是安全能力。

---

例如：

```text
前端

↓

后端
```

允许。

---

```text
前端

↓

数据库
```

禁止。

---

通过：

```text
NetworkPolicy
```

实现。

---

## Kubernetes 安全资源关系图

整体关系：

```text
User

↓

Authentication

↓

RBAC

↓

Admission Controller

↓

API Server
```

---

Pod 身份：

```text
ServiceAccount
```

---

敏感数据：

```text
Secret
```

---

运行安全：

```text
Pod Security
```

---

网络隔离：

```text
NetworkPolicy
```

---

## 生产环境最佳实践

### 禁止使用默认 ServiceAccount

为业务创建独立账号。

---

### 遵循最小权限原则

只授予必要权限。

---

### 敏感信息使用 Secret

不要写入 YAML 明文。

---

### 开启 Pod Security

推荐：

```text
Restricted
```

模式。

---

### 配置 NetworkPolicy

避免网络完全开放。

---

### 定期审计 RBAC

删除无用权限。

---

## 常见故障排查

查看 ServiceAccount：

```bash
kubectl get sa
```

---

查看 Role：

```bash
kubectl get role
```

---

查看 RoleBinding：

```bash
kubectl get rolebinding
```

---

查看 ClusterRole：

```bash
kubectl get clusterrole
```

---

查看 Secret：

```bash
kubectl get secret
```

---

查看 Pod Security：

```bash
kubectl get ns --show-labels
```

---

## 面试常见问题

### ServiceAccount 的作用是什么？

为 Pod 提供身份。

---

### RBAC 的作用是什么？

权限控制。

---

### Role 和 ClusterRole 的区别？

作用范围不同。

---

### Secret 的作用是什么？

存储敏感数据。

---

### Admission Controller 的作用是什么？

资源准入检查。

---

### Pod Security 的作用是什么？

限制 Pod 高危权限。

---

## FAQ

### Secret 是加密存储吗？

默认仅 Base64 编码。

建议结合 ETCD 加密。

---

### ServiceAccount 会自动创建吗？

每个 Namespace 默认存在一个。

---

### Role 能管理 Node 吗？

不能。

需要 ClusterRole。

---

## 总结

Kubernetes 安全体系围绕身份、权限、准入和数据保护展开。

其中：

- ServiceAccount 提供身份
- RBAC 提供权限控制
- Secret 管理敏感数据
- Pod Security 约束运行权限
- Admission Controller 执行准入检查
- NetworkPolicy 实现网络隔离

可以记住一句话：

> Kubernetes 安全并不仅仅是 RBAC，而是由身份认证、权限授权、准入控制和运行时安全共同构建的完整体系。

---

## 相关阅读

### Kubernetes 架构原理

- Kubernetes API Server 工作原理
- Kubernetes Controller Manager 工作原理
- Kubernetes ETCD 工作原理

### Kubernetes 资源体系

- Kubernetes API 资源详解
- Kubernetes 工作负载资源详解
- Kubernetes 存储资源详解
- Kubernetes 网络资源详解

### 安全相关实战

- Kubernetes RBAC 实战指南（待更新）
- Kubernetes Secret 使用指南（待更新）
- Kubernetes ServiceAccount 实战（待更新）
- Kubernetes NetworkPolicy 实战（待更新）
- Kubernetes Pod Security 实战（待更新）