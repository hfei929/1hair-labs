---
title: Kubernetes Loki 日志实战：Grafana Alloy 采集、LogQL 查询与 PVC 持久化
description: 在 Kubernetes 1.36.1 集群从零部署 Grafana Loki 与 Alloy，实测日志采集、LogQL 查询、ring 500 排错和 PVC 持久化。解析 detected_level 标签、StatefulSet 自动删除 PVC 风险，以及 Helm upgrade 的 NodePort 迁册与假掉线故障。
keywords:
  - Kubernetes Loki
  - Grafana Alloy 日志采集
  - LogQL 查询
  - Loki PVC 持久化
  - Kubernetes 集群日志
  - journald 容器日志
tags:
  - Loki
  - Grafana Alloy
  - Kubernetes
  - 可观测性
  - 日志管理
  - 故障排查
series: 测试集群生产化改造
series_order: 10
---

# Loki 从零装机：日志的三层记忆，和一把熟悉的新刀

> **实测声明**：本文所有命令与输出来自我的测试集群（3 master + 3 worker，K8s 1.36.1，Debian 13，Calico IPIP）。装机实验执行于 2026-10-13 13:38–16:35，复活赛与迁册实验执行于 2026-10-14 上午；Loki chart 7.3.0（镜像 3.6.11）、Alloy chart 1.13.1（v1.20.1）。文中源码引用均已对照对应 tag 逐行核实。输出除标注外未做任何改写。

本文记录在 Kubernetes 集群中从零部署 Grafana Loki 与 Grafana Alloy 的实测过程：从 journald 和容器日志的保留现状出发，手写 Alloy 采集管线、用 LogQL 查询日志，并排查 Loki ring 500、`detected_level` 查询误区、PVC 数据保留和 Helm upgrade 迁册。重点不只是“装起来”，而是确认日志从哪里来、能保留多久，以及哪些操作会让它再次消失。

## 我运维了 153 天，从来没有过日志系统

这句话写出来的时候我自己愣了一下，但它是事实：

```bash
$ kubectl get pods,sts,ds,svc,cm,pvc -A 2>&1 | grep -i -E 'loki|promtail|alloy' | tee 01-loki-remnants.txt
$ echo "匹配行数: $(grep -c . 01-loki-remnants.txt)"
匹配行数: 0  （0=零痕迹）
```

监控有了（Prometheus + Grafana），告警有了（飞书 + 邮件），etcd 备份有了。日志呢？靠三样东西撑着：

1. **journald**——每台节点自己的系统日志，有轮转，够不着容器
2. **/var/log/pods**——kubelet 替容器落盘的日志文件，轮转策略是 kubelet 配置说了算
3. **我自己的 `| tee` 习惯**——这个系列每篇文章的实验输出都靠人肉重定向落盘，说难听点，我才是这个集群最大的日志系统

第三条是自嘲，也是真话。从 [etcd 备份篇](etcd-backup-restore.md)到[告警通知实录](k8s-alerts-ignored-for-25-days.md)，每一篇的原始证据都在我主机的目录里，格式是 `NN-描述.txt`。如果哪天我的 WindTerm 会话日志丢了，这个集群的可观测性历史就少一半。

所以这一篇做两件事：先把"日志现状"审计清楚（集群 153 天，日志的记忆到底有多短），再从零装一套 Loki——选型决策本身是内容，不只是操作记录。

## 先审计：日志的三处栖息地现状

装机前，我对六台节点做了一轮只读勘查：

```bash
$ for h in master01 master02 master03 worker01 worker02 worker03; do
  ssh $h 'echo "-- journal 用量"; sudo journalctl --disk-usage; \
    echo "-- 最老 boot"; sudo journalctl --list-boots | head -2; \
    echo "-- /var/log/pods 存量"; sudo du -sh /var/log/pods; \
    echo "-- 24h 日志增量(MiB)"; sudo find /var/log/pods -name "*.log" -mmin -1440 -exec du -cm {} + | tail -1'
done | tee 05-node-log-reality.txt
```

六台节点的关键数字（原样摘录）：

