# Kubernetes 其他资源

## 概述

这个章节介绍 Kubernetes 的其他常用资源，包括事件、Namespace、配额、限制范围等。

## 事件（Event）

### 概述
Event 记录了集群发生的各种事件。

### 查看事件
```bash
kubectl get events
kubectl describe pod <pod-name>  # 事件在描述信息中
```

## Namespace（命名空间）

### 概述
Namespace 是 Kubernetes 的资源隔离机制，将集群中的资源分组到不同的逻辑单位中。

### 创建 Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: my-namespace
```

## ResourceQuota（资源配额）

### 概述
ResourceQuota 控制窗 Namespace 中的资源总额。

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "100"
```

## LimitRange（上限范围）

### 概述
LimitRange 控制 Pod 和 Container 的最大、最小资源配置。

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-cpu-limit
spec:
  limits:
  - max:
      cpu: "2"
      memory: "4Gi"
    min:
      cpu: "100m"
      memory: "128Mi"
    type: Container
```

## HorizontalPodAutoscaler（水平自动扩容）

### 概述
HPA 根据资源使用率或自定义指标自动调整 Pod 副本数。

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## VerticalPodAutoscaler（垂直自动扩容）

### 概述
VPA 根据 Pod 的实际使用情况自动调整 Request、Limit。

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-vpa
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: "Auto"
```

## 常见问题

**Q：如何在集群中创建另一个 Namespace？**
A：`kubectl create namespace <name>` 或 apply 一个 YAML 文件。

**Q：如何检查 Namespace 的配额使用情况？**
A：使用 `kubectl describe resourcequota <name>` 查看详细信息。

**Q：HPA 一直延迟扩容？**
A：检查：
1. Metrics Server 是否安装
2. Pod 是否已收集统计数据
3. 设置的指标是否正确
