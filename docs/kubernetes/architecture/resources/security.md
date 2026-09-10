---
title: Kubernetes 安全资源：从 ServiceAccount 到 RBAC，一条请求要过几道关
description: 拆解 Kubernetes 安全资源：认证/授权/准入三道关分别在哪一层、ServiceAccount 如何给 Pod 身份、RBAC 四个对象的真实关系与 YAML、Secret 为什么只是 Base64 不是加密、Pod Security 三档与 NetworkPolicy 为什么默认危险。并串起与 API Server、etcd 的站内链路。
authors:
  - hfei
date: 2026-09-09
categories:
  - Kubernetes
tags:
  - Kubernetes
  - Security
  - RBAC
  - ServiceAccount
  - Secret
  - NetworkPolicy
  - 云原生
---

# Kubernetes 安全资源：从 ServiceAccount 到 RBAC，一条请求要过几道关

## 先想清楚：Kubernetes 的安全是"三道关"，不是一个开关

很多人以为开了 RBAC 就安全了。实际上任何一次对 API Server 的请求都要连过三关，[API Server 详解](../control-plane/api-server.md) 里拆过：

1. **Authentication（认证）**：你是谁？——ServiceAccount token、客户端证书、OIDC；
2. **Authorization（授权）**：你能干什么？——RBAC 在这一关起作用；
3. **Admission（准入）**：这个请求合不合规？——Pod Security、ResourceQuota 在这一关拦。

三道关里 RBAC 只是第二关。理解这一点，排查"为什么这个操作被拒了"时才能定位到具体哪一关，而不是盯着 RBAC 猜。

## ServiceAccount：Pod 的身份

Pod 访问 API Server 需要身份，这个身份就是 ServiceAccount。每个命名空间默认有一个 `default` SA，Pod 不显式指定就用它：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: prometheus
spec:
  serviceAccountName: prometheus     # 不写就是 default
  automountServiceAccountToken: true # 默认 true，自动挂 token
  containers:
    - name: prometheus
      image: prom/prometheus
```

SA 的身份凭证通过一个 token 自动挂载进 Pod 的 `/var/run/secrets/kubernetes.io/serviceaccount/`。容器里的 client 库（比如 client-go）读这个 token 去 API Server 认证。

两个容易忽略的点：

- **不需要访问 API 的 Pod，把 `automountServiceAccountToken` 关掉**——多挂一个 token 就是多一份泄露面；
- **token 是"有寿命"的**：早期 SA token 是长期有效的 Secret（`kubernetes.io/service-account-token`），1.22 起默认用 **BoundServiceAccountTokenVolume**（projected volume + 有到期时间的 token），Pod 内读到的 token 会自动轮换。

生产上最容易犯的错是**所有 Pod 共用一个 default SA**——等于所有 Pod 共用同一张身份证，任何 Pod 拿到 token 就拥有了 default SA 的全部权限。正确做法是给每个需要访问 API 的组件建独立 SA，再配最小权限的 RBAC。

## RBAC：谁 + 能干什么 + 在哪

RBAC 四个对象，两两一对：

- **Role / RoleBinding**：命名空间内；
- **ClusterRole / ClusterRoleBinding**：集群级。

```yaml
# Role：定义"能干什么"
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
  - apiGroups: [""]          # 核心组
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
---
# RoleBinding：把 Role 授予"谁"
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: default
  name: read-pods
subjects:
  - kind: ServiceAccount
    name: prometheus
    namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

三个容易混淆的点：

- **Role 定义权限，RoleBinding 分发权限**——权限本身和"给谁"是两回事；
- **verbs 要写全**：`get` 能读单个，`list/watch` 才能被 informer 用——很多 controller 因为只配了 `get` 而反复报 forbidden；
- **核心组资源的 apiGroups 写 `[""]`**（空字符串），apps 组写 `["apps"]`，这是新手最容易写错的一处。

ClusterRole 的典型用途：`kubectl get nodes` 这类集群级资源的访问，以及让命名空间级的 Role 引用集群级权限。

验证权限最直接的方式：

```bash
kubectl auth can-i get pods --as=system:serviceaccount:default:prometheus -n default
# yes / no
```

Kubernetes 还内置了几个聚合 ClusterRole：`view`（只读）、`edit`（读写除 RBAC/配额外的资源）、`admin`（命名空间级管理员）。做最小权限时可以直接绑它们，但要注意 `edit` 比想象中大。

## Secret：Base64 不是加密

