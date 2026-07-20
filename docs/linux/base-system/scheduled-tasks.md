---
title: Linux 定时任务：Cron 与 Systemd Timer 完整指南 | 1Hair Labs
description: 深入讲解 Linux 定时任务机制，涵盖 Cron 语法与常见陷阱、Anacron 补执行、Systemd Timer 替代方案、日志监控与生产环境最佳实践。
keywords:
  - Cron
  - crontab
  - Systemd Timer
  - 定时任务
  - Anacron
  - 自动化运维
  - Linux
---

# Linux 定时任务：Cron 与 Systemd Timer 完整指南

## 前言

定时任务是自动化运维的基石。备份数据库、清理过期日志、定期巡检服务——这些都不应该靠人工手动执行。Linux 提供了两个主流方案：经典的 **Cron** 和现代的 **Systemd Timer**。

本文从 Cron 语法开始，深入常见陷阱（环境变量、路径、日志），再对比 Systemd Timer 的优势，帮你选择最适合的自动化方式。

!!! tip "先读完这篇文章再写定时任务"
    太多人写过「脚本手动跑 OK，Cron 里就是不行」的 Bug。看完「常见陷阱」那一节，你会省下大量调试时间。

---

## Cron 基础

### Crontab 语法

```text
*     *     *     *     *      /path/to/command
│     │     │     │     │
│     │     │     │     └── 星期（0-7，0 和 7 都表示周日）
│     │     │     └────── 月份（1-12）
│     │     └──────────── 日期（1-31）
│     └────────────────── 小时（0-23）
└──────────────────────── 分钟（0-59）
```

### 常见时间表达式

| 表达式 | 含义 |
| --- | --- |
| `*/5 * * * *` | 每 5 分钟 |
| `0 * * * *` | 每小时整点 |
| `0 2 * * *` | 每天凌晨 2 点 |
| `0 3 * * 0` | 每周日凌晨 3 点 |
| `0 4 1 * *` | 每月 1 号凌晨 4 点 |
| `0 9-17 * * 1-5` | 工作日 9 点到 17 点，每小时一次 |
| `30 2 1,15 * *` | 每月 1 号和 15 号凌晨 2:30 |

### 管理 Crontab

```bash
# 编辑当前用户的 crontab
crontab -e

# 查看当前用户的 crontab
crontab -l

# 删除当前用户的 crontab
crontab -r

# 以指定用户身份编辑（root 权限）
sudo crontab -u www-data -e

# 系统级 crontab（不推荐直接编辑）
cat /etc/crontab
```

### Crontab 示例

```bash
# 每天凌晨 2 点备份数据库
0 2 * * * /opt/scripts/backup-db.sh

# 每小时清理超过 7 天的临时文件
0 * * * * find /tmp -name "*.tmp" -mtime +7 -delete

# 每 5 分钟检查服务健康
*/5 * * * * /opt/scripts/healthcheck.sh >> /var/log/healthcheck.log 2>&1

# 每周日 3 点更新软件包
0 3 * * 0 apt update && apt upgrade -y
```

---

## Cron 常见陷阱

### 1. 环境变量不全

**Cron 运行的环境比交互式 Shell 少得多**——`PATH` 通常只有 `/usr/bin:/bin`，`HOME`、`USER` 以外的变量大多不存在。

```bash
# 错误示范：直接写 mysql 命令
0 2 * * * mysqldump -u root mydb > /backup/db.sql
# Cron: mysqldump: command not found（PATH 里没有）

# 正确做法 1：使用绝对路径
0 2 * * * /usr/bin/mysqldump -u root mydb > /backup/db.sql

# 正确做法 2：在脚本中设置 PATH
#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
mysqldump -u root mydb > /backup/db.sql

# 正确做法 3：在 crontab 顶部定义环境变量
PATH=/usr/local/bin:/usr/bin:/bin
0 2 * * * mysqldump -u root mydb > /backup/db.sql
```

### 2. `%` 符号被转义

Cron 中 `%` 会被转换成换行符。如果你需要用 `%`（例如 `date +%Y%m%d`）：

```bash
# 错误
0 2 * * * mysqldump mydb > /backup/db_$(date +%Y%m%d).sql
# 实际执行变成了：date +Y

# 正确：用反斜杠转义
0 2 * * * mysqldump mydb > /backup/db_$(date +\%Y\%m\%d).sql

# 或者把命令写到脚本里（推荐）
```

### 3. 输出无处可去

Cron 会把 stdout 和 stderr 通过邮件发送给用户。如果没配邮件服务，输出就丢了，错误也没法排查：

```bash
# 始终重定向
0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### 4. 凌晨 2 点到 3 点之间的夏令时坑

如果系统有时区切换（夏令时），凌晨 2:00 的任务可能：
-   被跳过（时钟直接从 1:59 → 3:00）
-   被执行两次（时钟回拨）

**解决**：避开凌晨 2:00-3:00，或改用 Systemd Timer（它用 UTC 单调时钟）。

---

## Anacron：确保错过也能执行

如果服务器在凌晨 2 点关机了，Cron 错过了备份任务——第二天它不会补执行。`anacron` 弥补了这个缺陷：

```bash
# /etc/anacrontab
# 周期(天)  延迟(分钟)  任务名     命令
1            5           cron.daily   run-parts /etc/cron.daily
7            10          cron.weekly  run-parts /etc/cron.weekly
30           15          cron.monthly run-parts /etc/cron.monthly
```

Anacron 会记录上次执行时间，开机后检查是否有任务过期未执行，自动补跑。适用于**非 7×24 运行的机器**。

---

## Systemd Timer 替代方案

Systemd Timer 是 Cron 的现代替代品，优势明显：

### Timer 示例

`/etc/systemd/system/cleanup.service`：

```ini
[Unit]
Description=Temp File Cleanup