| 节点 | journal 用量 | 最老 boot（CST） | /var/log/pods | 24h 增量 |
|---|---|---|---|---|
| master01 | 2.5G | 05-08 22:20 | 102M | 25 MiB |
| master02 | 365M | 05-08 22:20 | 46M | 18 MiB |
| master03 | 352.2M | 05-08 22:20 | 47M | 18 MiB |
| worker01 | 2.8G | 05-09 00:08 | 39M | 12 MiB |
| worker02 | 2.1G | 05-09 00:08 | 56M | 3 MiB |
| worker03 | 2.1G | 05-09 00:08 | 67M | 10 MiB |

两个发现。

**发现一：journald 的记忆比我以为的长。** 我的预感是"轮转早把集群生日（05-12）之前的日志吃干净了"，结果 `--list-boots` 显示三台 master 的最老 boot 条目停在 **05-08 22:20**——比集群生日还早四天，journald 意外地覆盖了集群的完整一生。看起来记忆没丢？

不过这里有第二个发现。

**发现二：同样是 master，journal 用量差了 7 倍。** master01 攒了 2.5G，master02 只有 365M。它们的负载量级完全不在一个档次吗？不是——真相藏在 boot ID 里。三台 master 的最老 boot 条目共享同一个 boot ID `f8647cf9...`，三台 worker 共享 `3a0e3f72...`。这是当年 vSphere 克隆的痕迹：master01 是模板本尊，master02/03 是**运行中被克隆出来的**——连 journald 的档案一起被复制了。所以 master02 的 365M 不是"少记了"，而是它自己出生那一刻起记的日志；master01 的 2.5G 里有一部分是模板机的遗产。

这意味着一个有点尴尬的结论：**我无法从 journald 的现状推断"被轮转吃掉了多少历史"**——克隆污染了基线。审计能确定的只有：最老的完整证据链从 05-08/05-09 开始，集群生日 05-12 的日志在 journal 里还活着。

至于 `/var/log/pods`，最老文件是 node-exporter 的 `0.log`，时间 **06-08 17:33**——正好是监控栈安装日。容器日志的"官方记忆"从监控栈才算起，之前的容器日志已经被 kubelet 的轮转收走了。

审计结论：三层记忆，每一层的起点都不一样，而且**没有任何一层是集中式的**。要查一个跨节点的问题，我得 ssh 六台机器各 grep 一遍。

## 四个选型决策（ADR）

这个系列的原则是"看得见配置才敢上生产"，所以选型决策本身值得写下来。四个：

**决策一：采集器不选 Promtail。** 这个决定不难，但理由值得记录。Promtail 已经官宣 EOL（2026-03-02），结论很明确：新装机不要再用它。替代品是 Alloy——Grafana 官方的下一代采集器，我选了 v1.20.1。看 chart 的更新频率也能感知社区的动向：

```bash
$ helm search repo grafana/loki --versions | head -4
NAME          CHART VERSION   APP VERSION   DESCRIPTION
grafana/loki  7.3.0           3.6.12        Helm chart for Grafana Enterprise Logs supporti...
grafana/loki  7.2.0           3.6.11        ...
grafana/loki  7.1.0           3.6.8         ...

$ helm search repo grafana/alloy --versions | head -4
NAME           CHART VERSION   APP VERSION   DESCRIPTION
grafana/alloy  1.13.1          v1.20.1       Grafana Alloy
grafana/alloy  1.13.0          v1.20.0       ...
```

Promtail 的 chart 还能搜到（6.17.1），但那是冻结的尸体，不是可选项。

**决策二：不用官方捆绑包，用裸 chart + 手写管线。** Loki 官方文档现在首推 `k8s-monitoring` 捆绑包——一个元 chart，把 alloy-logs、指标采集、一大堆默认配置全包进去。一键装好。但一键的结果是：日志从哪来、经过什么处理、发到哪里，全部藏在元 chart 的嵌套 values 里。这在测试集群上跑没问题，但这个系列要的是**知道自己装了什么**。所以：Loki 用官方 chart，Alloy 用官方 chart，中间的管线自己写。四行配置的事，自己写比解开捆绑包的层层默认值更省心。

