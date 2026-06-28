# Linux 系统故障排除：拨云见日，精准定位

系统故障排除是最能考验 Linux 运维综合能力的环节。当系统出现异常时，**恐慌和盲目操作是最大的敌人**。本文将从故障排查的方法论出发，结合 CPU、内存、磁盘、网络、应用等常见故障场景，提供一套系统化的定位思路和工具链，帮助你**沉着冷静、有理有据**地解决问题。

!!! tip "临危不乱，有的放矢"
    故障发生时，第一件事不是查百度，而是**收集现场信息**。我见过有人遇到负载飙升就重启服务器，结果丢失了所有可能的原因痕迹。正确的做法是：先 `uptime`、`dmesg -T | tail`、`top -bn1` 保存快照，再尝试恢复。以下方法论来自大量实战教训。
    
![Linux 故障排查指南](../assets/images/linux/Linux-troubleshooting.png)

---

## 一、故障排查方法论

### 1.1 分步排查原则

```
现象确认 → 信息收集 → 假设验证 → 定位根因 → 修复验证 → 复盘总结
```

### 1.2 常用信息收集命令

| 命令 | 作用 | 适用时机 |
|------|------|----------|
| `uptime` | 负载和运行时间 | 第一印象 |
| `dmesg -T \| tail` | 内核环形缓冲区最后几条消息 | 硬件/OOM/内核错误 |
| `last \| head` | 最近登录记录 | 怀疑入侵 |
| `ss -tunlp` | 监听端口和连接 | 服务不可用 |
| `ps auxf` | 进程树及状态 | 找出异常进程 |
| `free -h` | 内存概况 | 内存不足 |
| `df -h` | 磁盘空间 | 磁盘满 |
| `journalctl -xe` | 最新系统日志 | 大部分故障 |

### 1.3 故障分级与响应

- **P0（致命）**：服务完全不可用，立即响应，优先恢复而非排查原因。
- **P1（严重）**：部分功能受损，快速定位并修复。
- **P2（一般）**：性能下降或非核心问题，计划内处理。
- **P3（轻微）**：警告或异常但无影响，记录留待分析。

!!! tip "磨刀不误砍柴工"
    我习惯为每台服务器建立一个“救援文档”，包含：管理 IP、带外登录方式、常用服务启动命令、最近一次变更记录。这样在慌乱时也能按图索骥。此外，`screen` 或 `tmux` 是必备技能——意外断线后可以重新连回之前的会话。

---

## 二、常见故障场景与解决思路

### 2.1 无法登录（SSH 连不上）

**现象**：`Connection refused` 或 `Connection timed out`。

**排查步骤**：

1. **网络层**：`ping` 目标 IP，检查网络通断。
2. **端口**：`telnet <IP> 22` 是否通？
3. **服务状态**：有带外管理时，登录后 `systemctl status sshd`。
4. **防火墙**：`iptables -L -n` 或 `firewall-cmd --list-all`。
5. **SSH 配置**：`PermitRootLogin no` 是否误封了普通用户？`AllowUsers` 是否正确？
6. **资源耗尽**：`MaxStartups` 或 `MaxSessions` 达到上限。

**常用命令**：
```bash
# 从另一台机器测试
ssh -vvv user@host   # 详细调试输出
nmap -p 22 host      # 扫描端口

# 本地（有带外时）
systemctl status sshd
journalctl -u ssh -n 50
ss -tlnp | grep :22
```

!!! tip "柳暗花明又一村"
    当 SSH 完全无法连接时，如果服务器有 BMC/iDRAC/IPMI，一定要提前配置好。没有的话，可以在 cron 里加一个反向 SSH 隧道作为备用通道。例如：`*/5 * * * * ssh -R 2222:localhost:22 user@backup-server -N`，紧急时通过备份服务器跳转。

### 2.2 系统负载过高

**现象**：`uptime` 负载 > CPU 核心数 * 0.7，系统响应缓慢。

**排查步骤**：

