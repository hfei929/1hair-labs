---
title: Rook Ceph OSD 故障恢复实测：600 秒 auto-out、1 分钟回填与零回迁
description: Kubernetes 1.36.1 + Rook 1.18.1 + Ceph 19.2.3 的 9 OSD 集群实测单盘故障注入：mon 静坐 600 秒（mon_osd_down_out_interval）后 auto-out，backfill 不足 1 分钟补齐 33 个 PG；复活时 AUTOOUT 位与 old_weight 备份让 OSD 25 秒回 in、零回迁；并解析 ceph_osd_in 序列消失（absent≠0）的告警盲区。
keywords:
  - Ceph OSD 故障恢复
  - Rook Ceph
  - Ceph auto-out
  - mon_osd_down_out_interval
  - PG backfill
  - Ceph OSD reweight
  - ceph_osd_in 序列消失
  - Prometheus 告警规则
tags:
  - Ceph
  - Rook
  - Kubernetes
  - Prometheus
  - 存储
  - 故障排查
---

!!! abstract "实测声明"

    本文所有命令与输出均来自真实集群实测（非预测、非模拟）：

    - **时间**：2026-11-08 20:00 ~ 2026-11-09 14:15
    - **集群**：K8s 1.36.1，3 master + 3 worker（Debian 13）
    - **存储栈**：rook v1.18.1 + ceph v19.2.3 + cephcsi v3.14.0，manifest 直装
    - **Ceph 拓扑**：9 OSD（每 worker 3×50G），3 mon 钉在 master，size=3，33 PG
    - **数据规模**：RBD 池 1.31k objects / 5.0 GiB（L2 实验灌入）
    - 数据块均逐字复制自终端落盘文件（`~/ceph-l0/`）

---

# 杀一块 Ceph OSD：600 秒静坐、1 分钟搬家、0 字节回迁

## 三个数字开头

先说结论，三个数字：

1. **600 秒**——杀掉一块 OSD 后，集群安静地等了整整 600 秒才开始干活。不是卡住了，是在等一个定时器。
2. **不到 1 分钟**——定时器到点后，1.9G 副本全部搬家完毕，33 个 PG 全部回到 clean。静坐 9 分半，干活半分钟。
3. **0 字节**——4 小时后把这块盘插回来，集群 25 秒内把它重新纳入编制，reweight 恢复 1.0，而数据搬运量是零。

第三个数字是这次实验最大的意外。我原本以为复活会触发第二轮 backfill（数据回流至少要再搬一遍），实际是：**数据从未离开那块盘，回家不用搬家**。

这是"生产化改造"第三战役（存储）的收官实验：在跑着真实应用的 Rook/Ceph 集群里，完整走一遍 OSD 的死亡与复活，全程有 [Prometheus](../observability/prometheus.md) 历史曲线兜底——**先接线，再杀盘**。

## 动刀之前先接线

实验顺序是这次最值的决策。杀盘过程只有十几分钟，如果中间态没抓到，事后想复盘就只能重来；而 Prometheus 的历史曲线不会漏——前提是杀盘之前指标已经在进库。

而"指标进库"这件事本身，折腾了一个晚上。起点是我想确认 [Grafana](grafana-first-open-blind-spot.md) 能不能看 Ceph，结果从 CRD 开关一路拆到 ServiceMonitor 抓取链，共四把锁、四次翻车：

```mermaid
flowchart TD
    Q["起点<br/>Grafana 能看 Ceph 吗"] --> L1["锁一 CRD 开关<br/>monitoring enabled"]
    L1 -->|"patch 被 CRD 拒"| F1["翻车一<br/>strategic merge 不收<br/>必须显式 --type=merge"]
    F1 --> L2["锁二<br/>ServiceMonitor 建不出来"]
    L2 -->|"operator 日志 forbidden"| F2["翻车二<br/>缺独立 RBAC 清单<br/>rbac.yaml 第一对补上"]
    F2 --> L3["锁三<br/>annotate nudge 哑火"]
    L3 -->|"operator 零动作"| F3["翻车三<br/>watch 谓词不认 annotate<br/>重启 operator 裁决"]
    F3 --> L4["锁四<br/>Prometheus targets 空"]
    L4 -->|"检查太早 仅 28 秒"| F4["翻车四<br/>operator 重载+抓取没跟上<br/>9 分钟后全绿"]
    F4 --> OK["四锁全通<br/>Ceph 指标进 Prometheus"]
    OK --> KILL["可以安心杀盘了"]

    classDef start fill:#DBEAFE,stroke:#2563EB,color:#0f172a
    classDef lock fill:#EDE9FE,stroke:#7C3AED,color:#0f172a
    classDef fail fill:#FEF3C7,stroke:#D97706,color:#0f172a
    classDef pass fill:#D1FAE5,stroke:#059669,color:#0f172a
    class Q start
    class L1,L2,L3,L4 lock
    class F1,F2,F3,F4 fail
    class OK,KILL pass
```

