---

title: Kubernetes Ingress 工作原理详解：域名访问、HTTPS证书与流量入口一次讲透
description: 深入理解 Kubernetes Ingress 工作原理，包括 Ingress Controller、域名解析、HTTPS证书、反向代理、负载均衡以及生产环境最佳实践。
keywords:

  - Kubernetes Ingress
  - Ingress Controller
  - Nginx Ingress
  - Kubernetes HTTPS
  - Kubernetes域名访问
  - Kubernetes网络
tags:
  - Kubernetes
  - Ingress
  - Kubernetes网络
author: HairLabs

---

# Kubernetes Ingress 工作原理详解：域名访问、HTTPS证书与流量入口一次讲透

## 文章摘要

在 Kubernetes 中，Service 解决了 Pod IP 不稳定的问题，但仍然无法很好地解决域名访问、HTTPS 证书管理、统一流量入口等需求。

为了让用户能够像访问普通网站一样访问 Kubernetes 应用，Kubernetes 引入了 Ingress。

本文将详细讲解 Ingress 的设计目的、工作原理、Ingress Controller 的作用以及 HTTPS 证书配置方案。

---

## 学习目标

阅读完本文后，你将掌握：

* 为什么需要 Ingress
* Ingress 与 Service 的区别
* Ingress Controller 的作用
* 域名访问原理
* HTTPS 工作机制
* TLS 证书配置
* 常见 Ingress Controller
* 生产环境最佳实践

---

## 适用人群

本文适合：

* Kubernetes 初学者
* Linux 运维工程师
* DevOps 工程师
* 云计算学习者
* Kubernetes 面试准备人员

---

## 为什么需要 Ingress？

假设集群中部署了三个业务：

```text
用户系统
订单系统
支付系统
```

对应 Service：

```text
user-service

order-service

pay-service
```

---

如果全部使用 NodePort：

```text
192.168.1.10:30080

192.168.1.10:30081

192.168.1.10:30082
```

虽然能访问。

但存在很多问题：

* 端口难记
* 不支持域名
* 不支持 HTTPS
* 不便统一管理

---

企业生产环境更希望：

```text
user.example.com

order.example.com

pay.example.com
```

统一访问。

---

这就是 Ingress 存在的意义。

---

## Ingress 是什么？

很多新人误以为：

```text
Ingress
=
负载均衡器
```

实际上：

```text
Ingress
=
流量转发规则
```

本质上只是一个 Kubernetes 资源对象。

类似：

```yaml
kind: Deployment
```

或者：

```yaml
kind: Service
```

一样。

---

Ingress 本身不会处理流量。

真正工作的组件是：

```text
Ingress Controller
```

---

## Ingress 在 Kubernetes 中的位置

```text
Internet
    │
    ▼

Ingress Controller

    │
    ▼

Ingress Rules

    │
    ▼

Service

    │
    ▼

Pod
```

---

## Ingress 与 Service 的区别

很多人容易混淆。

| 资源      | 作用                 |
| ------- | ------------------ |
| Service | 暴露服务               |
| Ingress | 管理 HTTP/HTTPS 流量入口 |

---

Service 解决：

```text
Pod 如何被访问
```

---

Ingress 解决：

```text
用户如何访问网站
```

---

## 什么是 Ingress Controller？

这是理解 Ingress 的关键。

---

### Ingress

只是规则：

```yaml
kind: Ingress
```

例如：

```yaml
host: www.example.com
```

---

### Ingress Controller

负责读取规则并生成配置。

常见实现：

* Nginx Ingress Controller
* Traefik
* HAProxy Ingress
* Kong Ingress
* APISIX Ingress

---

可以理解为：

```text
Ingress
=
交通法规

Ingress Controller
=
交警
```

---

## 最常见的 Nginx Ingress Controller

目前使用最广泛。

架构如下：

```text
Internet
    │
    ▼

Nginx Ingress Controller

    │
    ▼

Service

    │
    ▼

Pod
```

---

工作流程：

```text
监听 Ingress 资源

↓

生成 Nginx 配置

↓

热加载配置

↓

转发流量
```

---

## 域名访问原理

假设访问：

```text
www.example.com
```

---

### 第一步：DNS解析

域名解析：

```text
www.example.com

↓

1.2.3.4
```

Ingress 对外地址。

---

### 第二步：请求到达 Ingress

浏览器：

```text
https://www.example.com
```

请求进入 Ingress Controller。

---

### 第三步：匹配规则

例如：

```yaml
host: www.example.com
```

匹配成功。

---

### 第四步：转发 Service

```text
web-service
```

---

### 第五步：转发 Pod

```text
Pod-A

Pod-B

Pod-C
```