1. **负载类型**：`mpstat -P ALL 1` 查看每个 CPU 的 `%usr`、`%sys`、`%iowait`。
   - 高 `%usr`：用户进程计算密集 → `top`/`htop` 找 CPU 高的进程。
   - 高 `%sys`：内核态占用多 → 可能系统调用频繁，或用 `strace -c -p <pid>`。
   - 高 `%iowait`：磁盘瓶颈 → 转磁盘排查。
2. **运行队列**：`vmstat 1` 看 `r`（运行队列）和 `b`（阻塞 I/O）列。
3. **上下文切换**：`vmstat` 的 `cs` 列过高，可能进程/线程数量爆炸。
4. **查看具体进程**：`htop` 按 P 排序 CPU，按 M 排序内存。

**解决思路**：
- 应用层优化（代码、配置）
- 限制资源（cgroup、`nice`）
- 扩容（CPU 核心数、升级硬件）

!!! tip "抽丝剥茧，层层深入"
    负载高不一定是 CPU 不足。例如 Nginx 配置 `worker_processes auto` 但每个 worker 绑定一个 CPU，若请求大量静态小文件，软中断可能导致 `%si` 升高。用 `top` 按 `1` 看各核心，若某个核心 `%si` 偏高，检查网卡多队列是否开启。

### 2.3 内存不足与 OOM

**现象**：`dmesg` 中出现 `Out of memory: Kill process`，服务进程被杀死。

**排查步骤**：

1. **查看可用内存**：`free -h` 看 `available` 列。
2. **查看 swap 使用**：`swapon --show`，`vmstat 1` 看 `si`/`so`。
3. **内存占用 Top 10**：`ps aux --sort=-%mem | head`
4. **查看 slab 内存**：`slabtop`（内核缓存占用）。
5. **查看 OOM 评分**：`cat /proc/<pid>/oom_score`。

**解决思路**：
- 调整 OOM 优先级：`echo -500 > /proc/<pid>/oom_score_adj` 保护关键进程。
- 增加内存或 swap。
- 检查内存泄漏（`valgrind` 或 `pmap`）。
- 限制进程内存（systemd `MemoryMax` 或 cgroups）。

!!! tip "未雨绸缪，有备无患"
    我习惯设置 `vm.panic_on_oom=0`（默认）让内核自行处理，同时开启 `sysrq` 以便在内存紧张时触发 `echo f > /proc/sysrq-trigger` 手动 OOM。另外，`/var/log/kern.log` 中的 OOM killer 日志会显示被杀进程的内存映射，是定位泄漏的关键。

### 2.4 磁盘空间满（No space left on device）

**现象**：`df -h` 显示使用率 100%，但 `du -sh /*` 统计总和不符。

**排查步骤**：

1. **inode 耗尽**：`df -i` 检查 inode 使用率，若满则删除大量小文件。
2. **被删除但仍在打开的文件**：`lsof | grep deleted`，这些文件虽被删除但未释放空间，重启相关进程即可。
3. **挂载点覆盖**：某个目录下有文件，但该目录被另一个文件系统挂载覆盖，原文件不可见但仍占空间。`mount --bind / /mnt` 然后检查 /mnt 对应目录。
4. **隐藏日志**：某些程序不经过 syslog 直接写文件，轮转失效。

**解决思路**：
- 清理日志：`journalctl --vacuum-size=200M`
- 清理旧内核：`apt autoremove` 或 `dnf remove $(dnf repoquery --installonly --latest-limit=-3)`
- 查找大文件：`find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null`

!!! tip "小不忍则乱大谋"
    磁盘满导致服务不可用是最常见的故障之一。我习惯对 `/var/log` 单独分区，并设置 `logrotate` 最大保留 30 天。同时用 `monit` 监控磁盘使用率超过 80% 时告警，超过 90% 自动清理 `/tmp` 和 `journald` 日志。

### 2.5 网络不通或丢包严重

**现象**：`ping` 丢包、连接超时。

**排查步骤**：