四把锁的细节每一条都值得单独写，这里只讲对杀盘实验最关键的两条经验：

**第一，CRD 上的 patch 永远显式 `--type=merge`。** 给 CephCluster 开 `monitoring.enabled` 时，不带 `--type` 的 patch 走 strategic merge，而 CRD 不支持这个策略，整块拒收。CRD 家族的坑在这之前已经踩过三回（apiVersion 的组、字段位置、patch 类型），这是第四回。

**第二，annotate 不触发 operator 的 reconcile。** 想让 operator 重读配置，往 CR 上打时间戳 annotation 是无效动作——operator 的 watch 谓词按 `generation` 过滤，annotation 不动 generation。裁决手段是重启 operator pod：无状态、启动即全量 reconcile、数据面零波及。

!!! tip "接线完成态"

    最终抓取链：`rook-ceph-mgr`（instance `192.168.114.148:9283`）+ 全节点 ceph-exporter DaemonSet，`ceph_health_status` 等指标 15s 进一次 Prometheus。顺带被数据打脸的一课：**`ceph_health_status` 里 0 才是 HEALTH_OK**——我预注册时写的是"1=OK"，Ceph 的枚举是 `HEALTH_OK=0 / WARN=1 / ERR=2`，跟 Linux 惯例正好相反。

还有一个当时差点误判的细节：打完 ServiceMonitor 标签后 28 秒去查 targets，空的——**不是没接上，是查得太早**。operator 重载配置、Prometheus 发现并开始抓取，整条链要几十秒。9 分钟后再查全绿。顺带一提，[监控首日那 9 个红 target](k8s-monitoring-red-from-day-one.md) 是同一道题的另一面：那边是真没接上，这边是接上了、抓取还没跑起来。慢故障实验的第一课在杀盘之前就来了：**时序敏感的检查，要么等够时间，要么事后回放历史**。

## 杀掉 osd.2

选 osd.2 不是随机的：它是 worker03 的第一块盘，上面落着全集群 33 个 PG 里的 12 个。数学先算好，动手才有底：

```text
33 PG × 3 副本 = 99 份副本
每块盘的期望份额 = 99 / 9 = 11 份
CRUSH 不是完美均匀 → 12 份，正常散布
每份约 4MB → osd.2 上约 1.9G 数据
```

预注册写在杀盘之前：**degraded PG 数 10-12 个；RBD 应用全程无感；auto-out 在 600 秒左右触发**。前两条命中，第三条精确命中——但"operator 会把 deployment 副本拉回 1"这条押错了，后面细说。

动手方式是最温和的故障注入——不删盘、不擦数据，只把 OSD pod 缩到零：

```bash
# T0 = 01:22:17Z
kubectl -n rook-ceph scale deploy rook-ceph-osd-2 --replicas=0
```

25 秒后（定点采样，`l3c-kill-osd2.txt` 逐字）：

```text
2026-11-09T01:22:17Z
  cluster:
    id:     a9a364ff-9398-48e2-9b92-b6afd368616f
    health: HEALTH_WARN
            1 osds down
            Degraded data redundancy: 493/3918 objects degraded (12.583%), 12 pgs degraded

  services:
    mon: 3 daemons, quorum b,a,c (age 2d)
    mgr: a(active, since 34h)
    osd: 9 osds: 8 up (since 25s), 9 in (since 34h)

  data:
    pools:   2 pools, 33 pgs
    objects: 1.31k objects, 5.0 GiB
    usage:   15 GiB used, 435 GiB / 450 GiB avail
    pgs:     493/3918 objects degraded (12.583%)
             21 active+clean
             12 active+undersized+degraded
```

这 25 秒读出三层信息：**down 已经检出**（`8 up`）；**但还在编制里**（`9 in`——注意是 9 不是 8，说明 CRUSH 拓扑没动）；**12 个 PG 立刻降级**（`active+undersized+degraded`——PG 还活着，只是少了一份副本）。预注册的 10-12 命中上沿。

