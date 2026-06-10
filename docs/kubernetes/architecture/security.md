# Kubernetes 安全资源

## 概述

Kubernetes 安全资源控制管理 Pod、Service Account、防护等安全方面。

## 安全授权

### RBAC（Role-Based Access Control）

基于角色的访问控制机制。

#### Role
探索了一个 Namespace 内的权限。

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
spec:
  rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
```

#### RoleBinding
绑定 Role 与 user、group、service account 的关系。

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-reader
subjects:
- kind: User
  name: jane@example.com
  apiGroup: rbac.authorization.k8s.io
```

## Pod 安全上下文

### SecurityContext
定义了 Pod 或容器的安全配置。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-context-demo
spec:
  securityContext:
    runAsUser: 1000
  containers:
  - name: sec-ctx-demo
    image: busybox
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
```

## 常见问题

**Q：如何查看权限配置？**
A：使用 `kubectl auth can-i <verb> <resource> --as=<user>`。

**Q：Pod 无法动作防火墙？**
A：查看 SecurityContext 是否设置驾驶了。
