---
title: Kubernetes 网络资源详解：Service、Ingress、NetworkPolicy、Gateway API 一文讲透
description: 深入理解 Kubernetes 网络资源体系，包括 Service、Ingress、NetworkPolicy、Gateway API 的作用、关系以及生产环境最佳实践。
keywords:
  - Kubernetes网络
  - Service
  - Ingress
  - NetworkPolicy
  - Gateway API
  - Kubernetes网络资源
tags:
  - Kubernetes
  - Network
  - Networking
author: HairLabs | 一根头发丝的宽度
---

# Kubernetes 网络资源详解：Service、Ingress、NetworkPolicy、Gateway API 一文讲透

## 文章摘要

网络是 Kubernetes 中最重要的基础能力之一。

无论是 Pod 之间通信、服务发现、外部访问，还是网络安全控制，都离不开 Kubernetes 网络资源。

本文将从资源对象的角度，系统讲解 Kubernetes 网络体系，帮助你建立完整的网络认知框架。

---

## 学习目标

阅读完本文后，你将掌握：

- Kubernetes 网络资源体系
- Service 的作用
- Ingress 的作用
- NetworkPolicy 的作用
- Gateway API 的定位
- 服务发现流程
- 流量访问流程
- 网络资源选择原则

---

## 适用人群

本文适合：

- Kubernetes 初学者
- Linux 运维工程师
- DevOps 工程师
- 云原生学习者
- Kubernetes 面试准备人员

---

## Kubernetes 网络到底解决什么问题？

先思考几个问题：

### Pod 如何访问 Pod？

例如：

```text
Pod-A

↓

Pod-B
```

---

### 应用如何访问数据库？

例如：

```text
Java

↓

MySQL
```

---

### 用户如何访问网站？

例如：

```text
Browser

↓

Web Service
```

---

### 如何限制网络访问？

例如：

```text
前端可以访问后端

后端禁止访问数据库
```

---

这些都属于 Kubernetes 网络体系负责解决的问题。

---

## Kubernetes 网络资源体系

整体结构如下：

```text
Ingress / Gateway

↓

Service

↓

EndpointSlice

↓

Pod
```

---

网络安全：

```text
NetworkPolicy
```

---

底层实现：

```text
CNI

Kube-Proxy

CoreDNS
```

---

本文重点关注资源对象。

---

## Service

Service 是 Kubernetes 最基础的网络资源。

---

作用：

```text
提供稳定访问入口
```

---

例如：

```text
Pod-A

Pod-B

Pod-C
```

---

IP 可能变化。

---

Service 提供：

```text
固定访问地址
```

---

客户端只需要访问：

```text
Service
```

即可。

---

### Service 类型

| 类型 | 用途 |
|--------|--------|
| ClusterIP | 集群内部访问 |
| NodePort | 节点端口暴露 |
| LoadBalancer | 云负载均衡 |
| ExternalName | 外部服务映射 |

---

生产环境最常见：

```text
ClusterIP
```

---

## EndpointSlice

很多人只知道 Service。

实际上：

```text
EndpointSlice
```

才保存真实后端地址。

---

例如：

```text
10.244.1.10

10.244.2.11

10.244.3.12
```

---

这些才是真正的 Pod IP。

---

Service：

```text
负责入口
```

---

EndpointSlice：

```text
负责记录后端
```

---

## Ingress

Ingress 是 Kubernetes 最常见的流量入口资源。

---

主要负责：

```text
HTTP

HTTPS
```

流量管理。

---

例如：

```text
www.example.com
```

访问：

```text
web-service
```

---

或者：

```text
api.example.com
```

访问：

```text
api-service
```

---

## Ingress 能做什么？

支持：

### 域名路由

```text
api.example.com
```

---

### 路径路由

```text
/api

/admin
```

---

### HTTPS

TLS 证书管理。

---

### 负载均衡

请求分发。

---

## NetworkPolicy

这是 Kubernetes 网络安全核心资源。

---

默认情况下：

```text
所有 Pod 可以互通
```

---

例如：

```text
Pod-A

↓

Pod-B
```

允许访问。

---

在生产环境：

通常需要限制访问。

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

这就是：

```text
NetworkPolicy
```

的作用。

---

## NetworkPolicy 能控制什么？

### 入站流量

Ingress

---

### 出站流量

Egress

---

例如：

```text
只允许访问3306
```

---