**决策三：单副本。** Loki 的常规部署是读写分离多副本（distributor/ingester/querier 各自多实例），那是给有对象存储、有真实写入压力的场景准备的。我的测试集群没有对象存储，写入量是六台节点的系统日志，单副本（single binary）是诚实的起点。这个决策后面会坑我一下，见后文 ring 事故——但"被坑"本身也是单副本决策的一部分。

**决策四：存储用 NFS PVC。** [Grafana 实测篇](grafana-first-open-blind-spot.md)的教训前置：SQLite 长在 emptyDir 上，pod 删除即阵亡。Loki 的数据（WAL + 索引 + chunk）必须落在 PVC 上。集群里现成的存储是 NFS CSI（192.168.114.155，`/nfs/k8s`），容量 49G 用了 7%，给 Loki 分 30Gi 足够。

## 装机：顺利的部分和坑人的部分

### 顺利的部分

装机走的是标准流程，两个细节值得说。

一是**镜像断网**。`registry-1.docker.io` 在我的环境里全节点超时，这是老朋友了（[containerd 到 runc 的容器启动链路](../kubernetes/architecture/node/containerd-from-cri-to-runc.md)里也涉及镜像准备）。解法还是华为云源 + retag：从华为源 pull，`ctr -n k8s.io images tag` 回 docker.io 的名字，`IfNotPresent` 就能命中本地缓存。六台节点、双 tag、同 digest，一遍过。

二是 **PVC 计时**。helm install 后立刻 wait：

```bash
$ kubectl -n monitoring wait --for=jsonpath='{.status.phase}'=Bound pvc/storage-loki-0 --timeout=120s \
    && echo "PVC Bound 耗时: $(( $(date +%s) - t0 ))s"
persistentvolumeclaim/storage-loki-0 condition met
PVC Bound 耗时: 29s
```

29 秒看着不快，但这 29 秒里大头是 helm install 自己（NOTES 打印完 wait 才开跑，且立刻 met）——NFS CSI 的动态供给本身在 install 过程中就完成了。真正的计时课在[PVC 毫秒级时间线实测](../kubernetes/architecture/storage/pvc-timeline-ms-breakdown.md)里学过：**wait 口径含轮询间隔和前置耗时，对象时间戳才是事件本身的时刻**。

### 坑人的部分：ring 500，37 分钟

pod 那边按"一是"的流程处理完镜像（retag 后删 pod 重建，loki-0 2/2 Running），`/ready` 返回 200——但所有写请求（`/loki/api/v1/push`）全部 500。查日志，distributor 报 ring 里找不到足够的 ingester。

根因：**Loki 3.x 的 `replication_factor` 默认值是 3，且不随 deploymentMode 切换**。我用 `deploymentMode: SingleBinary` 装了单副本，但 `replication_factor` 还是 3——distributor 认为需要 3 个 ingester 副本才算"写安全"，ring 里永远只有 1 个。37 分钟拒写，直到我在 values 里显式加上：

```yaml
loki:
  commonConfig:
    replication_factor: 1
```

这个坑我复盘时在自己的流程表上记了一笔：**改部署模式时，把所有带"副本/份数"语义的默认值重查一遍**——它们不会跟着模式自动切换。chart 想当然给了分布式场景的默认值，单副本场景的人就得自己踩。

顺便：修复后删除 pod 重建，marker 入库成功。**Day0 = 2026-10-13T07:56:53Z**（UTC）——这是 Loki 记忆的起点，三层记忆里最短的一层，从这一秒开始。

还有一段插曲值得单独记下。ring 500 的 37 分钟里，**告警系统全程安静**。pod 2/2 Running、readinessProbe 打的是 `/ready` 返回 200，而 ring 只挡 `/loki/api/v1/*` 业务路径——探针证明进程活着，不等于服务能用。对比一下上一批 KubePodNotReady 告警的窗口（我这里留着三源证词：飞书通知截图、台账、Prometheus 序列逐秒对齐）：

```
KubePodNotReady + KubeStatefulSetReplicasMismatch: firing 05:57:31Z → resolved 06:24:31Z（28 个采样点）
ring 500 期间（37 分钟，直到 07:56:53Z 告终）：零告警
```

