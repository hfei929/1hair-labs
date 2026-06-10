# Kubernetes API Server

## 概述

API Server 是 Kubernetes 集群的中心，是唯一与 Etcd 通信的组件。它提供了 RESTful 接口，所有对集群资源的操作都必须通过 API Server。

## 核心职责

### 1. 请求处理
- **认证（Authentication）**：验证请求者身份（证书、Token、Basic Auth）
- **授权（Authorization）**：检查请求者是否有权限执行该操作（RBAC、ABAC）
- **准入控制（Admission Control）**：对请求进行校验和变更（ValidatingWebhook、MutatingWebhook）

### 2. 资源存储与读取
- 所有集群资源（Pod、Service、Deployment 等）都存储在 Etcd 中
- API Server 是 Etcd 的唯一客户端

### 3. Watch 机制
- 客户端可以 Watch 资源的变化，实时监听资源更新
- Controller 和 Scheduler 通过 Watch 机制感知资源变化

## 关键配置与安全

### 认证方式
| 方式 | 说明 | 使用场景 |
|------|------|--------|
| Client Certificate | X.509 证书认证 | Kubelet、API Server 间通信 |
| Token | Bearer Token（Service Account Token） | Pod 内应用访问 API |
| Basic Auth | 用户名密码（不推荐） | 开发测试 |
| Webhook | 调用外部服务认证 | 与第三方身份认证系统集成 |

## 常见问题

**Q：API Server 宕机会怎样？**
A：无法创建、修改、删除资源，但已运行的 Pod 不受影响。