1. **本机检查**：`ip link` 接口是否 UP；`ip addr` IP 配置；`ip route` 默认路由。
2. **ARP 检查**：`arp -n` 看邻居 MAC 是否正确。
3. **链路质量**：`mtr -r <dest>` 观察各跳延迟和丢包率。
4. **防火墙**：`iptables -L -n -v` 统计丢包计数。
5. **网卡丢包**：`ethtool -S eth0 | grep drop`，`ip -s link show eth0`。
6. **连接队列溢出**：`ss -lnt` 查看 `Recv-Q` / `Send-Q` 是否有积压。

**解决思路**：
- 调整内核参数（`net.core.somaxconn`、`net.ipv4.tcp_max_syn_backlog`）
- 网卡多队列、中断亲和性
- 升级网卡驱动或固件

!!! tip "路遥知马力，日久见人心"
    间歇性网络故障最难排查。我曾在一次故障中发现只有 1500 字节以上的大包丢包，最终定位到交换机 MTU 配置不一致。建议使用 `ping -M do -s 1472 <dest>` 测试 MTU。另外，`tcpdump` 抓取 ICMP 包，观察是否有 `frag needed` 消息。

### 2.6 服务无法启动或频繁重启

**现象**：`systemctl status <service>` 显示 `failed` 或 `activating` 状态。

**排查步骤**：

1. **查看服务日志**：`journalctl -u <service> -n 50 -e`
2. **检查配置文件语法**：例如 Nginx `nginx -t`，MySQL `mysqld --validate-config`
3. **端口冲突**：`ss -tlnp | grep :<port>`
4. **依赖服务未启动**：`systemctl list-dependencies <service>`
5. **权限问题**：服务运行用户对配置文件、日志目录是否有写权限。
6. **资源限制**：`systemctl show <service> | grep -E "Limit|Memory"`

**解决思路**：
- 修复配置文件后 `systemctl daemon-reload`
- 手动前台运行：`/usr/sbin/nginx -c /etc/nginx/nginx.conf` 查看错误输出。
- 启用 `PrivateTmp=true` 防止 /tmp 冲突。

!!! tip "知错能改，善莫大焉"
    有些服务启动失败是因为环境变量缺失。可以用 `systemctl edit <service>` 添加 `Environment=` 或 `EnvironmentFile=`。另外，`strace -f -p <pid>` 跟踪系统调用，观察服务启动时卡在哪个文件或 socket。

---

## 三、经典故障案例与排查过程

### 案例1：CPU 使用率偶发飙升至 100%

**现象**：某 Web 服务器每天下午 3 点左右 CPU 飙升至 100%，持续 10 分钟后恢复。

**排查过程**：
1. 事先配置了 `atop` 记录历史，回放 3 点的日志发现是 `cron` 启动了某个脚本。
2. 检查 cron 条目：`*/5 * * * * /usr/local/bin/backup.sh`，发现该脚本会对整个 `/var/www` 打包压缩。
3. 压缩过程消耗大量 CPU，且未限制 `nice`。
4. **解决**：在脚本中加入 `nice -n 19` 降低优先级，并将执行时间改为凌晨。

**经验**：定时任务是 CPU 尖峰的常见来源，使用 `atop` 或 `sysstat` 回看是定位的关键。

### 案例2：磁盘空间莫名减少

**现象**：`df -h` 显示 `/` 分区使用率每天增长 1%，但 `du -sh /*` 加起来远小于已用空间。

**排查过程**：
1. 怀疑有文件被删除但仍被进程占用，执行 `lsof | grep deleted`。
2. 发现 `/var/log/messages` 被删除，但 rsyslog 进程仍持有句柄。
3. **解决**：重启 rsyslog 服务，空间立即释放。

**经验**：`lsof | grep deleted` 是排查“幽灵文件”的利器，配合 `df` 和 `du` 对比使用。

### 案例3：某端口无法访问，但本地监听正常

**现象**：`ss -tlnp` 显示 8080 端口处于 `LISTEN` 状态，但从外部 `telnet` 不通。

**排查过程**：
1. 检查防火墙：`iptables -L -n` 没有拒绝规则。
2. 检查服务绑定 IP：`ss -lntp | grep 8080` 显示 `127.0.0.1:8080`，只绑定了本地环回。
3. **解决**：修改配置文件中的 `listen` 指令为 `0.0.0.0` 或服务器实际 IP。