pod 卡 NotReady 时告警很吵，服务真坏了时告警在睡觉。这是比[Grafana 实测篇](grafana-first-open-blind-spot.md)里“下拉框少两行”更深一层的盲区实证：**探针路径和业务路径不是一条路**。

## Alloy 手写管线：四环解剖

采集侧的全部配置就这四环（alloy chart 的 `alloy.configMap.content`）：

```text
discovery.kubernetes → discovery.relabel → local.file_match → loki.source.file
                                                        ↓
                                          process (stage.cri) → loki.write
```

- `discovery.kubernetes`：问 API server 要全集群的 pod 清单
- `discovery.relabel`：把 pod 元数据做成标签（namespace/pod/container/node/...）
- `local.file_match`：每个容器匹配到 `/var/log/pods/.../*/*.log` 的文件路径
- `loki.source.file`（tail_from_end）+ `process`（CRI 日志格式解析）→ `loki.write`：追文件、拆 CRI 前缀、发给 Loki

六台节点各跑一个 alloy DaemonSet（tolerations 让它也上 master），从 apply 到六台全 Ready 用了 29 秒。

这套东西和 kube-prometheus-stack 的差别在哪？装 Prometheus 的时候，ServiceMonitor 怎么选目标、指标怎么打标签，chart 全替你写好了——好用，但不清楚。Alloy 这四环是我一行行写的，每个容器的日志**从哪个文件、带哪些标签、经过什么处理、发到哪**，全部在我眼皮底下。对一个要写"生产化改造"系列的人来说，这个差别就是文章的可信度。

Grafana 那边，datasource 靠的还是老熟人——sidecar 供给链（[Grafana 实测篇](grafana-first-open-blind-spot.md)讲过的 ConfigMap → sidecar → 文件机制）。我创建了一个带 `grafana_datasource: "1"` 标签的 ConfigMap，指到 `http://loki.monitoring.svc.cluster.local:3100`，sidecar 自动捡走，Grafana 的数据源列表从 2 变 3。跨组件复用，一行没多写。

## LogQL 第一课，和一分钟两条的心跳

数据通了，学三句查询。

**第一课：查行。** `{namespace="monitoring"}` 就是 LogQL 的 `SELECT *`。装好后第一眼看到的是监控栈自己的日志在刷屏——安装期自指：Loki 在收集监控栈的日志，监控栈的日志里又有 Loki 自己的告警心跳。

**第二课：数行。** `count_over_time({namespace="monitoring"}[1m])`，近 1 分钟 48 条。再配 `topk` 看 5 分钟窗口谁最吵：`loki 78、grafana 17、loki-sc-rules 10`——最吵的是 Loki 自己的 sidecar。`loki-sc-rules` 是什么？为什么它每 5 分钟打 10 条日志？

**第三课变成了源码考古。** `loki-sc-rules` 是 loki chart 塞进 loki-0 的一个 sidecar 容器，镜像是 kiwigrid/k8s-sidecar 2.5.0——和[Grafana 实测篇](grafana-first-open-blind-spot.md)里的两个 sidecar 是同一个项目，只是版本更老。它的工作是 watch 带 `loki_rule` 标签的 ConfigMap/Secret（ruler 规则的供给链，和 grafana_dashboard 一个模式）。它的 env 我用 jsonpath 拉出来对了一遍：

```
METHOD=WATCH  LABEL=loki_rule  RESOURCE=both  FOLDER=/rules
LOG_LEVEL=INFO  WATCH_SERVER_TIMEOUT=60  WATCH_CLIENT_TIMEOUT=60
```

每 5 分钟 10 条 = **每分钟 2 条**。[Grafana 实测篇](grafana-first-open-blind-spot.md)发现的机制（sidecar 2.7.3 的“心跳”其实是 watch 重连时重新初始化产生的日志）在这里应该原样复现——但我不想只凭“应该”，于是拉了 2.5.0 的源码来对：

- `src/resources.py` L359：`_watch_resource_iterator` 每轮循环第一行调 `_initialize_kubeclient_configuration()`
- `src/client.py` L32：`logger.info("Loading incluster config...")`

