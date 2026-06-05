# Linux 系统性能优化：知其然，更知其所以然

!!! note "抛砖引玉"
    系统性能优化需要对操作系统内核、硬件体系结构以及业务负载特征有相当深入的理解，同时依赖大量实际生产环境的经验积累。笔者也远非无所不知，本文仅基于有限的项目实践和知识梳理，分享一些相对安全、经过验证的优化思路和方法。**请读者以批判性眼光参考，并始终在生产环境前进行充分测试**。文中的不足之处，欢迎指正与探讨。

性能优化是 Linux 运维领域最考验功力的环节。它需要你**洞悉系统各组件之间的耦合关系**，而不是盲目套用“优化脚本”。本文不提供玄学般的“一键优化”，而是从 **CPU、内存、磁盘、网络** 四个维度，讲解参数调优的**原理、适用场景和风险**，帮助你建立属于自己的优化思维框架。

!!! tip "欲穷千里目，更上一层楼"
    性能优化的前提是**准确测量**。在没有监控数据的情况下谈优化，犹如盲人摸象。请务必先阅读本系列的《系统监控》一文，拿到基线数据后，再回来讨论优化。

## 一、性能优化的核心原则

### 1. 优化必须有的放矢

性能瓶颈通常只有一个（或少数几个）。你需要用监控工具找到真正的瓶颈——是 CPU 不足？内存泄漏？磁盘 I/O 饱和？还是网络延迟？**不要凭感觉优化**。

### 2. 权衡与取舍

- **内存换 CPU**：例如增大缓存、预读
- **CPU 换 I/O**：例如压缩数据、启用加密
- **延迟换吞吐**：例如合并写入、批量处理

### 3. 优化要有可回滚方案

修改内核参数前，记录原始值。使用 `sysctl -a > sysctl.before` 备份。**永远在测试环境验证**。

!!! tip "磨刀不误砍柴工"
    我曾见过有人直接在生产环境执行 `echo 1 > /proc/sys/vm/drop_caches` 来“释放内存”，结果导致应用响应骤降——因为热点数据被清出了缓存。所以，理解每个参数的含义比知道命令更重要。

---

## 二、CPU 性能优化

### 2.1 关键指标回顾

- **`%usr`**：用户态 CPU 占比。过高说明应用计算密集。
- **`%sys`**：内核态占比。过高可能是系统调用频繁、上下文切换过多。
- **`%iowait`**：等待 I/O 的 CPU 时间。过高表示磁盘是瓶颈。
- **`%irq` / `%softirq`**：硬/软中断。过高通常与网卡或磁盘驱动相关。
- **`load average`**：运行队列长度 + 不可中断进程数。超过核心数*0.7 需关注。

### 2.2 常见优化手段

#### (1) 进程调度策略

Linux 默认调度器是 `CFS`（完全公平调度）。对于交互式或延迟敏感的应用，可以调整 `nice` 值或调度策略。

```bash
# 降低进程优先级（nice 值越高优先级越低）
nice -n 19 ./cpu_intensive_job

# 改变已运行进程的优先级
renice -n -5 -p 1234   # 提高优先级（需要 root）

# 设置实时调度策略（谨慎使用，可能饿死其他进程）
chrt -f -p 10 1234     # FIFO 调度，优先级 10
```

#### (2) CPU 亲和性（绑核）

将关键进程绑定到特定 CPU 核心，避免缓存失效和迁移开销。

```bash
# 启动时绑定 CPU 0,2
taskset -c 0,2 ./my_app

# 对已有进程绑定
taskset -cp 0,2 1234
```

#### (3) 内核参数调优

```bash
# /etc/sysctl.conf 或 /etc/sysctl.d/99-performance.conf

# 减少时钟中断对 CPU 的扰动（适用于虚拟机或专用服务器）
kernel.hz = 100

# 允许更频繁的进程迁移（多核负载均衡）
kernel.sched_migration_cost_ns = 500000

# 增大默认时间片（减少抢占，适合批处理）
kernel.sched_min_granularity_ns = 10000000
```

