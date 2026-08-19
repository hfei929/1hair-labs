---
title: Lab 实验室 - 1HairLabs
description: 故障演练与技术验证实验室，记录 Kubernetes 高可用故障注入、ETCD 恢复、Pod OOM、CPU 压力测试等真实实验过程，所有结论均经过验证。
hide:
  - comments
---

# Lab 实验室

所有结论都应经过验证。

这里记录各种实验环境中的故障演练、问题复现和技术验证过程。与教程不同，Lab 关注的不是"怎么安装"，而是"坏了之后会怎样"——通过主动注入故障，观察系统的真实反应，验证架构设计是否经得起考验。

---

## 内容索引

### HA 故障演练系列

基于 3 Master + 3 Worker + HAProxy + Keepalived 的生产级 HA 集群，逐层注入故障，验证高可用架构的真实表现。

| 文章 | 故障场景 | 核心验证 |
|---|---|---|
| [EP.1：一台 Master 宕机](failover-test-1.md) | 强制关闭一台 Master 节点 | kubectl 是否中断、ETCD 多数派是否保持、业务是否受影响 |
| [EP.2：LB 节点整机宕机](failover-test-2.md) | 打挂 Keepalived + HAProxy 所在的负载均衡器 | VIP 能否自动漂移、漂移过程中 kubectl 是否中断 |
| [EP.3：ETCD 多数派失效](failover-test-3.md) | 停掉 3 个 ETCD 中的 2 个，破坏多数派 | 控制平面是否瘫痪、数据平面是否存活、能否恢复 |

> 系列结论：Master 宕机 → 集群无感知；LB 宕机 → VIP 2~3 秒漂移，kubectl 短暂卡顿后恢复；ETCD 多数派失效 → 控制平面不可写，但已运行 Pod 不受影响。

### 资源压力测试

模拟生产环境中最常见的资源耗尽场景，观察 Kubernetes 和 Linux 内核如何响应，以及监控系统能否提前发现风险。

| 文章 | 故障场景 | 核心验证 |
|---|---|---|
| [CPU 打满故障演练](cpu-stress-test.md) | 对节点所有 CPU 核心施加满载压力 | Grafana 指标变化、Load Average 解读、Pod 是否受影响、告警是否触发 |
| [Pod OOM 故障模拟](pod-oom-test.md) | 创建持续申请内存的 Pod，触发 OOM Killer | OOMKilled 状态、Exit Code 137、CrashLoopBackOff 循环、Prometheus 提前预警 |

> 系列结论：CPU 打满 → 业务变慢但不挂；内存超限 → Pod 被内核直接杀死。资源限制不是可选项，是生产标配。

---

## 实验环境

所有实验基于以下环境完成：

| 组件 | 配置 |
|---|---|
| 集群架构 | 3 Master + 3 Worker + 2 LB（HAProxy + Keepalived） |
| K8s 版本 | v1.34.0 |
| 监控栈 | Prometheus + Grafana + Alertmanager |
| 虚拟化 | VMware vSphere |

---

## 内容计划

| 方向 | 规划内容 |
|---|---|
| K8s 网络 | Service 不通故障复现、CNI 插件异常、DNS 解析失败 |
| K8s 存储 | PV 挂载失败、存储容量耗尽、CSI 驱动异常 |
| K8s 调度 | 节点资源不足导致 Pod Pending、亲和性冲突 |
| 监控告警 | 告警风暴模拟、Alertmanager 路由验证 |
| 虚拟化 | vSAN 故障测试、存储恢复实验 |

---

## 实验原则

**1. 先建基线，再注入故障**

每次实验前，先记录集群的完整健康状态（节点 Ready、Pod Running、ETCD 健康、HAProxy 后端 UP）。没有基线，"正常"就缺乏说服力。

**2. 模拟真实故障，不要温和停止**

用 `shutdown -h now` 而不是 `systemctl stop kubelet`，用 vCenter 强制关机而不是优雅停止。生产环境的故障从来不优雅。

**3. 观察比操作更重要**

故障注入后，不要急着恢复。观察 kubectl 响应、Pod 状态、监控指标、ETCD 健康——这些数据才是实验的真正价值。

**4. 记录恢复过程**

故障能复现是第一步，能恢复才是完整实验。记录每一步恢复操作和对应的系统反应，形成"故障 → 影响 → 恢复"的完整闭环。