一个值得注意的细节：down 检出这么快（秒级），是因为 scale-0 走的是 SIGTERM 干净退出，OSD 关停时会主动跟 mon 告别；如果是拔电/断网类的硬故障，就得等 peer 心跳超时（grace 约 20 秒）才轮得到 mon 标 down。两条路殊途同归，只是 down 的消息来得快慢不同。

## 九分半的静坐

接下来发生的事，是这次实验最反直觉的部分——**什么都没发生**。

从 01:23:00 到 01:32:30，Prometheus 的 `ceph_pg_degraded` 曲线是一条笔直的平台：

```text
时间(UTC)     pg_degraded   health_status   事件
01:22:00        0              0            kill 前最后采样
01:23:00       12              1            WARN，kill 后首个采样点
01:23:30       12              1            │
01:24:00       12              1            │
   ...          ...           ...           │ 静坐 9.5 分钟，曲线纹丝不动
01:32:00       12              1            │
01:32:30       12              1            ┘
~01:32:36     （auto-out 触发）
01:33:00        2              1            out 后 ~24s，10/12 PG 已回满
01:33:30        0              0            HEALTH_OK，搬家结束
```

（数据来自 `ceph_pg_degraded` 与 `ceph_health_status` 的 30s step 历史回放）

!!! note "down ≠ out"

    OSD 挂掉（down）和 OSD 被移出集群（out）是两个独立的事件。down 只意味着"这块盘失联了"；CRUSH 的拓扑没变，PG 的副本位置没有重算，**集群不搬任何数据**。为什么？因为搬数据很贵——静坐期间集群在赌这块盘会自己回来。生产上瞬态故障（内核 panic 后重启、宿主机维护、网络抖动）占大头，为每次失联都搬一遍数据会把集群自己的 IO 打爆。

    等待的价码是一个定时器：`mon_osd_down_out_interval`，默认 **10 分钟**（600 秒）。600 秒内盘回来了，什么都没发生过；600 秒没回来，mon 才认为它真死了，标记 out，触发重新布局。

这个设计哲学翻译成人话：**等 600 秒的成本是零，搬 1.9G 数据的成本是真实的 IO——先用便宜的，再用贵的**。

## 六百秒整：auto-out 的源码

实测的 auto-out 触发时刻可以从两个独立证据反推，互相印证：

- `ceph osd stat` 显示 `8 in (since 2m)`，采样时刻 01:34:36，反推 out ≈ 01:32:36
- `ceph_osd_in{osd="2"}` 指标序列的终止点在 01:32:00-01:33:00 采样之间

kill 在 01:22:17，down 在 25 秒内已检出（干净退出，OSD 主动上报），600 秒定时器从 down 时刻起算，到期约 01:32:20-40，实测 out 落在 01:32:36——**定时器如期而至**（`since 2m` 的读数分辨率是 ±1 分钟，out 的真实时刻落在分辨率带内，与定时器完全相容）。

顺带一个容易漏掉的容量侧证据：基线 `ceph -s` 显示 `435 GiB / 450 GiB avail`（9 盘口径），终局变成 `385 GiB / 400 GiB avail`——osd.2 被 out 后，集群总容量当场从 450 掉到 400。REWEIGHT 0 不只是"不再写入"，是这块盘的 50G 从账上整个划掉了。

拉 v19.2.3 源码看这 600 秒里 mon 到底做了什么（`src/mon/OSDMonitor.cc`，tick 内 `down_pending_out` 扫描）：

![六百秒整：auto-out 的源码](ceph-osd-600s-sit-1min-move-0bytes-back.assets/210417.png)

```cpp
// OSDMonitor.cc L5204-5226（节选，v19.2.3）
if (osdmap.is_down(o) && osdmap.is_in(o) && can_mark_out(o)) {
  utime_t orig_grace(g_conf()->mon_osd_down_out_interval, 0);  // 默认 10_min
  // ... 定时器未到，跳过 ...
  pending_inc.new_weight[o] = CEPH_OSD_OUT;              // L5211 权重归零
  pending_inc.new_state[o] |= CEPH_OSD_AUTOOUT;          // L5216 打 AUTOOUT 位
  pending_inc.new_xinfo[o].old_weight =
      osdmap.osd_weight[o];                              // L5219-21 备份原权重
  mon.clog->info() << "Marking osd." << o << " out (has been down for "
                   << int(down.sec()) << " seconds)";
}
```

三件事，每一件都有后文：