!!! tip "牵一发而动全身"
    实时调度策略（`SCHED_FIFO`/`SCHED_RR`）能让你的程序几乎独占 CPU，但**很容易导致系统无响应**——比如键盘鼠标的驱动也是普通进程。生产环境使用实时调度前，务必在测试中模拟极端情况。另外，绑核虽然提高了缓存命中率，但也可能造成核心闲置而其他核心过载，需要结合负载特征决定。

---

## 三、内存性能优化

### 3.1 关键指标

- **`MemAvailable`**：真实可用内存（含可回收缓存）
- **`Swap used`**：已用交换空间。非零不一定有问题，持续增长才有风险。
- **`OOM Killer` 触发**：内存完全耗尽时的应急机制，触发时系统日志必有记录。

### 3.2 常见优化手段

#### (1) 调整缓存与回收行为

```bash
# 查看当前脏页比例
sysctl vm.dirty_ratio                # 默认 20%
sysctl vm.dirty_background_ratio     # 默认 10%

# 调低脏页比例，让内存更早刷盘（降低内存压力，但 I/O 增加）
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5

# 增大脏页超时时间（允许更多脏页积累，适合写多读少的场景）
vm.dirty_expire_centisecs = 6000     # 60 秒
```

#### (2) 透明大页（THP）管理

THP 可以降低 TLB 缺页开销，但对某些数据库（如 MySQL、MongoDB）反而导致延迟抖动。

```bash
# 查看状态
cat /sys/kernel/mm/transparent_hugepage/enabled

# 关闭 THP（推荐数据库场景）
echo never > /sys/kernel/mm/transparent_hugepage/enabled
# 永久配置：在 /etc/rc.local 或 systemd 服务中加入
```

#### (3) 限制进程内存（cgroups）

使用 `systemd` 或 `cgexec` 限制进程的内存使用，防止某个程序耗尽系统内存。

```bash
# 使用 systemd 服务限制内存
# 在服务单元文件中加入：
[Service]
MemoryMax=2G
MemoryHigh=1.8G
```

#### (4) 调整 OOM 评分

进程的 `/proc/<pid>/oom_score_adj` 值范围 -1000 到 1000。值越高，越容易被 OOM Killer 选中。

```bash
# 保护关键进程（SSH、数据库）
echo -500 > /proc/1234/oom_score_adj
```

!!! tip "他山之石，可以攻玉"
    很多数据库官方文档都会建议**关闭 THP**、**设置 vm.swappiness=1**（避免主动换页）。但不要全盘照抄。比如 `vm.swappiness` 默认 60，若你的内存充足且应用冷数据多，调低到 10 即可；若内存紧张且磁盘极快（NVMe），甚至可以保持默认。我见过有人无脑设成 0，结果系统 OOM 杀进程——因为内核认为换页成本太高而拒绝交换。正确做法：让 `swappiness` 和存储介质匹配——HDD 设低，SSD 可稍高。

---

## 四、磁盘 I/O 性能优化

### 4.1 关键指标

- **`%util`**：磁盘忙闲程度。接近 100% 表示饱和。
- **`await`**：平均 I/O 等待时间。HDD 应 <20ms，SSD <5ms。
- **`r/s`、`w/s`**：每秒请求数。高 IOPS 需要高性能磁盘。
- **`svctm`**：实际服务时间（已不准确，忽略）。

### 4.2 常见优化手段

#### (1) 选择正确的 I/O 调度器

- **mq-deadline**：默认调度器，平衡延迟与吞吐，适用于大部分设备。
- **none（NOOP）**：适用于 NVMe SSD，将调度交给硬件。
- **bfq**：适合桌面/多媒体场景，保低延迟。

```bash
# 查看当前调度器
cat /sys/block/sda/queue/scheduler

# 临时修改
echo mq-deadline > /sys/block/sda/queue/scheduler

# 永久修改：内核参数 elevator
GRUB_CMDLINE_LINUX="elevator=mq-deadline"
```