2.5.0 和 2.7.3 的这两段**逐行几乎一致**。然后是实测对账，近 10 分钟的原始日志：

```
01:52:11.209Z +0.003s  {"time": "2026-10-14T01:52:11.209505+00:00", "level": "INFO", ...
01:53:11.225Z +60.016s {"time": "2026-10-14T01:53:11.224906+00:00", "level": "INFO", ...
01:53:11.226Z +0.001s  {"time": "2026-10-14T01:53:11.225724+00:00", "level": "INFO", ...
```

日志成对出现，对内差 1-3 毫秒（两个线程：RESOURCE=both，ConfigMap 和 Secret 各一个 watcher），对间 60.01-60.02 秒（WATCH_SERVER_TIMEOUT=60，服务器到点礼貌断开）。10 分钟整 20 条，精确等于 2 条/分钟。

同一个数字，两种推导：[Grafana 实测篇](grafana-first-open-blind-spot.md)从日志现象推到源码，这篇从源码预测到日志实测。跨版本（2.5.0 vs 2.7.3）、跨组件（Grafana vs Loki）、同一机制、同一数字。这种闭环比任何“教程一致性声明”都有说服力。

## detected_level：看起来像标签的标签

查日志的时候，每条流都多了一个我没配置过的标签：

```
labels: {'app': 'loki', 'container': 'loki-sc-rules', 'detected_level': 'info', ...}
```

我没写任何 level 提取管线，它是哪来的？翻 Loki 3.6.11 源码，链条是这样的：

- `pkg/validation/limits.go` L318：`validation.discover-log-levels` **默认开启**——"Discover and add log levels during ingestion"
- `pkg/distributor/distributor.go` L667-671：每次 push，`fieldDetector.extractLogLevel()` 检测每行的级别，append 到 `entry.StructuredMetadata`
- `pkg/distributor/field_detection.go` L97-120：优先级是 流标签里已有 level 系字段 > 解析日志行本身（JSON 找 level 键 > logfmt > 纯文本启发式）
- `pkg/util/constants/levels.go`：`LevelLabel = "detected_level"`，值归一化成 trace/debug/info/warn/error/critical/fatal

也就是说，Loki 服务端在替我做 level 检测，存进 structured metadata。但 structured metadata **不进索引**——这是 Loki 的 cardinality 纪律：level 这种值域只有 8 个的字段，做索引标签太浪费。查询响应时它才被合并进返回的 labels，所以"看起来像标签"。

坑就在这。看两组实测对比（近 1 小时、同一批日志）：

```
管线形式  | detected_level="error"   →  2 行
选择器形式 {detected_level="error"}  →  0 行
```

第二条不是"没有 error 日志"，是**这个语法根本查不到它**——不是索引标签，不能当选择器。安静的零结果，比报错更危险：你会以为自己集群很干净。

顺带一个有意思的观察：alloy 在 master03 上的 stderr 流，detected_level=error——按行检测，同一个文件里混级别的行会被拆进多条流。grafana 主容器的近 1 小时里也有 1 条 error 流（和 info 流并存）。要把"看起来像标签"的东西当真过滤器用，管线语法是唯一的正道。

## 同一把刀，三种拧法

上一篇 Grafana 的核心剧情是那把刀：pod 删除 → emptyDir 清零 → SQLite 阵亡。这一篇的主悬案之一就是它：**同样的刀落在 Loki 身上会怎样？**

Loki 的部署形态是 StatefulSet + PVC（storage-loki-0，30Gi，NFS）。理论上 pod 删除不该伤到数据——理论上。

### 复活赛实测

删 pod 前先落盘基线：PVC uid、PV 名、marker（我在装机日写入的一行特殊日志，`job="loki-marker"`，作为"数据在场"的证人）。然后：

```
-- T0 删除时刻: 01:58:20.87（UTC）
pod "loki-0" deleted
-- 删除窗口 /ready: 000 000 000（三次拒连）
-- T1 Ready: 01:59:03.62
```

**T0 → Ready 42.75 秒。** 中间还有个细节：STS 控制器在 T0+1.3 秒就建出了新 pod 对象（creationTimestamp 01:58:22Z），剩下 41 秒全是容器启动。

