# Kubernetes API 资源

## 概述

Kubernetes 中的一切都是资源（Resource）。资源是 Kubernetes API 中的对象，可以通过 kubectl 或 API 调用进行决策、配置和管理。

## API 分组（API Group）

### 核心 API 组
| API 组 | 说明 | 常见资源 |
|--------|--------|--------|
| **v1** | 核心 API | Pod、Service、ConfigMap、Secret |
| **apps/v1** | 应用管理 | Deployment、StatefulSet、DaemonSet |
| **batch/v1** | 任务管理 | Job、CronJob |
| **networking.k8s.io/v1** | 网络策略 | NetworkPolicy、Ingress |
| **storage.k8s.io/v1** | 存储管理 | StorageClass、PersistentVolume |
| **rbac.authorization.k8s.io/v1** | 权限管理 | Role、RoleBinding、ClusterRole |

## 资源的三个粒度

### Cluster-scoped（集群级）
不属于任何 Namespace，作用于整个集群。
- Node
- Namespace
- ClusterRole
- StorageClass

### Namespace-scoped（命名空间级）
属于某个 Namespace，作用于命名空间内的资源。
- Pod
- Service
- ConfigMap
- Deployment

## 常见问题

**Q：spec 与 status 有什么区别？**
A：spec 是你声明的期望状态，status 是实际运行状态，由 Kubernetes 自动更新。