**经验**：服务绑定 IP 地址错误是最容易被忽视的原因。`netstat -tlnp` 中显示的 `127.0.0.1` 或 `::1` 表示仅本地。

---

## 四、高级排查工具与技巧

### 4.1 追踪进程系统调用（strace）

```bash
# 跟踪进程的系统调用和耗时
strace -c -p <pid>        # 汇总统计
strace -T -p <pid>        # 显示每个调用耗时
strace -f -o /tmp/strace.log <command>
```

### 4.2 动态追踪（perf / eBPF）

```bash
# perf top 实时显示热点函数
perf top -p <pid>

# 记录 CPU 采样
perf record -a -g -- sleep 30
perf report

# bpftrace 简单示例（需安装）
bpftrace -e 'kprobe:vfs_read { @[comm] = count(); }'
```

### 4.3 内存分析（valgrind / heaptrack）

```bash
valgrind --leak-check=full ./my_program
```

### 4.4 使用 systemd 的故障排查功能

```bash
# 查看服务启动失败的原因
systemctl status <service> -l --no-pager

# 查看服务的环境变量
systemctl show <service> --property=Environment

# 覆盖服务配置（临时）
systemctl edit <service>
```

!!! tip "工欲善其事，必先利其器"
    以上工具需要提前安装。建议在每台服务器上保留 `sysstat`（`sar`）、`perf`、`strace`、`lsof`、`tcpdump` 等基础工具。此外，`sos report` 可以一键收集几乎所有诊断信息，方便提交给厂商或社区求助。

---

## 五、实战练习

1. **模拟 CPU 高负载**：`stress -c 4 --timeout 60`，用 `top`、`mpstat`、`pidstat` 定位进程。
2. **模拟内存泄漏**：编写一个不断分配内存的 C 程序或使用 `stress --vm 1 --vm-bytes 512M`，观察 OOM 行为。
3. **模拟磁盘空间满**：`fallocate -l 5G /tmp/bigfile`，然后练习使用 `df`、`du`、`lsof` 排查。
4. **模拟网络丢包**：`tc qdisc add dev eth0 root netem loss 10%`，然后用 `ping`、`mtr` 排查。
5. **服务故障**：故意破坏一个服务的配置文件，练习使用 `journalctl` 和配置文件测试命令。
6. **综合排障**：在一个虚拟机中同时模拟多种故障，要求自己写出排查顺序和每条命令的意义。

!!! tip "熟能生巧，百炼成钢"
    故障排查能力只能通过实战提高。建议在测试环境中故意破坏系统（但要有快照），然后尝试仅用命令行恢复。时间久了，你会形成肌肉记忆。

---

## 六、总结

故障排除不是玄学，而是有章可循的科学。核心方法论：

- **收集现场**：不要急于重启或修复，先备份日志和状态。
- **由外到内**：从用户感知 → 服务状态 → 系统资源 → 内核日志，层层深入。
- **隔离变量**：每次只改变一个因素，验证假设。
- **善用工具链**：`top` → `dstat` → `strace` → `perf`，由粗到细。
- **复盘总结**：记录故障原因、解决步骤、预防措施。

### 排查流程图（简化版）

```
用户报障
  │
  ├─ 服务可用性？ → 检查端口、进程、防火墙
  │
  ├─ 性能慢？ → CPU/内存/磁盘/网络检查
  │
  ├─ 功能异常？ → 应用日志、配置、依赖服务
  │
  └─ 完全不可用？ → 查看 dmesg、系统日志、硬件告警
```

### 终极建议

- **监控先行**：没有监控，故障排查如同盲人摸象。
- **文档化**：将经常遇到的故障整理成 Runbook，团队共享。
- **自动化恢复**：对于常见故障（如磁盘满），可以编写脚本自动清理。

下一步，你可以学习 **Linux 内核参数调优** 或 **容器化运维**，将故障排查能力应用于更复杂的场景。

Happy Troubleshooting!