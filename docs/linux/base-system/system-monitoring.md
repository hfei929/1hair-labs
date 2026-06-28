# Linux 系统监控：洞悉系统脉搏的必备技能

系统监控是运维人员的“眼睛”和“耳朵”。无论你是排查性能瓶颈、定位异常进程，还是规划容量升级，掌握系统监控工具都能让你**知己知彼，百战不殆**。本文将从 CPU、内存、磁盘、网络、进程五个维度，介绍 Linux 下最实用的监控命令和技巧。

!!! tip "知己知彼，百战不殆"
    很多初学者只会用 `top` 看一眼 CPU 使用率，但真正的监控需要“多点开花”。我的经验是：**先全局后局部，先趋势后细节**。先用 `htop`、`dstat` 看整体负载，再用 `pidstat`、`iotop` 定位具体进程。切忌一上来就盯着某个数字看，容易错过关联异常。

---

## 一、系统负载与 CPU 监控

### 1. `uptime` —— 快速查看系统负载

```bash
uptime
# 输出示例：
# 14:23:15 up 10 days,  2:15,  3 users,  load average: 0.08, 0.03, 0.01
```

三个负载值分别代表 **1分钟、5分钟、15分钟** 的平均活跃进程数（包括正在运行和不可中断等待的进程）。负载值超过 CPU 核心数通常表示系统过载。

!!! tip "春江水暖鸭先知"
    对于负载值，我一般这样判断：**负载 < 0.7×核心数**：空闲；**0.7~1.0×核心数**：正常繁忙；**> 1.0×核心数**：可能有性能问题。但要注意，I/O 等待也会推高负载，此时 CPU 使用率可能并不高。

### 2. `top` / `htop` —— 实时进程监控

```bash
top
# 常用快捷键：
# P - 按 CPU 使用率排序
# M - 按内存使用率排序
# 1 - 展开所有 CPU 核心
# c - 显示完整命令路径
# k - 杀死进程
# q - 退出
```

`htop` 是增强版，支持鼠标操作和树形视图，使用更直观（需安装）。

```bash
sudo apt install htop   # Debian/Ubuntu
sudo dnf install htop   # RHEL/Fedora
htop
```

### 3. `mpstat` —— 查看每个 CPU 核心的使用率

```bash
# 安装 sysstat 包
sudo apt install sysstat

# 每秒报告一次，共 5 次
mpstat -P ALL 1 5
```

输出中 `%usr`（用户态）、`%sys`（内核态）、`%iowait`（等待 I/O）、`%idle`（空闲） 是关键指标。

### 4. `pidstat` —— 按进程查看 CPU 统计

```bash
# 查看所有进程的 CPU 使用情况，每秒一次
pidstat 1

# 查看特定进程
pidstat -p 1234 1
```

!!! tip "不见兔子不撒鹰"
    当系统负载高但 `top` 里找不到明显占用 CPU 的进程，很可能是 **I/O 等待** 或 **软中断** 造成的。此时用 `mpstat` 看 `%iowait`，若很高，再用 `iotop` 找哪个进程在疯狂读写。另外，`top` 里 `%si`（软中断）过高通常与网卡或磁盘驱动有关。

---

## 二、内存监控

### 1. `free` —— 查看内存使用概览

```bash
free -h
#              total   used   free   shared  buff/cache   available
# Mem:           7.7G   2.1G   1.2G    123M       4.4G       5.1G
# Swap:          2.0G   0.0B   2.0G
```

- **available** 是实际可用的内存（包括可回收的 cache），比 `free` 列更有参考价值。
- 大量 `buff/cache` 是正常的，Linux 会尽量利用空闲内存做缓存。

### 2. `vmstat` —— 虚拟内存统计

```bash
vmstat 1 5
# procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
#  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
```

关键列：

- **r**：运行队列长度（正在运行+等待 CPU 的进程数）
- **b**：处于不可中断睡眠的进程数（通常在等待 I/O）
- **si/so**：swap 换入换出量（非零表示内存紧张）
- **bi/bo**：块设备读/写量
- **us/sy/wa/id**：用户/系统/I/O等待/空闲 CPU 占比

### 3. `/proc/meminfo` —— 详细内存信息

```bash
cat /proc/meminfo | grep -E "^(MemTotal|MemFree|MemAvailable|SwapTotal|Cached)"
```

### 4. `smem` —— 更精确的内存占用报告（含 PSS）

`smem` 可以显示 **PSS（Proportional Set Size）**，按比例分摊共享内存，比 `RES` 更准确。

```bash
sudo apt install smem
smem -r -s pss | head -10
```