#### (2) 调整预读值（read-ahead）

预读值太大浪费内存，太小影响顺序读性能。

```bash
# 查看当前值（单位 512 字节扇区）
blockdev --getra /dev/sda

# 设置预读为 8MB (16384 扇区)
blockdev --setra 16384 /dev/sda
```

#### (3) 文件系统挂载选项优化

```bash
# /etc/fstab 示例

# 普通 SSD + ext4：禁用访问时间更新，降低写负载
UUID=xxx / ext4 defaults,noatime,nodiratime,discard 0 1

# 数据库服务器：禁用日志更新（有风险）
UUID=xxx /data ext4 defaults,noatime,data=writeback 0 2

# XFS：适合大文件，增大分配组
UUID=xxx /data xfs defaults,noatime,largeio,inode64 0 0
```

#### (4) 使用更快的存储或分层存储

- 将频繁读写的数据移到 SSD/内存盘（`tmpfs`）
- 使用 bcache、LVM cache 或 dm-cache 实现缓存加速

!!! tip "因材施教，量体裁衣"
    很多优化措施是“有代价的”。例如 `data=writeback` 可以提高 ext4 写入性能，但系统崩溃后可能丢失数据或元数据损坏。数据库通常用 `data=ordered` 默认模式更安全。对于日志服务器或可重算的临时数据，则可以大胆采用激进选项。理解 workload（随机读 vs 顺序写、OLTP vs 批处理）才是选择优化方向的根本。

---

## 五、网络性能优化

### 5.1 关键指标

- **重传率**：`TcpRetransSegs / OutSegs` > 2% 有问题
- **接收/发送缓冲区溢出**：`ss -s` 中的 `sockstat` 列
- **软中断 CPU 占用**：`top` 里的 `%si`

### 5.2 常见优化手段

#### (1) 调整 TCP 缓冲区大小

```bash
# /etc/sysctl.conf

# 增大 TCP 缓冲区范围（用于高带宽高延迟链路）
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728

# 启用窗口缩放（支持大窗口）
net.ipv4.tcp_window_scaling = 1
```

#### (2) 减少 TIME_WAIT 连接数量

```bash
# 允许更快回收 TIME_WAIT socket（注意：NAT 环境下慎用）
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30

# 增大本地端口范围
net.ipv4.ip_local_port_range = 1024 65000
```

#### (3) 网卡多队列与软中断负载均衡

```bash
# 查看队列数
ethtool -l eth0

# 设置多队列（需要驱动支持）
ethtool -L eth0 combined 4

# 手动设置 RPS（Receive Packet Steering）
echo f > /sys/class/net/eth0/queues/rx-0/rps_cpus
```

#### (4) 开启 TCP 快速打开（TFO）

适用于频繁短连接场景（如 Web 服务）。

```bash
net.ipv4.tcp_fastopen = 3   # 1: 客户端, 2: 服务端, 3: 两者
```

!!! tip "欲速则不达"
    网络优化参数往往牵涉到 TCP 协议栈的深度机制。例如 `tcp_tw_reuse` 虽然可以复用 TIME_WAIT socket，但在负载均衡器后面可能会导致连接串扰。现在的内核推荐使用 `tcp_tw_reuse` 配合 `tcp_timestamps`，并且永远不要在生产使用 `tcp_tw_recycle`。

---

## 六、性能调优的正确流程

1. **建立基线**：在正常负载下，记录各项指标一周。
2. **寻找瓶颈**：使用监控工具定位当前系统最紧张的资源。
3. **提出假设**：比如“磁盘 I/O 等待过高是因为读取随机化”。
4. **测试验证**：在测试环境尝试一种优化手段，对比指标变化。
5. **上线实施**：采用灰度和回滚预案。
6. **持续监控**：观察一段时间，确认副作用。