1. **权重归零**——这就是 `ceph osd tree` 里看到的 REWEIGHT 0，CRUSH 从此不再把数据映射到这块盘；
2. **打 AUTOOUT 位**——一个"这是 mon 自动标的 out"的身份标记，与手动 `ceph osd out` 的关键区别就在这一位，第九章会用到；
3. **备份原权重到 xinfo.old_weight**——为复活时的自动恢复埋的伏笔。

还有两道多数人不知道的保险（同样在源码里）：

```yaml
# src/common/options/mon.yaml.in（v19.2.3，节选）
- name: mon_osd_down_out_subtree_limit
  default: rack      # 整个 subtree 全 down 时不自动 out——默认 rack 级
- name: mon_osd_min_in_ratio
  default: 0.75      # in 的 OSD 比例低于 75% 时停止自动 out
```

subtree 保险的语义：如果整个 rack 的 OSD 同时 down，那多半是机架级网络/电源故障，盘大概率还活着，此时**重置定时器、不搬数据**。注意默认值是 `rack` 而不是 `host`——**单台 worker 三块盘全死，600 秒后照常 auto-out**，只有整机架故障才停手。min_in_ratio 则是雪崩闸：in 的盘已经少于 75% 时再 out 只会加速崩盘，mon 拒绝执行。

## 不到一分钟的搬家

auto-out 落地的瞬间，静坐结束，backfill 开始。493 份副本（12 个 PG × 平均 41 份）从其余 8 块盘的现有副本复制到 CRUSH 新算出的位置——实测**不足 1 分钟全部完成**：

```text
~01:32:36  auto-out，CRUSH 重算，12 个 PG 进入 backfill
01:33:00   degraded 12 → 2（out 后 ~24 秒，10/12 PG 已回满）
01:33:30   degraded 0，33 个 PG 全部 active+clean，HEALTH_OK
```

我实验前预期"小时级"。翻车原因很简单，也很重要：**heal 时间与数据量成正比**。1.9G 副本在本地虚拟盘上搬完只要几十秒；生产集群单盘 4T、数据 80% 满，同样的流程要搬 3T+，时间放大三个数量级。"小时级"是 TB 盘的口径，我的 5G 家底把这道除法算成了分钟级。

对实验设计本身还有一个教训：01:23:00 到 01:33:30 之间我们只有 30 秒粒度的 Prometheus 曲线，backfill 的中间态（`active+remapped+backfilling`）在终端上一眼都没见过——**关键时刻窗内要用 15-30 秒间隔轮询**。好在曲线数据一分不丢，这就是先接线的回报。

auto-out 后 12 分钟的终局采样，逐字复制：

```text
2026-11-09T01:34:36Z
  cluster:
    id:     a9a364ff-9398-48e2-9b92-b6afd368616f
    health: HEALTH_OK

  services:
    mon: 3 daemons, quorum b,a,c (age 2d)
    mgr: a(active, since 34h)
    osd: 9 osds: 8 up (since 12m), 8 in (since 2m)

  data:
    pools:   2 pools, 33 pgs
    objects: 1.31k objects, 5.0 GiB
    usage:   15 GiB used, 385 GiB / 400 GiB avail
    pgs:     33 active+clean

9 osds: 8 up (since 12m), 8 in (since 2m); epoch: e110

 2    hdd  0.04880          osd.2        down         0  1.00000
```

（osd tree 最后一行：osd.2 状态 `down`、REWEIGHT 已归零、crush weight 仍是 1.0——**盘还在集群拓扑里，只是不再承载数据**）

全程时间线一张图收束：

```mermaid
timeline
    title 一块 OSD 的死亡与复活
    section 动刀
        T+0 : scale-0 杀掉 osd.2
    section 检出
        T+25秒内 : OSD 干净退出上报 mon
        T+25秒 : WARN + 12 个 PG degraded
    section 静坐
        静坐 9 分半 : down 但 in 集群按兵不动
        : degraded 曲线走平台
    section auto-out
        T+600秒 : mon 打 AUTOOUT 位 weight 归零
        : 原权重 1.0 已备份
    section 搬家
        T+660秒 : backfill 493 份副本约 1.9G
        : 33 个 PG 全部 active+clean
    section 复活
        T+4小时07分 : scale-1 复活 rollout 22 秒
        T+4小时07分25秒 : boot 认出 AUTOOUT 位 恢复权重 1.0
        : 零搬运 25 秒回满血
```

插曲：押错的预注册。我原以为 rook operator 会发现 osd-2 的 deployment 副本被改成 0，然后把它拉回 1——实测 12 分钟纹丝不动，operator 日志里 osd-2 零匹配。原因翻文档才知道：**手动 scale-0 恰好是 rook 官方移除 OSD 流程的第一步**，operator 尊重这个用户意图。分界线很清晰：CephCluster CR 归 operator 管，Deployment 副本数归用户管。