!!! tip "瑞雪兆丰年，内存看可用"
    很多新手看到 `free` 列很少就以为内存不足，其实应该看 `available`。在 Linux 中，空闲内存少并不意味着内存压力大——它会主动用内存做缓存。只有当 `available` 长期接近 0，且 `swap` 大量使用（`si/so` 非零），才需要考虑加内存。另外，`/proc/meminfo` 中的 `Shmem` 包括 tmpfs 和共享内存，有时会占很多，别误以为是泄露。

---

## 三、磁盘 I/O 监控

### 1. `iostat` —— 磁盘使用统计

```bash
iostat -x 1 5
# 关键列：
# %util：设备繁忙程度（接近100%说明磁盘饱和）
# await：平均 I/O 等待时间（毫秒）
# r/s, w/s：每秒读写请求数
# rkB/s, wkB/s：每秒读写数据量
```

### 2. `iotop` —— 按进程查看 I/O 活动

```bash
sudo iotop -o
# -o 只显示有 I/O 活动的进程
```

### 3. `df` / `du` —— 查看磁盘空间

```bash
df -h                     # 文件系统使用情况
du -sh /home/* | sort -hr # 查看每个用户目录大小，从大到小排序
```

### 4. `lsof` —— 查看进程打开的文件

```bash
lsof | grep deleted       # 查看已被删除但仍被进程占用的文件（空间未释放）
lsof -p 1234              # 查看某个进程打开的所有文件
```

!!! tip "冰冻三尺，非一日之寒"
    磁盘 I/O 问题往往逐渐积累。`iostat -x 1` 看到 `await` 值超过 20ms 就应警惕，超过 100ms 则严重影响性能。另外，`%util` 达到 100% 不一定代表磁盘坏了，可能是大量随机读写或队列深度过大。对于 SSD，`%util` 常接近 100% 但延迟可能仍可接受。解决 I/O 瓶颈的方法：增加缓存（如 `vm.dirty_ratio` 调整）、使用更快的磁盘（NVMe）、将日志或数据分散到多个磁盘。

---

## 四、网络监控

### 1. `ss` / `netstat` —— 查看网络连接和统计

```bash
ss -tunp                # 所有 TCP/UDP 连接及进程
ss -s                   # 汇总统计
```

### 2. `iftop` / `nethogs` —— 实时流量监控

```bash
sudo iftop -i eth0      # 显示接口流量，类似 top
sudo nethogs            # 按进程显示带宽使用
```

### 3. `nload` / `bmon` —— 更友好的流量图

```bash
nload eth0
bmon -p eth0
```

### 4. `nstat` —— 网络协议栈统计

```bash
nstat -z                # 显示并清零内核网络统计
netstat -s              # 传统方式
```

### 5. `tcpdump` / `tshark` —— 抓包分析

```bash
sudo tcpdump -i eth0 -nn port 80 -c 100
sudo tshark -i eth0 -Y "http.request"
```

!!! tip "工欲善其事，必先利其器"
    当怀疑网络丢包或重传时，`nstat -z` 观察 `TcpRetransSegs` 和 `TcpExtTCPLoss` 是否快速增长。若重传多，用 `mtr` 查链路质量。另外，`ss -ti` 可以查看每个 TCP 连接的精细信息（包括 RTT、重传、拥塞窗口），非常强大。示例：`ss -ti state established`。

---

## 五、综合性监控工具

### 1. `dstat` —— 多维度资源统计

`dstat` 能同时显示 CPU、磁盘、网络、分页、系统调用等，是 `vmstat+netstat+iostat` 的集大成者。

```bash
sudo apt install dstat
dstat -c -d -n -m -l --top-cpu --top-io --top-mem 2
```

### 2. `glances` —— 基于 Web 的全能监控

`glances` 提供终端 UI 和 Web 界面，支持跨平台。

```bash
sudo apt install glances
glances                    # 终端模式
glances -w                 # 启动 Web 服务，默认端口 61208
```

### 3. `atop` —— 历史回放功能

`atop` 记录系统活动日志，可回放任意时间点的状态。

```bash
sudo apt install atop
atop                       # 实时模式
atop -r /var/log/atop/atop_YYYYMMDD  # 回放某天的日志
```

!!! tip "兼听则明，偏信则暗"
    单一工具往往有局限。例如 `top` 看到的 CPU 高可能是 I/O 等待，而 `iostat` 才能揭示。我常用的“三板斧”是：**`dstat 2` 看全局 → `htop` 看进程 → `pidstat` 和 `strace` 钻细节**。对于历史问题排查，一定要提前部署 `atop` 或 `sysstat` 的周期收集（`sar`），否则故障发生后只能瞪眼。

---

## 六、系统日志监控

系统日志本身就是监控的重要数据源。

### 1. `journalctl` —— systemd 日志

