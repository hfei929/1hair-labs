# Kubernetes CSI

## 概述

CSI（Container Storage Interface）是容器存储接口标准，定义了存储系统与容器编排平台的交互规范。Kubernetes 通过 CSI 插件实现动态存储卷管理、快照、克隆等功能。

## CSI 的核心概念

### PersistentVolume（持久化卷）
集群级别的存储资源，代表真实的存储空间。

### PersistentVolumeClaim（持久化卷声明）
Pod 对存储的请求，类似于 CPU/内存的 Request。

### StorageClass（存储类）
定义存储的动态配置方式，简化 PV 和 PVC 的绑定过程。

## 存储生命周期

```
Pod 创建并声明 PVC
    ↓
Kubernetes 查找匹配的 PV 或触发动态配置
    ↓
CSI 驱动创建真实存储资源
    ↓
存储卷挂载到 Pod 所在 Node
    ↓
Pod 可以读写存储
    ↓
Pod 删除，存储卷回收（Delete / Retain）
```

## 常见 CSI 实现方案

### 块存储（Block Storage）
| 实现 | 特点 | 应用场景 |
|------|------|--------|
| **Ceph RBD** | 分布式、高可用 | 生产环境推荐 |
| **AWS EBS** | 云原生 | AWS 环境 |
| **vSphere VMDK** | VMware 环保 | vSphere 环境 |
| **iSCSI** | 传统存储 | 已有存储基础设施 |

### 文件存储（File Storage）
| 实现 | 特点 | 应用场景 |
|------|------|--------|
| **NFS** | 简单、兼容性好 | 中小规模集群 |
| **Ceph CephFS** | 分布式、高性能 | 生产环境推荐 |
| **GlusterFS** | 分布式、开源 | 开源场景 |

### 对象存储（Object Storage）
| 实现 | 特点 | 应用场景 |
|------|------|--------|
| **AWS S3** | 云原生 | AWS 环境 |
| **MinIO** | 自托管 | 私有云 |
| **Ceph Object Gateway** | 分布式 | 多功能存储 |

## 存储类示例

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: csi.ceph.com
parameters:
  clusterID: ceph-cluster
  fstype: ext4
allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

## PVC 与 Pod 绑定

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi

---
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: my-pvc
```

## 常见问题

**Q：PVC 一直 Pending？**
A：检查：
1. StorageClass 是否存在
2. 存储空间是否充足
3. CSI 驱动是否正常运行
4. PVC 的 accessMode 是否支持

**Q：如何扩容存储卷？**
A：修改 PVC 的 `spec.resources.requests.storage` 值，StorageClass 需支持 `allowVolumeExpansion: true`。

**Q：如何使用存储快照？**
A：使用 VolumeSnapshot 对象，前提是 CSI 驱动支持快照功能。
