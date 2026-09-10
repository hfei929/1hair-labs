---
title: Kubernetes 辅助资源：Namespace、配额、HPA、PDB 这些"配角"在管什么
description: 拆解 Kubernetes 辅助资源：Namespace 为什么只是逻辑隔离不是安全边界、Label 与 Annotation 一个用于查一个用于记、ResourceQuota/LimitRange 如何计量资源、HPA 按什么指标伸缩、PDB 怎么在维护窗口保命、Event 与 Lease 一个记日记一个当心跳。并串起与调度、驱逐、升级、故障演练的站内链路。
authors:
  - hfei
date: 2026-09-09
categories:
  - Kubernetes
tags:
  - Kubernetes
  - Namespace
  - ResourceQuota
  - HPA
  - PDB
  - Label
  - 云原生
---

# Kubernetes 辅助资源：Namespace、配额、HPA、PDB 这些"配角"在管什么

## 配角不是配角：它们管的是"集群的运营性"

Deployment、Service、PV 解决的是"应用怎么跑"，而 Namespace、Label、ResourceQuota、HPA、PDB、Event、Lease 解决的是"集群怎么被管好"。它们不直接承载业务，却决定了资源怎么隔离、怎么计量、怎么自动伸缩、怎么在维护窗口里保命。

本文按"隔离 → 标识 → 计量 → 伸缩 → 保命 → 观察"的顺序串起来。

## Namespace：逻辑隔离，不是安全边界

Namespace 把资源划进不同名字空间，同名资源（比如 `nginx`）可以在 `dev` 和 `prod` 各有一个。但一个经常被误解的点：**Namespace 不是安全边界**——它不提供网络隔离，也不自动做 RBAC 隔离，只是"命名和组织"上的隔离。真正的隔离要配合 RBAC（[安全资源](security.md)）和 NetworkPolicy（[CNI 详解](../network/cni.md)）来做。

默认命名空间：`default`、`kube-system`、`kube-public`、`kube-node-lease`。其中 `kube-node-lease` 很年轻，专门给节点心跳的 Lease 对象住（见下文 Lease）。

## Label 与 Annotation：一个用来查，一个用来记

```yaml
metadata:
  labels:
    app: nginx
    env: prod
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
```

- **Label** 参与 selector：Service 靠它找 Pod、Deployment 靠它认领 Pod。Label 有严格的 key/value 语法，能被索引和查询。
- **Annotation** 不参与选择，只存附加信息（Ingress 配置、`kubectl.kubernetes.io/last-applied-configuration`）。

一句话：Label 是给控制器"筛选"用的，Annotation 是给工具"备注"用的。把想筛选的信息写进 Annotation，selector 就永远选不到。

### selector：matchLabels 与 matchExpressions

选资源有两种写法，复杂场景用表达式：

```yaml
selector:
  matchLabels:
    app: nginx
  matchExpressions:            # 表达式，与 matchLabels 是 AND 关系
    - key: env
      operator: In             # In / NotIn / Exists / DoesNotExist
      values: ["prod", "staging"]
```

`matchExpressions` 支持 `In`、`NotIn`、`Exists`、`DoesNotExist` 四种操作符，能做"标签存在但值不限定"这类筛选。

## ConfigMap：配置与镜像解耦

ConfigMap 存非敏感配置，让"改配置"不必"重新打镜像"：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: prod
  nginx.conf: |
    server {
      listen 80;
    }
```

用法有三种：

```yaml
env:
  - name: APP_ENV
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: APP_ENV          # 1. 注入环境变量
volumes:
  - name: config
    configMap:
      name: app-config        # 2. 挂成文件
```

ConfigMap 和 Secret 的区别就一条：**非敏感用 ConfigMap，敏感用 Secret**（[安全资源](security.md)）。把密码塞进 ConfigMap 是常见反模式。

## ResourceQuota 与 LimitRange：一个管总量，一个管单个

同一个命名空间里没有约束，一个团队就能吃光集群资源。两个资源配合：

```yaml
# ResourceQuota：限制整个命名空间的总量
apiVersion: v1
kind: ResourceQuota
metadata:
  name: quota
  namespace: team-a
spec:
  hard:
    requests.cpu: "16"
    requests.memory: 32Gi
    pods: "20"
    services: "10"
    persistentvolumeclaims: "10"   # 对象个数也能限
---
# LimitRange：限制单个对象并给默认值
apiVersion: v1
kind: LimitRange
metadata:
  name: limits
  namespace: team-a