---

最终返回页面。

---

## 基于域名的路由

例如：

```yaml
rules:
```

配置：

```text
user.example.com
```

转发：

```text
user-service
```

---

配置：

```text
order.example.com
```

转发：

```text
order-service
```

---

效果：

```text
不同域名

↓

不同业务
```

---

## 基于路径的路由

例如：

```text
example.com/user
```

---

转发：

```text
user-service
```

---

例如：

```text
example.com/order
```

---

转发：

```text
order-service
```

---

效果：

```text
一个域名

↓

多个业务
```

---

## HTTPS 是如何实现的？

这是生产环境最常见需求。

---

浏览器访问：

```text
https://example.com
```

---

TLS 握手发生在：

```text
浏览器

↓

Ingress Controller
```

之间。

---

而不是：

```text
浏览器

↓

Pod
```

之间。

---

因此：

```text
证书通常部署在 Ingress
```

而不是应用容器中。

---

## TLS 证书配置

首先创建 Secret：

```bash
kubectl create secret tls website-tls
```

---

Ingress 引用：

```yaml
tls:
```

配置。

---

效果：

```text
HTTPS

↓

Ingress

↓

HTTP

↓

Pod
```

---

这称为：

```text
TLS Termination
```

即：

```text
SSL卸载
```

---

## 常见 Ingress Controller

### Nginx Ingress

最常见。

适合大部分场景。

---

### Traefik

配置简单。

适合云原生环境。

---

### Kong

支持 API 网关能力。

---

### APISIX

国内使用增长较快。

支持插件扩展。

---

## Ingress 与 LoadBalancer 的关系

很多新人容易混淆。

---

### LoadBalancer

负责：

```text
公网IP
```

---

### Ingress

负责：

```text
流量管理
```

---

生产环境通常：

```text
Internet

↓

LoadBalancer

↓

Ingress

↓

Service

↓

Pod
```

---

## 生产环境最佳实践

### 一个集群部署一个 Ingress Controller

推荐：

```text
统一管理流量
```

---

### 所有业务统一走 HTTPS

避免：

```text
明文传输
```

---

### 使用 Cert-Manager 自动签发证书

减少人工维护。

后续可单独写专题。

---

### 避免大量 NodePort

统一通过 Ingress 暴露。

---

## 常见故障排查

### 域名无法访问

检查：

```bash
nslookup example.com
```

确认 DNS 是否正常。

---

### Ingress 无法生效

查看：

```bash
kubectl get ingress
```

---

### Ingress Controller 未运行

查看：

```bash
kubectl get pod -A
```

确认：

```text
ingress-nginx
```

正常运行。

---

### Service 配置错误

查看：

```bash
kubectl describe ingress
```

确认后端 Service 是否正确。

---

### HTTPS 证书异常

查看：

```bash
kubectl get secret
```

确认 TLS Secret 存在。

---

## 运维排查命令

查看 Ingress：

```bash
kubectl get ingress -A
```

查看详细信息：

```bash
kubectl describe ingress web
```

查看 Ingress Controller：

```bash
kubectl get pod -n ingress-nginx
```

查看日志：

```bash
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

查看证书：

```bash
kubectl get secret
```

---

## 面试常见问题

### Ingress 的作用是什么？

统一管理 HTTP/HTTPS 流量入口。

---

### Ingress 本身能处理流量吗？

不能。

需要 Ingress Controller。

---

### Ingress 与 Service 的区别？

Service 暴露服务。

Ingress 管理访问入口。

---

### HTTPS 证书一般放在哪里？

通常部署在 Ingress Controller。

---

### Ingress Controller 最常见实现？

Nginx Ingress Controller。

---

## FAQ

### 没有 Ingress 可以运行网站吗？

可以。

使用 NodePort 或 LoadBalancer。

但不推荐。

---

### 一个集群可以有多个 Ingress Controller 吗？

可以。

通过 IngressClass 区分。

---

### Ingress 只能处理 HTTP 吗？

标准 Ingress 主要针对：

* HTTP
* HTTPS

TCP/UDP 通常需要额外配置。

---

## 总结

Ingress 是 Kubernetes 应用对外访问体系的核心组件。

它负责：

* 域名访问
* HTTPS 证书管理
* 路径路由
* 虚拟主机管理
* 统一流量入口

可以记住一句话：

> Service 解决 Pod 访问问题，而 Ingress 解决用户访问网站的问题。

---

## 相关阅读

* [Kubernetes Service 详解]
* [Kubernetes Kube-Proxy 工作原理]
* [Kubernetes CNI 工作原理]
* [Kubernetes CoreDNS 工作原理]
* [Kubernetes Cert-Manager 实战]
