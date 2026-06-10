# Kubernetes CRI

## 概述

CRI（Container Runtime Interface）是容器运行时接口标准，定义了 Kubelet 与容器运行时的交互规范。通过 CRI，Kubernetes 支持多种容器运行时，不再强依赖 Docker。

## CRI 的演进背景

### 之前：Docker 时代
```
Kubelet
  ↓
Dockershim（Docker 适配层）
  ↓
Docker Daemon
  ↓
容器
```

### 现在：CRI 标准化
```
Kubelet
  ↓
CRI Socket
  ↓
容器运行时（Docker / containerd / CRI-O）
  ↓
容器
```

## CRI 核心组件

### 两个主要服务

1. **ImageService**
   - 拉取容器镜像
   - 管理镜像生命周期
   - 支持镜像缓存、删除等操作

2. **RuntimeService**
   - 创建和管理容器
   - 创建和管理 Pod 沙箱
   - 执行容器命令、查看日志等

## 常见容器运行时

### 1. Docker（传统，逐步淘汰）
- 完整的容器解决方案
- 需要 Dockershim 适配
- Kubernetes 1.20+ 开始废弃 Dockershim

### 2. containerd（推荐）
- 轻量级容器运行时
- 性能优秀
- CNCF 项目，得到广泛支持
- 占有率最高

### 3. CRI-O（红帽推荐）
- Kubernetes 特定设计
- 更轻量、安全性更高
- 主要用于 OpenShift

### 4. Kata（安全容器）
- 基于虚拟机的安全容器
- 隔离性更好
- 性能成本更高

## 容器运行时的选择

| 指标 | Docker | containerd | CRI-O | Kata |
|------|--------|-----------|-------|------|
| **性能** | 中 | 高 | 高 | 低 |
| **轻量级** | 否 | 是 | 是 | 否 |
| **安全性** | 中 | 中 | 高 | 很高 |
| **成熟度** | 很高 | 很高 | 中 | 中 |
| **市场占有率** | 最高 | 最高 | 低 | 很低 |

## 镜像拉取流程

```
Pod 定义镜像
    ↓
Kubelet 调用 CRI 拉取镜像
    ↓
容器运行时拉取镜像
    ├─ 检查本地缓存
    ├─ 连接镜像仓库（处理认证）
    ├─ 分层下载（pull layers）
    └─ 解压到本地存储
    ↓
镜像准备就绪
    ↓
创建容器
```

## 配置容器运行时

### containerd 配置示例
```toml
[plugins."io.containerd.grpc.v1.cri"]
  sandbox_image = "k8s.gcr.io/pause:3.6"
  [plugins."io.containerd.grpc.v1.cri".containerd]
    snapshotter = "overlayfs"
```

### Kubelet 配置
```bash
kubelet --container-runtime=remote \
        --container-runtime-endpoint=unix:///run/containerd/containerd.sock
```

## 常见问题

**Q：Dockershim 移除对集群有什么影响？**
A：
- 需要迁移到 containerd、CRI-O 等其他运行时
- 不影响已运行的 Pod
- 新集群部署需要使用新运行时

**Q：如何检查容器运行时？**
A：
```bash
kubectl get nodes -o wide  # 查看 Container Runtime 列
kubectl describe node <node-name>  # 查看详细信息
```

**Q：镜像拉取经常失败？**
A：检查：
1. 网络连接是否正常
2. 镜像仓库认证是否正确
3. 镜像名称和 Tag 是否正确
4. 容器运行时日志（如 containerd logs）