## 消失与复活：absent 不等于 0

杀盘全程里最值得单独立传的，是一条 Prometheus 序列的生与死。

复盘时我想画 `ceph_osd_in` 的曲线，验证 in 状态翻转的时刻。第一次查询用了我猜的 label（`osd="2"`）——空的。换成 `ceph_daemon="osd.2"` 再查，曲线出来了，但形态出乎意料：

```text
// l3d-osd2curve.txt，raw JSON 时间点换算成 UTC（30s step，区间 01:15:00-01:45:00）
ceph_osd_up{ceph_daemon="osd.2"}:
  01:15:00  1
  01:22:00  1        ← 最后一个健康样本
  01:23:00  0        ← kill 后首个采样点，up 线翻 0
    ...     0        ← 此后保持 0
  01:32:00  0        ← 序列最后一个样本，01:33:00 起（auto-out 后）序列终止

ceph_osd_in{ceph_daemon="osd.2"}:
  01:15:00  1
    ...     1        ← 全区间为 1，静坐 9 分半里 in 状态纹丝不动
  01:32:00  1        ← 序列最后一个样本；01:33:00 起序列不存在
```

up 线和 in 线的**终止是同一个时刻**——auto-out 之后，两条序列一起从指标宇宙里退场了。

in 线不是 1→0，是**整条序列消失了**。被 out 的 OSD 从 mgr 的指标输出里除名——查询侧看到的是"没有这个序列"，而不是"这个序列值为 0"。

这在 Prometheus 里是个经典陷阱：`absent` 和 `0` 是两回事。`sum(ceph_osd_in) == 8` 不代表集群只该有 8 块 in 的盘——它代表"当前存在于指标里的 in 盘恰好 8 块"，被除名的序列不参与任何聚合。如果告警规则写成 `ceph_osd_in{osd="2"} == 0`，**永远不会触发**，因为根本没有这条序列。

同一族的前科：[Mimir 迁移那次](mimir-from-zero.md)，pod 被删后 `up{job="..."}` 整组序列消失，`count(up)` 从 53 掉到 48——不是哪个 target 挂了，是它们从指标宇宙里退场了。Ceph 的 OSD 只是同一个故事的存储版。

而这条序列还有下半场——4 小时后 osd.2 复活，序列在 05:30:20 重新出现，首点即 1。一条序列，两段生命，中间 4 小时是空白。对监控的意义：**判断"东西还在不在"要警惕序列粒度**，用 `absent()` 函数或 `count()` 基线对比，不要对一条可能不存在的序列做等值断言。

## 老家家具一件没动

复活实验的设计很简单：把 deployment 缩回 1，看会发生什么。预注册了三个走向：A. 自动回 in，数据回流，第二轮 backfill；B. up 但停在 out，需要手动 `ceph osd in`；C. pod 起不来。经典口径（"out 的 OSD 重启后停在 out，要手动拉 in"）让我押了 B 侧。

实测走向 A，而且干脆到离谱——**rollout 22 秒，25 秒内 up + in + reweight 1.0，33 个 PG 全程 clean，全程 12×15s 采样没有捕捉到任何 degraded/remapped/backfilling**。

疑点随之而来：如果 1.9G 副本真的在复活后从其他盘搬回 osd.2，按上一轮的速度也要几十秒的 backfill 过程态；一点没看到，那数据到底回没回来？两条证据合围：

**证据一**，`ceph osd df`（复活次日 15:55 采集——距复活 34 小时后的稳态，逐字）：

