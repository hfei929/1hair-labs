---
title: Kubernetes Network 专题
description: Kubernetes 网络模型、CNI、Service、Ingress 与流量入口相关知识的归档专题。
---

# Network 专题

网络是 Kubernetes 里最容易让人“看起来懂、实际又绕”的部分。这里聚焦 Pod 网络、Service 网络、Ingress 入口以及 CNI 插件的原理。

## 主题范围

- Pod 网络创建全过程：从 RunPodSandbox 到 veth pair
- Calico BGP 跨节点通信：BIRD、Felix、IPIP 隧道拆解
- CNI 插件如何为 Pod 分配网络
- Service、Endpoint 与 kube-proxy 的工作方式
- Ingress 与七层流量入口

## 推荐阅读

- [Pod 网络创建全过程](./pod-network-creation.md)
- [Calico BGP 跨节点通信](./calico-bgp.md)
- [CNI 原理](./cni.md)
- [Ingress 原理](./ingress.md)
- [Kube Proxy 原理](./kube-proxy.md)