Secret 存敏感信息没错，但默认它只是 **Base64 编码，不是加密**：

```bash
echo -n 'mypassword' | base64
# bXlwYXNzd29yZA==
```

Base64 一眼可还原，它的意义只是"避免明文直接躺在 YAML 里"，不提供任何机密性。真正要防的是两类：

1. **etcd 落盘**：Secret 明文存在 etcd 里，能读 etcd 的人就能拿到。要开 etcd 加密（encryption at rest，或用 KMS 插件），配置见 [ETCD 详解](../control-plane/etcd.md)；
2. **RBAC 泄露**：能 `get secret` 的人等于能看到所有明文。用 RBAC 收紧 Secret 的读权限，比依赖 Base64"加密"有用得多。

常用类型：`Opaque`（通用）、`kubernetes.io/tls`（TLS 证书）、`kubernetes.io/dockerconfigjson`（镜像仓库认证）、`kubernetes.io/service-account-token`（SA token）。

两个工程细节：Secret 单个对象上限 1MiB，大了会被拒；设置 `immutable: true` 后不能改，适合做不可变凭据。

## Pod Security：限制 Pod 能干什么

RBAC 管"谁能操作 API"，Pod Security 管"Pod 跑起来以后能有多危险"——比如 `privileged: true`、`hostNetwork: true`、挂 hostPath。这些配置本身不违法，但一个被攻破的容器加上这些权限，就可能逃逸到节点。

Pod Security 三个级别：

- **Privileged**：不限制；
- **Baseline**：禁止已知提权路径（privileged 容器、hostPath 等）；
- **Restricted**：最严，面向安全敏感环境。

通过给命名空间打 label 生效：

```bash
kubectl label ns default \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/audit=restricted
```

`enforce` 是强制拒绝，`warn` 只告警，`audit` 只记录。推荐的灰度路径是：先 audit → 再 warn → 最后 enforce。个别必须跑特权容器的命名空间，可以打 `pod-security.kubernetes.io/enforce=privileged` 豁免。

容器层面还有更细的 `securityContext`：

```yaml
spec:
  containers:
    - name: app
      securityContext:
        runAsNonRoot: true        # 禁止以 root 跑
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]           # 丢光默认 capabilities，再按需加
```

## NetworkPolicy：默认允许，默认很危险

Kubernetes 网络默认是"**所有 Pod 之间互通**"。要隔离必须显式用 NetworkPolicy 声明"谁可以访问谁"：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: db          # 这条策略作用于 db Pod
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend   # 只允许 frontend 进来
      ports:
        - protocol: TCP
          port: 3306
```

NetworkPolicy 的 `from`/`to` 可以组合 podSelector、namespaceSelector、ipBlock 三种来源。它只是"声明"，真正落地要靠支持它的 CNI 插件（Calico、Cilium 支持，Flannel 默认不支持），插件选择见 [CNI 详解](../network/cni.md)。

## 准入控制：API Server 前的最后一道闸

RBAC 之后，写入请求还要过 Admission。Admission 分两类：

- **内置准入控制器**：ResourceQuota、LimitRange、NamespaceLifecycle 等，跟着 API Server 走；
- **Webhook**：MutatingAdmissionWebhook（改请求）和 ValidatingAdmissionWebhook（拒请求），调用你自建的 HTTP 服务——服务网格的 sidecar 注入、镜像仓库的准入策略都靠它。

这一层是"为什么 apply 返回成功、实际对象却被改了/拒了"的常见答案。

## 排错：被 Forbidden 了怎么办

```bash
kubectl auth can-i <verb> <resource> -n <ns>       # 当前身份能不能做
kubectl describe rolebinding <name> -n <ns>        # 看绑定关系
kubectl get pod <pod> -o yaml | grep serviceAccount # 看 Pod 用哪个 SA
```

被拒时先判断是第几关：报 `Forbidden` 是 RBAC（第二关），报 `denied by admission` 是准入（第三关），报 `Unauthorized` 是认证（第一关）。

## 推荐阅读

- [API Server 详解](../control-plane/api-server.md) — 认证、鉴权、准入三关的完整链路
- [ETCD 详解](../control-plane/etcd.md) — Secret 的 etcd 加密落盘
- [为什么不能直接改 etcd](../control-plane/why-not-directly-modify-etcd.md) — 绕过 API Server 改 etcd 为什么危险
- [CNI 详解](../network/cni.md) — NetworkPolicy 依赖的网络插件
- [辅助资源](other-resources.md) — ResourceQuota 等准入侧的资源管控