或者：

```text
禁止访问互联网
```

---

都可以实现。

---

## Gateway API

这是 Kubernetes 网络领域的重要发展方向。

---

可以理解为：

```text
Ingress升级版
```

---

相比 Ingress：

支持更复杂流量治理。

---

主要资源：

### GatewayClass

定义实现。

---

### Gateway

定义入口。

---

### HTTPRoute

定义路由。

---

关系：

```text
Gateway

↓

HTTPRoute

↓

Service
```

---

## Service 与 Ingress 的区别

面试高频问题。

| 项目 | Service | Ingress |
|--------|--------|--------|
| 作用 | 服务发现 | 流量入口 |
| 工作层级 | 四层 | 七层 |
| 管理对象 | Pod | Service |
| HTTPS | 不负责 | 支持 |

---

简单理解：

```text
Service 找 Pod

Ingress 找 Service
```

---

## Ingress 与 Gateway API 的区别

| 项目 | Ingress | Gateway API |
|--------|--------|--------|
| 功能 | 基础 | 强大 |
| 扩展性 | 一般 | 优秀 |
| 多团队协作 | 一般 | 更好 |
| 未来趋势 | 当前主流 | 下一代标准 |

---

## Service Mesh 属于网络资源吗？

严格来说：

```text
不是 Kubernetes 原生资源
```

---

但属于：

```text
云原生网络体系
```

重要组成部分。

---

例如：

```text
Istio

Linkerd
```

---

主要解决：

```text
服务治理

流量控制

可观测性
```

问题。

---

## 网络资源关系图

典型访问链路：

```text
Browser

↓

Ingress

↓

Service

↓

EndpointSlice

↓

Pod
```

---

安全控制：

```text
NetworkPolicy
```

---

底层实现：

```text
CNI

Kube-Proxy
```

---

## 生产环境最佳实践

### 内部访问使用 ClusterIP

推荐默认方案。

---

### 外部访问统一使用 Ingress

避免大量 NodePort。

---

### 所有生产 Namespace 配置 NetworkPolicy

避免网络完全开放。

---

### 关注 Gateway API

未来发展方向。

---

## 常见故障排查

查看 Service：

```bash
kubectl get svc
```

---

查看 EndpointSlice：

```bash
kubectl get endpointslice
```

---

查看 Ingress：

```bash
kubectl get ingress
```

---

查看 NetworkPolicy：

```bash
kubectl get networkpolicy
```

---

查看 Gateway：

```bash
kubectl get gateway
```

---

## 面试常见问题

### Service 的作用是什么？

提供稳定访问入口。

---

### EndpointSlice 的作用是什么？

保存后端 Pod 地址。

---

### Ingress 的作用是什么？

管理 HTTP/HTTPS 流量。

---

### NetworkPolicy 的作用是什么？

控制 Pod 网络访问。

---

### Gateway API 是什么？

下一代 Kubernetes 流量管理标准。

---

## FAQ

### 没有 Service 可以访问 Pod 吗？

可以，但不推荐。

---

### NetworkPolicy 默认生效吗？

需要 CNI 支持。

---

### Gateway API 会取代 Ingress 吗？

短期不会。

长期有可能逐步替代部分场景。

---

## 总结

Kubernetes 网络资源负责实现服务发现、流量访问以及网络安全控制。

其中：

- Service 提供服务发现
- EndpointSlice 维护后端地址
- Ingress 提供流量入口
- NetworkPolicy 提供网络隔离
- Gateway API 提供下一代流量治理能力

可以记住一句话：

> Service 解决服务发现，Ingress 解决流量入口，NetworkPolicy 解决网络安全，而 Gateway API 正在定义 Kubernetes 网络的未来。

---

## 相关阅读

### Kubernetes 架构原理

- Kubernetes Kube-Proxy 工作原理
- Kubernetes CNI 工作原理
- Kubernetes API Server 工作原理

### Kubernetes 资源体系

- Kubernetes API 资源详解
- Kubernetes 工作负载资源详解
- Kubernetes 存储资源详解
- Kubernetes 安全资源详解（待更新）

### 网络相关实战

- Kubernetes Service 详解：ClusterIP、NodePort、LoadBalancer 一次讲透
- Kubernetes Ingress 工作原理详解
- Kubernetes Gateway API 实战指南（待更新）
- Kubernetes NetworkPolicy 实战指南（待更新）