```text
ID  CLASS  WEIGHT   REWEIGHT  SIZE     RAW USE  DATA     OMAP    META     AVAIL    %USE  VAR   PGS  STATUS
 1    hdd  0.04880   1.00000   50 GiB  1.7 GiB  1.7 GiB   5 KiB   49 MiB   48 GiB  3.44  1.00   10      up
 4    hdd  0.04880   1.00000   50 GiB  2.0 GiB  1.9 GiB   5 KiB   49 MiB   48 GiB  3.91  1.14   13      up
 6    hdd  0.04880   1.00000   50 GiB  1.5 GiB  1.4 GiB   5 KiB   49 MiB   49 GiB  2.98  0.87   10      up
 0    hdd  0.04880   1.00000   50 GiB  1.6 GiB  1.5 GiB   7 KiB   32 MiB   48 GiB  3.10  0.90   10      up
 3    hdd  0.04880   1.00000   50 GiB  2.4 GiB  2.4 GiB   7 KiB   32 MiB   48 GiB  4.82  1.40   15      up
 7    hdd  0.04880   1.00000   50 GiB  1.2 GiB  1.1 GiB   8 KiB   31 MiB   49 GiB  2.32  0.68    8      up
 2    hdd  0.04880   1.00000   50 GiB  1.9 GiB  1.9 GiB   8 KiB   32 MiB   48 GiB  3.86  1.12   12      up
 5    hdd  0.04880   1.00000   50 GiB  1.8 GiB  1.8 GiB   4 KiB   48 MiB   48 GiB  3.63  1.06   12      up
 8    hdd  0.04880   1.00000   50 GiB  1.4 GiB  1.4 GiB   5 KiB   49 MiB   49 GiB  2.82  0.82    9      up
                       TOTAL  450 GiB   15 GiB   15 GiB  60 KiB  370 MiB  435 GiB  3.43
MIN/MAX VAR: 0.68/1.40  STDDEV: 0.69
```

读数三层：**osd.2 扛着 12 个 PG、1.9 GiB DATA**——正是杀盘时它名下那 12 个 PG（CRUSH 确定性：同样的权重拓扑算出同样的映射）；**PGS 列合计 10+13+10+10+15+8+12+12+9 = 99 = 33 PG × 3 副本**，对账吻合；**TOTAL 15 GiB 与 `ceph -s` 的 `usage: 15 GiB used` 互证**（5G 数据 × 3 副本口径）。而且这是复活 34 小时后的快照——12 个 PG 稳稳留在 osd.2 上，零搬运不是瞬时侥幸，是稳态。数据在盘上。

**证据二**，10 秒粒度的 Prometheus 回放（05:29:40 ~ 05:33:00），`ceph_pg_degraded` 与 `ceph_pg_backfilling` **全窗口为零**。没有搬运发生。

两个事实放在一起，唯一自洽的解释：**数据从未离开 osd.2 的盘**。时间线是这样的：

1. auto-out 时，backfill 给那 12 个 PG 在其他盘上补了新副本——但 osd.2 盘上的**旧副本一个字节没被删**（pod 只是停了，盘没动）；
2. 复活后 reweight 回 1.0，CRUSH 用**同样的权重拓扑**重新计算——算出的映射与杀盘前完全一致，那 12 个 PG 的副本位置又轮回到 osd.2；
3. peering 时发现 osd.2 上的副本还在（只差 out 期间约 20MB 的增量写入，走 recovery 秒级补齐），直接采用。

打个比方：**集群替你把家搬了，你 4 小时后回来，发现老家的门没锁、家具一件没动，产权登记也恢复了——你什么都不用搬**。

"故障恢复 ≠ 数据搬运"——Ceph 的恢复是逻辑回归，副本在、校验通过，就不搬。这个行为对生产的含义：**重启 OSD pod 是个近乎零成本的操作**，只要盘和数据还在，回归的代价是秒级元数据操作，而不是数据面搬迁。

## reweight 谁改回去的：源码定案

复活后 reweight 从 0 自动回 1.0，这不符合"经典口径"。翻 v19.2.3 源码，在 OSD boot 的处理路径里找到了确切机制（`OSDMonitor.cc` `prepare_boot`）：

![reweight 谁改回去的：源码定案](ceph-osd-600s-sit-1min-move-0bytes-back.assets/211630.png)

```cpp
// OSDMonitor.cc L3732-3751（节选，v19.2.3）
// mark in?
if ((g_conf()->mon_osd_auto_mark_auto_out_in &&
     (oldstate & CEPH_OSD_AUTOOUT)) ||          // 只认 AUTOOUT 位
    (g_conf()->mon_osd_auto_mark_new_in && (oldstate & CEPH_OSD_NEW)) ||
    (g_conf()->mon_osd_auto_mark_in)) {
  if (can_mark_in(from)) {
    if (xi.old_weight > 0) {
      pending_inc.new_weight[from] = xi.old_weight;   // 恢复备份的原权重
      xi.old_weight = 0;
    } else {
      pending_inc.new_weight[from] = CEPH_OSD_IN;
    }
  }
}
```

与 auto-out 侧的三件事严丝合缝地对上：

| auto-out 时（L5204-5226） | 复活 boot 时（L3732-3751） |
|---|---|
| 打 AUTOOUT 位 | 条件 `oldstate & CEPH_OSD_AUTOOUT`——**只认这个位** |
| 备份 old_weight = 1.0 | `new_weight = xi.old_weight`——**恢复备份** |