幸存三证：

```
PVC storage-loki-0: Bound（AGE 20h，连续）
PV pvc-1a7b86c2-...: 全程未动
新 pod uid=c9488245...（≠ 旧 8eeae2e9...，pod 是新的）

marker 总行数: 2
  2026-10-13T08:33:39.000000Z  LOKI-DAY0-MARKER 2026-10-13 装机纪念日：三层记忆里最短的一层从这一秒开始
  2026-10-14T01:59:03.821725Z  LOKI-RESURRECTION-MARKER 刀落下后数据仍在
```

复活后立刻 push 的新 marker 也进去了——两行 marker 隔了 **17.4 小时**，在同一查询里同框。刀落了，数据在。`k delete pod` 对 STS+PVC 就是不疼：pod 是耗材，PVC 才是本体。

### 但这把刀还有第三种拧法

同刀不同命的关键在 chart 的一行默认值。loki chart（7.3.0）的 singleBinary STS 模板里有这么一段（L29-33）：

```yaml
{{- if and (semverCompare ">= 1.23-0" ...) (.Values.singleBinary.persistence.enableStatefulSetAutoDeletePVC) ... }}
  persistentVolumeClaimRetentionPolicy:
    whenDeleted: {{ .Values.singleBinary.persistence.whenDeleted }}
{{- end }}
```

注释原话："Data on the singleBinary nodes is easy to replace, so we want to always delete PVCs to make operation easier..."（singleBinary 的数据容易重建，所以干脆删 PVC 让运维省事）。chart 的 values 默认 `enableStatefulSetAutoDeletePVC: true`——**卸载 release 时，PVC 会被连带删除**。

真跑一遍的话链条是这样的：`helm uninstall` → STS 删除 → PVC 焚毁 → PV（RECLAIM POLICY=Delete）回收 → NFS 上的目录消失。同一个 `kubectl delete pod` 不疼的存储，`helm uninstall` 一句话就烧掉。运维"省事"和运维"失忆"，中间隔的就是一个默认值。我的 values 里显式反开了这个开关（`enableStatefulSetAutoDeletePVC: false`）。

### get sts 看不见的东西

这里翻了一个自己的车，翻出来一个更深的机制，值得写。

我预测：反开开关后，`kubectl get sts loki -o jsonpath='{.spec.persistentVolumeClaimRetentionPolicy}'` 应该输出空（chart 模板整块不渲染，字段缺失，走 K8s 默认 Retain）。实测：

```
STS retentionPolicy: [{"whenDeleted":"Retain","whenScaled":"Retain"}]
```

显式的 Retain。我的第一反应是"实装的 chart 版本和本地研究副本不一致"——查了，就是 7.3.0，模板确实没有 else 分支。真凶在 API server：**K8s 的 admission 默认值填充**。v1.36.1 源码 `pkg/apis/apps/v1/defaults.go` L127-135：

```go
if obj.Spec.PersistentVolumeClaimRetentionPolicy == nil {
    obj.Spec.PersistentVolumeClaimRetentionPolicy = &appsv1.StatefulSetPersistentVolumeClaimRetentionPolicy{}
}
if len(obj.Spec.PersistentVolumeClaimRetentionPolicy.WhenDeleted) == 0 {
    obj.Spec.PersistentVolumeClaimRetentionPolicy.WhenDeleted = appsv1.RetainPersistentVolumeClaimRetentionPolicyType
}
// whenScaled 同理
```

chart 没写，API server 替它填了。这带来一个审计上的微妙事实：**从 `get sts` 的输出，你分不清 Retain 是 chart 写的还是 API 填的**。反开生效的唯一证据在 values 文件里（`grep AutoDelete loki-values.yaml`）。"没写"不等于"没有"——默认值的世界里，沉默的配置项和显式的配置项长得一模一样。

三种拧法排一排，就是这一篇的存储课：