!!! tip "行百里者半九十"
    性能优化不是一次性的。随着业务增长和内核版本升级，以前的调优参数可能不再适用。建议每半年审查一次 `/etc/sysctl.conf` 和启动参数，移除那些不再推荐或者被新内核更好实现了的选项。另外，**不要微优化**——如果某个调优只能带来不到 5% 的提升，除非是热点路径，否则不值得投入时间。

---

## 七、常见误区与反面案例

| 误区 | 正确做法 |
|------|----------|
| 随意清除 PageCache | 用 `sync && echo 3 > drop_caches` 前必须确认业务能容忍缓存丢失 |
| 盲目设置 `swappiness=0` | 内存紧张时会触发 OOM，应设为 1-10 之间的值 |
| 关闭所有服务以“释放资源” | 系统空闲资源会被内核用做缓存，关闭服务反而降低命中率 |
| 在生产环境直接修改 `/proc/sys/` 而不记录原始值 | 必须备份，且使用 `sysctl -w` 和 `sysctl.conf` 确保持久化 |
| 不区分 workload 就套用网络“优化”模板 | 高并发短连接和长连接大吞吐的优化方向截然相反 |

!!! tip "前车之鉴，后事之师"
    曾有一个案例：DBA 为提升 MySQL 性能，把 `vm.dirty_ratio` 从 20% 调高到 80%，结果某个大查询触发了大量脏页积压，内存耗尽前触发 flush 导致 I/O 尖峰，整个数据库僵死数分钟。最终调整到 40%，并配合 `vm.dirty_background_ratio=5` 才解决问题。这个故事告诉我们：**极端值往往比默认值更危险**。

---

## 八、实战练习

在虚拟机或实验环境中，尝试以下优化并观察前后效果：

1. **CPU 绑核**：启动两个死循环进程，一个绑核，一个不绑，用 `perf stat` 对比缓存未命中率。
2. **内存缓存回收**：运行一个大数据集查询（如 `find / -name "*.conf" > /dev/null`），观察 `free` 中 `buff/cache` 变化。然后手动 `echo 3 > drop_caches` 再查询，比较第二次的耗时。
3. **I/O 调度器对比**：在同一台机械硬盘上，分别使用 `mq-deadline` 和 `none` 调度器，用 `fio` 测试随机读写性能。
   ```bash
   fio --name=randwrite --rw=randwrite --bs=4k --size=1G --numjobs=4 --time_based --runtime=60
   ```
4. **网络吞吐调优**：在两台虚拟机之间用 `iperf3` 测试带宽，然后修改 TCP 缓冲区（`rmem/wmem`）为 16MB，再次测试，对比吞吐量变化。
5. **综合调优**：模拟混合负载（CPU+内存+磁盘），使用 `stress-ng`，然后尝试调整参数降低 `%sys` 或 `%iowait`。

!!! tip "师傅领进门，修行在个人"
    性能优化是最能体现 Linux 功底的领域。每遇到一个问题，建议深挖到内核源代码或权威文档，而不是轻信网上的“一键脚本”。推荐阅读《Systems Performance》（Brendan Gregg）和内核文档 `Documentation/admin-guide/sysctl/`。

---

## 九、总结

性能优化不是堆砌参数，而是**在理解系统组件协作关系基础上所做的权衡**。你需要：

- 能够**精准定位瓶颈**（监控、追踪）
- 知道每个参数**为什么有效、有何代价**（原理）
- 敢于**测试和回滚**（实践）

记住：**保持简单，避免过度工程**。很多时候，升级硬件（加内存、换 SSD）比折腾数十个内核参数更经济、更可靠。

### 推荐的优化顺序

1. **应用程序层**：算法优化、数据库索引、慢查询
2. **系统配置层**：文件系统挂载选项、调度器、内核参数
3. **硬件层**：内存扩容、磁盘升级、网卡队列

当你的技能达到能预言某个参数调整后的效果，并且能解释原因时，你就真正掌握了 Linux 性能优化的艺术。

下一步，你可以学习 **系统故障排查** 和 **Linux 内核追踪（eBPF）**，将优化能力推向更高层次。

Happy Tuning!