开关本身：

![开关本身](ceph-osd-600s-sit-1min-move-0bytes-back.assets/211805.png)

```yaml
# src/common/options/mon.yaml.in L916-926（节选）
- name: mon_osd_auto_mark_auto_out_in
  type: bool
  default: true
  desc: mark any OSD that comes up that was automatically marked 'out' back 'in'
```

**默认开**。整条机制链定案：

- **mon 自动 out 的 OSD，重启后自动回 in 并恢复原权重**——实测（25 秒内 up+in+1.0）与源码（AUTOOUT 位 + old_weight 恢复）双证；
- **手动 `ceph osd out` 的 OSD，重启后停在 out**——手动路径不打 AUTOOUT 位，boot 的 mark in 条件不满足，必须 `ceph osd in` 手动拉回。

"经典口径"没有错，错的记忆是把它套在了 auto-out 上。两个"out"是不同的东西：一个是 mon 的观察性判断（可逆），一个是管理员的拓扑决策（不可逆，除非再手动改）。另外 `prepare_boot` 里还有一行 `down_pending_out.erase(from)`（L3655）——600 秒窗口**内**盘就回来的话，连 out 都不会发生，pending 直接撤销。瞬时故障的最优路径是什么都不做。

## 数据面视角：用户的十一分钟

控制面的风起云涌，最终要落到一个问题上：**用 RBD 卷的应用感知到了什么？**

答案是：什么都没感知到。`rbd-app` 是个跑在 default ns 的裸 pod，挂着 10Gi 的 RBD PVC（由 [Ceph CSI](../kubernetes/architecture/csi.md) 供给，`/dev/rbd0` 挂在 `/data`），整个杀盘-静坐-out-搬家-复活全程零重启（pod 的最近一次重启发生在杀盘前 31 分钟），复活后写路径实测正常：

```text
POD=rbd-app
Filesystem                Size      Used Available Use% Mounted on
/dev/rbd0                 9.8G      5.0G      4.8G  51% /data
MNT=/data
20+0 records in
20+0 records out
20971520 bytes (20.0MB) copied, 0.012449 seconds, 1.6GB/s
-rw-r--r--    1 root, root     20.0M Nov  9 01:58 /data/l3c-probe
```

为什么无感？RBD 的客户端（worker01 内核里的 rbd 模块）持有的是**到主副本 OSD 的连接**，而 primary OSD 挂掉时 PG 会把 primary 角色切到存活的副本——客户端重连新 primary，IO 短暂停顿后恢复，卷和文件系统从头到尾没变。对 pod 来说，世界始终是 `/dev/rbd0`，9.8G，装着 5G 数据。

!!! note "白捡的素材：sleep 3600 指纹"

    复盘时发现 rbd-app 有 13 次重启、约每小时一次，一度怀疑与实验有关。查 lastState 定案：

    ```text
    restarts=14
    lastState={"terminated":{...,"exitCode":0,"finishedAt":"2026-11-09T01:50:19Z","reason":"Completed","startedAt":"2026-11-09T00:50:19Z"}}
    ```

    startedAt 到 finishedAt **精确相差 3600 秒**，exitCode 0。再看 pod 定义：`command=["sh","-c","sleep 3600"]`——容器主进程就是个一小时的 sleep，睡满退出，restartPolicy: Always 把它拉起来再睡一小时。杀盘无关，纯属保活设计的指纹。顺带它还是个活样本：**容器每小时轮回一次，`/data` 的数据纹丝不动**——RBD 卷的生命周期比容器长，这是 [PVC 存在意义](../kubernetes/architecture/storage/pv-pvc-storageclass.md) 的最好注脚。

## 读者自查三件事

如果你的集群也跑着 Rook/Ceph，拿这三条命令做个体检：

```bash
# 1. auto-out 的定时器是多少？（默认 10 分钟，生产按维护节奏权衡）
kubectl -n rook-ceph exec $(kubectl -n rook-ceph get pod -l app=rook-ceph-tools -o name | head -1) -- \
  ceph config get mon mon_osd_down_out_interval

# 2. 雪崩闸在不在？in 比例低于多少 mon 会拒绝继续 auto-out
kubectl -n rook-ceph exec $(kubectl -n rook-ceph get pod -l app=rook-ceph-tools -o name | head -1) -- \
  ceph config get mon mon_osd_min_in_ratio

# 3. 你的告警规则里有没有对"可能不存在的序列"做等值断言？
#    ceph_osd_in{ceph_daemon="osd.X"} == 0 这类规则在 OSD 被 out 时是哑的，
#    应改用 count(ceph_osd_in) < <期望值> 或 absent() 形态
```