spec:
  limits:
    - type: Container
      default:
        cpu: 500m
        memory: 512Mi
      defaultRequest:
        cpu: 250m
        memory: 256Mi
      max:
        cpu: "4"
        memory: 8Gi
```

ResourceQuota 管"总量"，LimitRange 管"单个 + 默认值"。注意 ResourceQuota 里 `requests.cpu` 和 `limits.cpu` 是分开的两项——只限 requests 不限 limits，可能被"低 requests、高 limits"钻空子。它们直接和 requests/limits 交互，后者的语义（调度保证 vs cgroup 限制）在 [Requests vs Limits](../../practice/requests-vs-limits.md) 里拆得很细。

## HPA：让副本数跟着负载走

HPA（Horizontal Pod Autoscaler）按指标调整 Deployment 的副本数：

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx
  minReplicas: 2
  maxReplicas: 10
  behavior:               # 防抖：避免指标抖动导致频繁伸缩
    scaleDown:
      stabilizationWindowSeconds: 300   # 观察 5 分钟才缩
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60              # 每分钟最多缩 50%
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

`behavior` 里的 `stabilizationWindowSeconds` 是防抖窗口：指标短暂掉下来不会立刻缩容，要观察满窗口才动。没配这个字段时，负载抖动会让副本数上下跳。

HPA 依赖 metrics-server 提供 CPU/内存指标（custom metrics 走 Prometheus adapter）。它调的是副本数（水平）；VPA（Vertical Pod Autoscaler）调的是单个 Pod 的 requests/limits（垂直），但会和 HPA 冲突、且需要重建 Pod，生产用得少。

HPA 能算准的前提是 requests 配得合理——requests 虚高，HPA 就永远缩不下来。这一层在 [资源优化实战](../../practice/resource-optimization.md) 里有基于监控数据的完整方法。

## PDB：维护窗口里的"最少存活副本"

节点升级、drain 时 Pod 会被驱逐。PDB（Pod Disruption Budget）声明"任意时刻至少几个副本必须活着"：

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: nginx-pdb
spec:
  minAvailable: 2          # 或者 maxUnavailable: 1
  unhealthyPodEvictionPolicy: IfHealthyBudget   # 1.26+：不健康 Pod 怎么算
  selector:
    matchLabels:
      app: nginx
```

`minAvailable` 和 `maxUnavailable` 二选一：前者说"至少几个活着"，后者说"最多几个可以死"。

`kubectl drain` 驱逐前会检查 PDB——不满足就拒绝，避免"升级节点时把整个服务一次打死"。这条链路在 [kubectl drain 到底做了什么](../../practice/kubectl-drain.md) 和 [集群升级实战](../../practice/cluster-upgrade.md) 里都有实战验证。

## Event 与 Lease：集群的"日记"和"心跳"

- **Event**：记录资源发生过的关键动作（Pod 创建、镜像拉取、调度失败、OOMKilled）。它是排错的第一现场，但**有保留期限、会被清理**，不能当长期审计用。

```bash
kubectl get events -n default --sort-by=.lastTimestamp
kubectl describe pod nginx | tail -20     # Events 通常在 describe 尾部
```

- **Lease**：轻量级心跳/选举资源。节点用 `kube-node-lease` 命名空间里的 Lease 上报心跳（比老的 NodeStatus 心跳更省），controller-manager 和 scheduler 用它做 leader election。

Lease 的节点心跳直接决定"节点多久被判 NotReady"，这条在 [API Server 全挂故障演练](../../../lab/api-server-all-down.md) 里有一整节讲心跳丢失后各组件的降级行为。

## 推荐阅读

- [Requests vs Limits](../../practice/requests-vs-limits.md) — 调度保证 vs cgroup 限制，配额的底层语义
- [资源优化实战](../../practice/resource-optimization.md) — 用监控数据配准 HPA 的 requests
- [kubectl drain 到底做了什么](../../practice/kubectl-drain.md) — PDB 在驱逐时的作用
- [集群升级实战](../../practice/cluster-upgrade.md) — PDB 如何保证升级零停机
- [API Server 全挂故障演练](../../../lab/api-server-all-down.md) — Lease 心跳与节点 NotReady 的判定
- [安全资源](security.md) — Secret 与 ConfigMap 的分工
- [安全资源](security.md) — Namespace 配合 RBAC 才是真正的隔离