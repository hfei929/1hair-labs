# Kubernetes CNI

## 概述

CNI（Container Network Interface）是容器网络接口标准，定义了容器之间、容器与主机之间的网络连接方式。Kubernetes 通过 CNI 插件实现 Pod 的网络互连。

## CNI 的核心要求

### Pod 网络模型
Kubernetes 要求：
1. **Pod 可以与所有其他 Pod 通信**（即使在不同 Node）
2. **Node 与 Pod 可以互相通信**
3. **Pod 不需要 NAT**（使用真实 IP）
4. **Pod 看到的 IP 与其他 Pod 看到的 IP 相同**

### 实现路径
```
Pod A（IP: 10.244.1.2）
    ↓
虚拟网卡 (veth)
    ↓
Bridge / Overlay Network
    ↓
其他 Node 或 Pod（通过 CNI 打通）
```

## 常见 CNI 实现方案

### 1. Flannel（简单、容易部署）
- 使用 VXLAN、UDP、Host Gateway 等后端
- 适合中小规模集群
- 性能尚可

### 2. Calico（功能丰富、性能优秀）
- 基于 BGP 路由
- 支持 NetworkPolicy 网络策略
- 支持网络加密
- 生产环境推荐

### 3. Weave（功能完整）
- Overlay 网络
- 支持加密、多网络等高级功能
- 性能中等

### 4. Cilium（最先进）
- 基于 eBPF 技术
- 支持微分割、负载均衡等高级特性
- 性能最优
- 学习曲线陡

## CNI 插件的安装与工作流程

### 部署 CNI 插件
```bash
# 以 Calico 为例
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/master/manifests/tigera-operator.yaml
```

### Pod 网络创建流程
```
创建 Pod
    ↓
Kubelet 调用 CNI 插件的 ADD 命令
    ↓
CNI 插件创建虚拟网卡
    ↓
CNI 插件配置 IP 地址和路由
    ↓
Pod 获得网络连接
```

## NetworkPolicy 网络策略

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}  # 适用于所有 Pod
  policyTypes:
  - Ingress
  - Egress
  # 默认拒绝所有入站和出站流量
```

## 常见问题

**Q：Pod 之间无法通信？**
A：检查：
1. CNI 插件是否正确安装
2. Pod IP 范围是否正确配置
3. NetworkPolicy 是否过于严格
4. 网络基础设施（路由、防火墙）是否开放

**Q：如何选择 CNI 插件？**
A：
- 简单场景：Flannel
- 生产环境：Calico
- 高性能场景：Cilium

**Q：能否混合使用多个 CNI 插件？**
A：理论上支持，但不推荐，会增加复杂度和故障排查难度。