| 拧法 | 对象 | 结果 |
|---|---|---|
| `kubectl delete pod` | Deployment + emptyDir | Grafana 的 SQLite 阵亡（上一篇） |
| `kubectl delete pod` | STS + PVC | Loki 幸存（本篇，42.75s 复活） |
| `helm uninstall` | STS + PVC + AutoDeletePVC 默认开 | 卸载即焚毁（chart 默认，已反开） |

## 升级税，和一次假掉线事故

装机日之后的第二天，我给这套东西做了一次收尾改造：NodePort 的"迁册"。这个过程里翻了今天最大的一个车，值得完整记录。

### 背景：upgrade 税

装机当天为了从节点外访问 Loki，我 `kubectl patch` 把主 svc 改成了 NodePort 31000。这是"带外修改"——chart 不知道这件事。后续每次 `helm upgrade`，chart 按自己的模板重渲染，NodePort 就会被吃掉（回归 ClusterIP）。这就是"升级税"：带外的爽快，upgrade 时都要还。

审计时还发现一个更隐蔽的问题：当时 patch 只指定了 http 端口的 nodePort，但 `type: NodePort` 一改，**grpc 端口也被连带拽成了随机 NodePort**：

```
loki   NodePort   10.111.104.251   <none>   3100:31000/TCP,9095:30332/TCP
```

30332——一个我从没打算暴露的端口，就这么对外开了 20 个小时，没有任何人知道。带外 patch 的粗糙性，又一个实证。

解法是把 NodePort 迁回 chart 管辖：values 的 `extraObjects` 加一个独立的 `loki-np` Service（selector 指向 single-binary 组件标签），主 svc 回归纯 ClusterIP。以后 upgrade 随便跑，NodePort 是 chart 的一部分，不会再被吃。

### 事故：两次"SSH 掉线"

迁册的命令块发到我的终端里执行，跑到一半，SSH 掉了。重连、重跑，又掉了。

说实话，第一次掉线时我心里凉了一下——命令块里有 `helm upgrade`。第二次掉线后我停了下来，先做了一次纯只读的集群审计：

```
helm history → REVISION 仍 4（upgrade 没跑）
svc → 主 svc 仍 NodePort 31000（patch 没跑）
无 loki-np 对象
loki-0 uid=c9488245 未动、marker 2 行、/ready 200
```

**零损害。** 死在哪了？values 的追加段——那一段确实执行了（文件里多了 extraObjects 块）——之后的第一个验证命令：`diff loki-values.yaml.v5 loki-values.yaml`。

`diff` 的退出码语义：**有差异时返回 1**。而我的命令块开头有一行 `set -eo pipefail`——`-e` 把退出码 1 当成失败，直接杀掉了整个 shell。SSH 会话跟着关闭，看起来和断线一模一样。重跑时 python 断言（`assert 'extraObjects' not in c`）拦住了重复追加，退出码又是 1，shell 又"掉线"。

两次都是假掉线。真凶是我自己写的 `set -e`，它把"diff 发现了预期的差异"（验证成功的语义）当成了致命错误。

!!! warring "**交互式粘贴块里禁用**"
    `set -eo pipefail`. 守卫逻辑用显式的 `if ...; then echo STOP; exit 1; fi` 长在命令里，diff/grep 这类"退出码非零≠失败"的命令后面跟 `|| true`。高危操作要先设计"看起来像事故的失败"长什么样——否则守卫自己就会制造事故现场。

### 重跑：迁册完成

去掉 set -e、落盘文件换新号（尸检现场保留不覆盖）、双守卫复检后重跑：

```
GUARD-1 OK: alloy 不走 31000
GUARD-2 OK: extraObjects 恰 1 块
service/loki patched          ← 主 svc 降回 ClusterIP，两个端口的 nodePort 显式清空
Release "loki" has been upgraded. Happy Helming!   REVISION: 5
```

验证全景：

```
loki      ClusterIP   10.111.104.251   3100/TCP,9095/TCP
loki-np   NodePort    10.107.220.191   3100:31000/TCP

/ready 经 31000: try1 → 200（黑窗 <2 秒）
uid=c9488245-8ed8-40ee-a403-7a0edae78ce6 created=2026-10-14T01:58:22Z   ← 未变
marker 总行数: 2
alloy 近 2 分钟采集: 38 行
```

