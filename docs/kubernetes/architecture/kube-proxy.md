# Kubernetes Kube Proxy

## 概述

Kube Proxy 是运行在每个 Worker Node 上的网络代理，负责维护网络规则，实现 Service 的负载均衡和流量转发。

## 核心职责

1. **Service 发现与监听**：通过 API Server Watch Service 和 Endpoint 的变化
2. **规则维护**：维护网络规则（iptables、IPVS、nftables 等）
3. **负载均衡**：将访问 Service IP 的流量分发到后端 Pod
4. **会话保持**：支持 Session Affinity 实现会话粘性

## Kube Proxy 的三种工作模式

### 1. userspace 模式（已废弃）
- 所有流量都经过 Kube Proxy 用户空间处理
- 性能低，基本不使用

### 2. iptables 模式（默认）
- 使用 Linux iptables 规则转发流量
- 性能较好，但规则多时性能下降
- 不支持优雅超时处理

### 3. IPVS 模式（推荐）
- 基于 Linux IPVS（IP Virtual Server）
- 性能最优，支持多种负载均衡算法
- 支持会话保持、连接超时等

## Service 流量转发流程

```
Pod 访问 Service IP（如 10.96.0.1:80）
    ↓
Kube Proxy 拦截（iptables 或 IPVS 规则）
    ↓
选择后端 Pod IP（负载均衡算法）
    ↓
NAT 转换，转发流量到 Pod IP:Port
    ↓
流量到达 Pod 容器
```

## 负载均衡算法

| 算法 | 说明 | 应用场景 |
|------|------|--------|
| Round Robin | 轮询 | 默认算法 |
| Least Connection | 最少连接 | 长连接应用 |
| Source Hash | 基于源 IP 哈希 | 需要会话保持 |
| Destination Hash | 基于目标 IP | 特殊场景 |

## 会话保持（Session Affinity）

通过 `service.spec.sessionAffinity: ClientIP` 实现

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

## 常见问题

**Q：Service IP 无法访问？**
A：检查：
1. Kube Proxy 是否运行
2. iptables/IPVS 规则是否存在
3. Endpoint 是否创建正确
4. Pod 网络是否连通

**Q：IPVS 模式的优势是什么？**
A：性能更优（内核级别实现）、支持更多负载均衡算法、连接跟踪更精准。

**Q：如何监控 Kube Proxy 的状态？**
A：检查 Kube Proxy 日志和 Prometheus 指标（`kube_proxy_*`）。