[Service]
Type=oneshot
ExecStart=/usr/bin/find /tmp -name "*.tmp" -mtime +7 -delete
```

`/etc/systemd/system/cleanup.timer`：

```ini
[Unit]
Description=Run temp cleanup hourly

[Timer]
OnCalendar=hourly
Persistent=true              # 错过了补执行
RandomizedDelaySec=30        # 随机延迟 0~30 秒，避免惊群

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable cleanup.timer --now

# 查看所有 Timer
systemctl list-timers
```

### 高级 Timer 配置

```ini
[Timer]
# 按日历时间
OnCalendar=*-*-* 02:00:00          # 每天凌晨 2 点
OnCalendar=Mon..Fri 09:00          # 工作日 9 点
OnCalendar=Sat,Sun 06:00           # 周末 6 点

# 按间隔（单调时钟，不受夏令时影响）
OnUnitActiveSec=1h                 # 上次执行后 1 小时
OnBootSec=5min                     # 开机后 5 分钟

# 精度窗口（分散负载，避免惊群）
RandomizedDelaySec=60

# 固定间隔（不受任务执行时长影响，类似 Cron）
AccuracySec=1s

# 持久化（错过补执行）
Persistent=true
```

---

## Cron vs Systemd Timer

| | Cron | Systemd Timer |
| --- | :---: | :---: |
| **配置方式** | 单行命令 | Service + Timer 两个文件 |
| **日志** | 需自行重定向或依赖邮件 | `journalctl -u xxx.service` 自动记录 |
| **错过补执行** | 需 anacron 辅助 | `Persistent=true` |
| **随机延迟** | 手动 `sleep $((RANDOM%60))` | `RandomizedDelaySec=` |
| **依赖管理** | 无 | `After=`、`Requires=` |
| **资源限制** | 无 | `MemoryMax=`、`CPUQuota=` |
| **夏令时** | 容易出坑 | `OnUnitActiveSec` 用单调时钟不受影响 |
| **调试** | 依赖邮件或手动执行 | `systemctl status` + journal 一体化 |
| **禁用** | 注释掉或删除行 | `systemctl disable --now` |

!!! tip "迁移建议"
    -   简单、低频的定时任务（每天备份一次）：Cron 足够
    -   需要日志、依赖、资源限制的：Systemd Timer
    -   新系统/新项目：优先选 Systemd Timer

---

## 监控与排错

### 查看 Cron 是否在运行

```bash
systemctl status cron      # Debian/Ubuntu
systemctl status crond     # RHEL/Rocky
```

### 查看 Cron 执行日志

```bash
# Debian/Ubuntu
grep CRON /var/log/syslog

# RHEL/Rocky
journalctl -u crond

# 或查看 mail（如果配了）
mail
```

### 调试不执行的定时任务

```bash
# 1. 看 Cron 服务是否运行
systemctl status cron

# 2. 看 Cron 日志有没有「执行了」
grep CRON /var/log/syslog | grep "your_script"

# 3. 模拟 Cron 环境运行脚本
env -i HOME=$HOME LOGNAME=$LOGNAME PATH=/usr/bin:/bin SHELL=/bin/sh sh -c '/opt/scripts/backup.sh'

# 4. 检查脚本权限
ls -la /opt/scripts/backup.sh
# 必须有执行权限！

# 5. 检查脚本末尾
# 脚本最后一行是否有换行符？
tail -c1 /opt/scripts/backup.sh | xxd
# 应该是 0a（换行符），不是空
```

---

## 生产环境最佳实践

1. **脚本独立**：不要在 crontab 里写复杂命令，写成独立脚本，crontab 只调用脚本
2. **日志重定向**：每条任务都加上 `>> /var/log/xxx.log 2>&1`
3. **锁机制**：防止上次任务没跑完，下次又启动了：

```bash
#!/bin/bash
LOCKFILE=/tmp/backup.lock
exec 200>"$LOCKFILE"
flock -n 200 || { echo "Another instance is running"; exit 1; }

# ... 实际的备份逻辑 ...

flock -u 200
```

4. **避开整点**：加上随机延迟，避免与大量其他任务同时触发（Cron 用 `sleep $((RANDOM%60))`，Timer 用 `RandomizedDelaySec`）
5. **监控告警**：关键任务的失败应该触发告警，而不是安静地失败

---

## 下一步学习

| 方向 | 教程 |
| --- | --- |
| **systemd** | [systemd 详解](systemd-explained.md) — Timer 的底层平台 |
| **Shell 脚本** | [Shell 基础](../shell/index.md) — 写更好的定时任务脚本 |
| **日志管理** | [日志管理](log-management.md) — 定时任务日志轮转 |
| **进程管理** | [进程管理](process-management.md) — 理解 Cron 守护进程 |

---

## 总结

定时任务是自动化运维的第一步：

1. **Cron 简单但坑多**：环境变量、`%` 转义、输出丢失、夏令时——都记住了再上线
2. **Systemd Timer 更现代**：有日志、有补执行、有随机延迟、有资源限制
3. **Anacron**：非 7×24 机器的救星，错过也能补跑
4. **生产环境**：脚本独立 + 日志重定向 + 文件锁 + 监控告警

选对工具，写好脚本，加上监控——你的定时任务就不会是「设了但不知道跑没跑」的黑盒。 🚀