最喜欢的两行是 uid 和 created——**upgrade 前后逐字符不变**。整个迁册零停机：STS 模板输出没有任何变化，loki-0 根本不知道发生过 upgrade。预测时我还担心 chart 的 PVC 扩容重建钩子（`enableStatefulSetRecreationForSizeChange`）会不会惊动 pod——查了模板，那个钩子需要显式开启，默认 false，纯担心。

还有一个意外之喜：预测里给 NodePort 黑窗留了 10-40 秒的余量，实测 **try1 直接 200**。revert → upgrade → loki-np 创建 → kube-proxy 规则同步，整条链不到 2 秒——脚本连续执行的间隙，比人肉敲两条命令的间隙小一个量级。所谓黑窗，大头本来就是人。

焚毁链顺手查到了最后一环。loki 的 SC 是 `nfs-expand`（`nfs.csi.k8s.io`，支持扩容），PV 的 RECLAIM POLICY 是 Delete——而 SC 的 parameters 里只有 server 和 share，**没有任何归档/保留类参数**。也就是说 AutoDeletePVC 那条链如果真烧起来，NFS 侧的目录也不会有软着陆。这条链我只查到这（没舍得真测一遍——30G 数据烧了要重装），CSI 驱动删除 PV 时对 NFS 目录的精确行为，留给以后一次专门的实验。

## 读者自查三件事

如果你的集群也想上日志层，动手前先花五分钟自查：

```bash
# 1) journal 的家底（每个节点）
sudo journalctl --disk-usage
sudo journalctl --list-boots | head -3    # 顺手看 boot ID，克隆机集群会有惊喜

# 2) 容器日志的体量和增速（决定你的 PVC 要多大）
sudo du -sh /var/log/pods
sudo find /var/log/pods -name "*.log" -mmin -1440 -exec du -cm {} + | tail -1

# 3) 装之前有没有历史残留（有没有人装过 promtail 然后忘了）
kubectl get pods,ds,cm -A 2>&1 | grep -i -E 'loki|promtail|alloy'
```

以及三条本文用血换来的装机清单：

- `deploymentMode: SingleBinary` 时，显式写 `replication_factor: 1`——默认值 3 不随模式切换
- 显式写 `enableStatefulSetAutoDeletePVC: false`——除非你真的想要"卸载即焚"
- 所有对 svc 的带外 patch，尽快迁回 chart 管辖（extraObjects）——upgrade 税和随机 NodePort 暴露都是它的利息

## 唯一知道边界的一层

三层记忆的格局现在是：journald（审计时点往前 158 天，节点各自为政）、/var/log/pods（4 个月，kubelet 轮转说了算）、Loki（1 天，集中、可查、有 marker 记生日）。第三层最短，但只有它是按我的意志建的——Day0 那行 marker 我让它记的是"三层记忆里最短的一层从这一秒开始"，写完这篇想想，它同时也是唯一一层**我知道边界在哪**的记忆。

可观测性四件套的下一块拼图是 Mimir——Prometheus 的长期存储。指标和日志都齐了，就差“历史”这一课了。

## 推荐阅读

- [Grafana 第一次认真打开：盲区期间照样绿的 28 个仪表盘](grafana-first-open-blind-spot.md)：了解 Loki 数据源如何接入 Grafana，以及 emptyDir 对 SQLite 数据的影响。
- [Loki 日志聚合：架构、LogQL 与 Grafana 集成](../observability/loki.md)：补齐 Loki 架构、LogQL 和 Grafana 集成的基础概念。
- [K8s 监控装了 98 天：9 个 Prometheus target 从第一天就是红的](k8s-monitoring-red-from-day-one.md)：从采集目标与告警链路理解监控盲区。
- [Prometheus P99 实测：apiserver 延迟 60 秒整的背后](p99-apiserver-latency-60s.md)：延伸阅读指标侧的 Prometheus 排查实录。
- [K8s 存储毫秒级拆解：一个 PVC 的 563 毫秒全链路时间线](../kubernetes/architecture/storage/pvc-timeline-ms-breakdown.md)：了解 PVC 从创建到绑定、挂载的实际时间线。