```bash
# 查看所有内核消息
journalctl -k

# 实时跟踪最新日志
journalctl -f

# 查看某个服务的历史日志
journalctl -u ssh.service --since today

# 按时间过滤
journalctl --since "2025-03-01 00:00:00" --until "2025-03-02 00:00:00"
```

### 2. 传统 syslog（`/var/log/`）

```bash
tail -f /var/log/syslog        # Debian/Ubuntu
tail -f /var/log/messages      # RHEL/Fedora
tail -f /var/log/dmesg          # 内核启动日志
```

!!! tip "前事不忘，后事之师"
    监控系统不仅要看“当下”，更要追溯“过去”。建议开启 `sar`（sysstat 包）的定时收集，保留一个月的数据。遇到突发故障，`sar -u -f /var/log/sa/saXX` 可以回看历史负载。另外，配置日志轮转（`logrotate`）防止磁盘被日志写满。

---

## 七、报警与自动化

手工敲命令适合临时排查，生产环境需要自动报警和趋势分析。

### 常用开源监控方案简介

| 方案 | 特点 | 适用场景 |
|------|------|----------|
| **Zabbix** | 企业级，模板丰富，支持自动发现 | 中型及以上环境 |
| **Prometheus + Grafana** | 云原生，指标拉取模式，灵活查询 | 动态环境、K8s |
| **Netdata** | 高精度实时监控，开箱即用 | 单机或小规模集群 |
| **Nagios / Icinga** | 经典，基于检查脚本 | 传统 IDC |

### 最小化报警实现（使用 systemd timer + 脚本）

```bash
# 示例：当负载超过 4 时发送邮件
#!/bin/bash
load=$(uptime | awk -F'load average:' '{print $2}' | cut -d, -f1 | tr -d ' ')
if (( $(echo "$load > 4.0" | bc -l) )); then
    echo "High load: $load on $(hostname)" | mail -s "Alert" admin@example.com
fi
```

!!! tip "勿谓言之不预"
    报警要避免“风暴”：设置合理的阈值、重复间隔和静默期。另外，监控不是目的，可操作的动作才是。收到报警后，第一时间知道执行什么命令——最好文档化。我的习惯是每个监控项都对应一个“故障处理手册”链接。

---

## 八、实战练习

建议你在自己的 Linux 虚拟机上完成以下操作，体验监控工具：

1. **制造 CPU 负载**：`stress -c 4 --timeout 60`（需安装 `stress`），同时运行 `htop` 观察。
2. **制造内存占用**：`stress --vm 2 --vm-bytes 512M --timeout 60`，用 `free -h -s 1` 监控内存变化。
3. **制造磁盘 I/O**：`dd if=/dev/zero of=bigfile bs=1M count=1024 &`，用 `iostat -x 1` 观察 `%util` 和 `await`。
4. **制造网络负载**：`iperf3 -s`（服务端）和 `iperf3 -c 127.0.0.1`（客户端），用 `iftop` 观察。
5. **使用 `dstat` 同时监控以上所有指标**：`dstat -c -d -n -m -l --top-cpu --top-io`。
6. **分析日志**：`journalctl -f` 同时执行一些错误命令，观察日志输出。
7. **配置一个简单的 `sar` 采集**：启用 sysstat 的定时任务，一小时后查看历史数据。

!!! tip "纸上得来终觉浅，绝知此事要躬行"
    以上所有工具，都建议你实际运行并观察输出。可以故意写一个无限循环的 shell 脚本（`while :; do :; done`）来练习定位进程。然后学会用 `taskset` 绑定 CPU，`nice` 调整优先级，体验监控与调优的联动。

---

## 九、总结与最佳实践

Linux 系统监控的核心是“**从整体到局部，从实时到历史**”。你需要掌握以下技能：

- **CPU**：关注 `load average`、`%iowait`、运行队列长度（`r`）
- **内存**：看 `available` 而非 `free`，警惕 `swap` 换入换出
- **磁盘**：重点监控 `%util` 和 `await`，配合 `iotop` 找进程
- **网络**：关注重传、丢包、连接队列溢出
- **日志**：集中收集并轮转，定期 review

### 三条监控黄金法则

1. **监控先从无侵入开始**：先用 `/proc` 和系统命令，不要立刻安装重量级 agent。
2. **基线先行**：正常运行一周，记录各项指标的“正常范围”，之后才能定义“异常”。
3. **自动化报警与自愈**：监控的最终目标是减少人工干预。例如磁盘使用率超 85% 时，自动清理旧日志或扩容。

下一步，可以深入学习 **系统性能优化** 和 **故障排查**，将监控发现的问题真正解决。监控是手段，稳定才是目标。

Happy Monitoring!