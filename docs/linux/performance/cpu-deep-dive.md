---
title: Linux CPU 使用率深度解析：Load Average、上下文切换与 Steal Time | 1Hair Labs
description: 深入讲解 Linux CPU 性能指标，涵盖 load average 的真相、CPU 状态分解（usr/sys/iowait/steal）、上下文切换的影响、中断处理与 CPU 亲和性、虚拟机 steal time 排查。
keywords:
  - Linux CPU
  - load average
  - 上下文切换
  - steal time
  - CPU亲和性
  - 中断
  - 性能分析
---

# Linux CPU 深度解析：Load Average、上下文切换与 Steal Time

## 前言

看到 `top` 里 CPU 100% 就喊「CPU 不够了」？看到 `load average` 50 就说「服务器要炸了」？很多对 CPU 性能的「直觉判断」其实是错的。

本文深入拆解 CPU 指标背后的真正含义，帮你建立正确的 CPU 性能分析框架。

---

## Load Average 的真相

### 它不是「CPU 使用率」

`load average` 是三个数字：

```bash
uptime
# 14:30:00 up 30 days, 1:23, 2 users, load average: 2.50, 1.80, 1.20
```

| 数字 | 含义 |
| :---: | --- |
| `2.50` | 过去 1 分钟的平均值 |
| `1.80` | 过去 5 分钟的平均值 |
| `1.20` | 过去 15 分钟的平均值 |

### Load Average 到底在算什么？

Load average 统计的是**两种状态的进程数量之和**：

| 状态 | 含义 | `ps` 标识 |
| --- | --- | :---: |
| **Running / Runnable** | 正在 CPU 上运行 OR 排队等待 CPU | `R` |
| **Uninterruptible Sleep** | 等待 I/O 完成（不可中断） | `D` |

!!! warning "关键认知"
    1. Load average 包含 **D 状态进程**。如果大量进程卡在磁盘 I/O（D 状态），Load 会飙得很高——但**不是 CPU 问题**，是磁盘问题！
    2. Load average 是**累加值**。4 核机器上 Load = 4 意味着 CPU 刚好满负荷。Load = 8 意味着有 4 个进程在排队。

```bash
# 查看系统 CPU 核心数
nproc

# 查看 D 状态进程（磁盘阻塞）
ps aux | awk '$8 ~ /D/'
```

### 判断标准

| Load 与核心数的关系 | 含义 |
| :---: | --- |
| **Load < 核心数 × 0.7** | 健康 |
| **Load ≈ 核心数** | CPU 接近饱和 |
| **Load > 核心数** | 有排队，需关注 |
| **Load >> 核心数** | 严重过载或 I/O 阻塞 |

---

## CPU 状态分解

```bash
mpstat 1
# CPU  %usr  %sys  %iowait  %irq  %soft  %steal  %guest  %idle
```

| 指标 | 含义 | 高占比说明 |
| --- | --- | --- |
| **`%usr`** | 用户态 CPU | 应用代码计算密集 |
| **`%sys`** | 内核态 CPU | 系统调用频繁、上下文切换多 |
| **`%iowait`** | 等待 I/O 的 CPU 空闲时间 | **磁盘是瓶颈**（CPU 在等磁盘） |
| **`%irq`** | 硬中断 | 网卡/磁盘中断密集 |
| **`%soft`** | 软中断 | 网络数据包处理（软中断） |
| **`%steal`** | 被 Hypervisor 偷走的时间 | **虚拟机资源被过度分配** |
| **`%idle`** | 真正空闲 | — |

!!! tip "%iowait 的误解"
    `%iowait` 高 ≠ CPU 忙。它的含义是：**CPU 空闲 + 有进程在等待 I/O**。如果只有一个核心在等 I/O，`%iowait` 可能显示很高，但实际上其他核心可能是空闲的。

---

## 上下文切换

每次 CPU 从一个进程/线程切换到另一个，都会产生开销：保存寄存器、切换页表、刷新 TLB。

```bash
vmstat 1
# r  b   swpd   free   buff   cache   si   so   bi   bo   in   cs
# 2  0      0  50000  10000  300000   0    0   50   20  500 3000
#                                          ↑ 中断     ↑ 上下文切换
```

| 字段 | 含义 |
| :---: | --- |
| `r` | Runnable 进程数（CPU 队列长度） |
| `b` | Uninterruptible Sleep 进程数 |
| `in` | 每秒中断次数 |
| `cs` | **每秒上下文切换次数** |

```bash
# 每个进程的上下文切换统计
pidstat -w 1
# cswch/s: 自愿切换（等待 I/O、锁）
# nvcswch/s: 非自愿切换（时间片用完）
```

**判断标准**：

| cs/s | 程度 |
| :---: | --- |
| < 10,000 | 正常 |
| 10,000 ~ 50,000 | 需关注 |
| > 50,000 | 可能是问题 |

过高的上下文切换通常意味着：线程过多、锁竞争严重、或任务粒度过细。

---

## 中断与软中断

```bash
# 查看中断分布
cat /proc/interrupts

# 查看软中断
cat /proc/softirqs
```

网卡收包会触发硬中断 → 内核将数据处理交给软中断（`ksoftirqd`） → 大量网络流量会导致 `%soft` 上升。

优化方向：网卡多队列（RSS）、中断亲和性（`/proc/irq/N/smp_affinity`）。

---

## CPU 亲和性与绑核

```bash
# 查看进程当前绑定在哪些核心上
taskset -cp <PID>

# 将进程绑定到 CPU 0,2
taskset -cp 0,2 <PID>

# 启动时绑核
taskset -c 0,2 ./my_app
```

绑核的好处：减少 CPU 缓存失效（cache miss），提升性能。代价：降低调度灵活性。

---

## 虚拟机 Steal Time

`%steal` 是虚拟化环境中特有的指标——Hypervisor 从 VM 偷走的 CPU 时间：

```bash
top
# %Cpu(s): 10.0 us, 5.0 sy, 0.0 ni, 60.0 id, 0.0 wa, 0.0 hi, 5.0 si, 20.0 st
#                                                                        ↑ steal
```

| %steal | 含义 |
| :---: | --- |
| **0 ~ 5%** | 正常 |
| **5 ~ 10%** | 宿主机负载偏高 |
| **> 10%** | 宿主机严重过载、CPU 超分配、或 NUMA 不平衡 |

**排查**：
1. 检查宿主机是否有其他 VM 在争抢 CPU
2. 检查是否启用了 CPU 热插拔导致 vCPU 迁移
3. 检查 NUMA 拓扑是否与 vCPU 分配匹配

---

## perf：CPU 性能分析利器

```bash
# 实时统计系统调用和事件
sudo perf top

# 对指定进程采样 30 秒
sudo perf record -p <PID> -g -- sleep 30
sudo perf report

# 统计指定进程的 CPU 事件
sudo perf stat -p <PID> sleep 10
```

---

## 总结

CPU 性能分析的关键认知：

1. **Load average ≠ CPU 使用率**——它包含 D 状态进程，高 Load 可能是磁盘问题
2. **%iowait 高 ≠ CPU 忙**——CPU 在空闲等磁盘，瓶颈在存储
3. **上下文切换**：> 50,000/s 需要关注，可能是线程过多或锁竞争
4. **%steal > 10%**：虚拟机资源被偷，宿主机过载
5. **perf 是终极武器**：当常规工具查不出问题，用 perf 看 CPU 到底在忙什么

CPU 不是最快的资源就是最慢的资源——取决于你的负载。理解每个指标的含义，才能在问题出现时一眼看穿本质。 🚀