第三条展开一句：这次实验里 OSD 被 out 后序列直接消失，如果你的 OSD 掉线告警写成 `== 0`，它在你最需要它的时候沉默。**告警规则要为"序列不存在"的形态设计，而不是只为"值变化"设计**。具体写法可以对照 [Prometheus 的告警规则](../observability/prometheus.md) 一节；路由和噪音治理另见 [Alertmanager](../observability/alertmanager.md)。

## 附：预注册对账表

预注册 11 条，命中 5 条，翻车 6 条。翻车条目比命中的更有价值，全部如实记录：

| # | 预注册（杀盘/接线前写下） | 结果 | 复盘 |
|---|---|---|---|
| 1 | degraded PG 10-12 个 | ✅ 12 | 命中上沿 |
| 2 | rbd-app 全程无感 | ✅ | 零重启 + 写路径正常 |
| 3 | auto-out ~600s | ✅ 615s | `mon_osd_down_out_interval` 默认 10_min |
| 4 | operator 会把副本拉回 1 | ❌ | scale-0 是 rook 移除流程第一步，operator 尊重用户意图 |
| 5 | heal 预期"小时级" | ❌ <1 分钟 | heal 时间 ∝ 数据量；"小时级"是 TB 盘口径 |
| 6 | `ceph_health_status` 1=OK | ❌ 0=OK | Ceph 枚举 HEALTH_OK=0，与 Linux 惯例相反 |
| 7 | `ceph_osd_in` 会 1→0 | ❌ 序列消失 | absent≠0；被 out 的 OSD 从 mgr 指标除名 |
| 8 | kps nsSelector 未设（要补） | ❌ 已是 {} | 免了一道 helm 税；谁设的待考 |
| 9 | 复活押 B（停在 out 要手动 in） | ❌ 走向 A | auto-out 可逆是源码默认行为，经典口径说的是手动 out |
| 10 | rbd-app 重启=一次性命令退出循环 | ✅ | `sleep 3600`，精确 1h 指纹 |
| 11 | 指标 label 是 `osd="2"` | ❌ `ceph_daemon="osd.2"` | v19 mgr 指标用 ceph_daemon label |

预注册的意义不是猜对——是**把"我以为"钉在实验之前**，让实验有机会打脸。这轮打出来的四条（#4 #5 #7 #9）每一条都比猜对值钱：它们各自对应一个下次能直接复用的机制判断。

## 挂账与下一个问题

挂账预告：worker02 三块 OSD 在杀盘前夜的一次重启考古（待查）；Grafana Ceph 面板（2842/5336/5342）导入后的面板篇。

下一步的问题留给读者也留给我自己：**min_in_ratio 0.75 的雪崩闸，在 9 OSD 的集群上意味着什么？** 答案是 out 到第 3 块盘时闸门落下（6/9 = 0.667 < 0.75）——小集群的 auto-out 会在连环故障时提前"装死"。这个数字值得每个 9 盘以下的小集群管理员知道。

## 推荐阅读

- [Mimir 从零装机：114 天的 Prometheus 从来没有过硬盘](mimir-from-zero.md)：absent≠0 的第一案，序列随 Pod 删除整组消失的同源故事。
- [Prometheus 监控体系：架构、PromQL 与服务发现](../observability/prometheus.md)：补齐 ServiceMonitor、抓取链与告警规则的背景知识。
- [K8s 监控装了 98 天：9 个 Prometheus target 从第一天就是红的](k8s-monitoring-red-from-day-one.md)：target 变红的另一种排查方向——真没接上，而不是抓取还没跑起来。
- [PV、PVC、StorageClass：K8s 存储三个对象到底谁管谁](../kubernetes/architecture/storage/pv-pvc-storageclass.md)：理解 RBD 卷为何比容器活得久。
- [Kubernetes CSI 工作原理](../kubernetes/architecture/csi.md)：理解 Ceph CSI 如何把 RBD 卷供给到 Pod。
- [Grafana 第一次认真打开：盲区期间照样绿的 28 个仪表盘](grafana-first-open-blind-spot.md)：Ceph 面板装进来之前，先看那套仪表盘藏着多少盲区。
- [Lab 实验室](index.md)：故障演练与生产化改造各战役的索引页。
