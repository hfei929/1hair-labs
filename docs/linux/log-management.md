# Linux 系统日志管理：明察秋毫，有据可依

日志是系统的“黑匣子”。当系统出现故障、遭受攻击或需要性能分析时，日志往往是唯一的线索。高效的日志管理能让你**运筹帷幄之中，决胜千里之外**。本文将从日志的产生、收集、轮转、集中存储到分析告警，构建一套完整的日志管理方案。

!!! tip "前事不忘，后事之师"
    我曾遇到过一台服务器因日志写满磁盘而宕机，事后发现是某个程序疯狂输出错误信息，而日志轮转配置失效。从那时起，我养成了三个习惯：**日志分离、自动轮转、远程备份**。以下经验均来自真实教训。

---

## 一、Linux 日志体系概览

Linux 日志系统经历了几代演进：

| 组件 | 职责 | 常见实现 |
|------|------|----------|
| **内核日志** | 记录内核产生的消息 | `printk` → `/proc/kmsg` → `syslog()` |
| **系统日志守护进程** | 收集、过滤、转发日志 | `rsyslog`、`syslog-ng` |
| **systemd 日志** | 系统启动后所有服务日志 | `journald`（二进制、结构化） |
| **应用日志** | 各应用自己的日志文件 | Nginx `/var/log/nginx/`, MySQL error log |

现代 Linux 发行版同时运行 `journald` 和 `rsyslog`，两者可以协同工作。

---

## 二、journald：systemd 时代的日志中心

### 2.1 基本使用

```bash
# 查看所有日志
journalctl

# 实时跟踪新日志
journalctl -f

# 查看本次启动以来的日志（默认显示本次启动）
journalctl -b

# 查看上一次启动的日志（故障排查常用）
journalctl -b -1

# 按时间过滤
journalctl --since "2025-03-01 00:00:00" --until "2025-03-02 23:59:59"

# 查看某个单元的日志
journalctl -u ssh.service
journalctl -u nginx.service --since today

# 查看特定优先级的日志（err 及以上）
journalctl -p err

# 查看内核日志
journalctl -k
```

### 2.2 日志持久化配置

默认情况下，`journald` 仅将日志存储在内存（`/run/log/journal`），重启会丢失。若要持久化：

```bash
# 创建目录
sudo mkdir -p /var/log/journal
sudo systemd-tmpfiles --create --prefix /var/log/journal

# 设置权限
sudo journalctl --flush

# 检查日志占用
journalctl --disk-usage
```

### 2.3 限制日志大小（`/etc/systemd/journald.conf`）

```ini
[Journal]
# 持久化存储最大占用（默认10% of filesystem）
SystemMaxUse=2G
# 单个日志文件最大大小
SystemMaxFileSize=200M
# 保留时间
MaxRetentionSec=604800   # 7天

# 转发到 rsyslog（默认 yes）
ForwardToSyslog=yes
```

修改后重启：`sudo systemctl restart systemd-journald`

!!! tip "兼听则明，偏信则暗"
    `journalctl` 的强大在于结构化查询。我常用 `journalctl -o json-pretty` 输出 JSON 格式，再配合 `jq` 处理。例如，找出过去一小时产生最多日志的单元：
    ```bash
    journalctl --since "1 hour ago" -o json | jq -r '._SYSTEMD_UNIT' | sort | uniq -c | sort -rn | head
    ```
    此外，`journalctl --verify` 可以检查日志文件完整性。

---

## 三、rsyslog：传统日志的重臣

尽管 `journald` 很强大，许多应用仍依赖 `/var/log/` 下的文本日志。`rsyslog` 负责将 `journald` 的日志写入传统文件，并支持过滤、转发。

### 3.1 基本配置文件结构

- `/etc/rsyslog.conf`：主配置
- `/etc/rsyslog.d/`：自定义配置片段（推荐在此添加）

### 3.2 常用配置示例

```bash
# /etc/rsyslog.d/50-default.conf

# 所有信息都记录到 /var/log/messages
*.info;mail.none;authpriv.none;cron.none    /var/log/messages

# 认证相关日志单独存放
authpriv.*                                  /var/log/auth.log

# 内核日志
kern.*                                      /var/log/kern.log

# 邮件日志
mail.*                                      /var/log/mail.log

# 定时任务日志
cron.*                                      /var/log/cron.log

# 紧急消息发送到所有登录用户
*.emerg                                     :omusrmsg:*
```

### 3.3 高级功能：过滤与模板

```bash
# 只记录包含 "error" 的行
:msg, contains, "error"  /var/log/error.log

# 基于程序名过滤
:programname, isequal, "sshd"  /var/log/sshd.log

# 使用模板定义文件名（按日期分割）
$template DynamicFile,"/var/log/%$YEAR%-%$MONTH%-%$DAY%.log"
*.*  ?DynamicFile
```

### 3.4 重启与验证

```bash
sudo systemctl restart rsyslog
# 检查配置语法
rsyslogd -f /etc/rsyslog.conf -N1
```

!!! tip "没有规矩，不成方圆"
    日志分离是排障的基础。我会将 **SSH、Web、数据库、防火墙** 的日志分别写入独立文件，并设置不同的轮转策略。例如，防火墙日志可能增长很快，需要更激进的轮转；而数据库慢查询日志适合保留更久。使用 `rsyslog` 的过滤功能实现分离非常简单。

---

## 四、日志轮转（logrotate）

日志文件如果不轮转，最终会撑爆磁盘。`logrotate` 是 Linux 标准工具。

### 4.1 全局配置 `/etc/logrotate.conf`

```bash
# 默认每周轮转一次
weekly
# 保留4个轮转文件（即四周）
rotate 4
# 轮转后创建新文件
create
# 使用日期作为后缀
dateext
# 是否压缩旧日志
compress
# 延迟压缩（保留最近一个未压缩）
delaycompress
# 忽略缺失文件
missingok
# 如果日志为空则不轮转
notifempty
```

### 4.2 自定义配置（`/etc/logrotate.d/`）

以 `/etc/logrotate.d/nginx` 为例：

```bash
/var/log/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nginx adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

关键参数说明：
- `daily/weekly/monthly`：轮转周期
- `rotate N`：保留历史份数
- `postrotate/endscript`：轮转后执行的命令（常用于让程序重新打开日志文件）
- `sharedscripts`：对匹配的所有日志只执行一次脚本

### 4.3 手动测试与强制轮转

```bash
# 手动运行一次（调试模式）
sudo logrotate -d /etc/logrotate.conf

# 强制执行
sudo logrotate -f /etc/logrotate.conf

# 查看轮转状态
cat /var/lib/logrotate/status
```

!!! tip "凡事预则立，不预则废"
    我见过因为 `logrotate` 的 `copytruncate` 选项导致日志丢失的真实案例。`copytruncate` 虽然可以不重启服务，但在复制和截断之间有一个时间窗口，少量日志可能丢失。对于关键服务，推荐使用 `postrotate` 发送信号的方式。另外，记得为 `logrotate` 设置 crontab（大多数发行版已默认配置），检查 `/etc/cron.daily/logrotate`。

---

## 五、集中式日志管理

单机日志只能解决本地问题。当你有几十上百台服务器时，集中式日志系统是必需品。

### 5.1 使用 rsyslog 转发

#### 服务端配置（日志接收器）
```bash
# /etc/rsyslog.conf 开启模块
module(load="imtcp")
input(type="imtcp" port="514")

# 使用模板按客户端 IP 分类存储
$template RemoteLogs,"/var/log/remote/%FROMHOST-IP%/%PROGRAMNAME%.log"
*.* ?RemoteLogs
```

#### 客户端配置（发送方）
```bash
# 在 /etc/rsyslog.d/ 创建转发配置
*.* @@logserver.example.com:514
# @@ 表示 TCP，@ 表示 UDP
```

### 5.2 使用 ELK / Graylog / Loki

| 方案 | 特点 | 适用场景 |
|------|------|----------|
| **ELK**（Elasticsearch, Logstash, Kibana） | 功能最全，生态丰富 | 大中型环境、需要复杂查询和可视化 |
| **Graylog** | 内置搜索和告警，较 ELK 更易运维 | 中等规模，希望开箱即用 |
| **Loki + Promtail + Grafana** | 轻量，与 Prometheus 生态整合 | 云原生、K8s 环境，节省存储 |

#### 快速体验 Loki（单机版）：
```bash
# 使用 Docker 运行
docker run -d --name loki -p 3100:3100 grafana/loki
# 安装 promtail（收集日志并发送）
# 配置 Grafana 数据源为 Loki
```

!!! tip "尺有所短，寸有所长"
    不要一上来就搭建庞大的 ELK。对于中小环境，`rsyslog` 集中转发 + `grep` 已足够。当需要全文搜索和可视化时，再考虑 ELK。我的建议：**先集中，后分析**。即使是单机，也建议将重要日志发送到另一台服务器，避免攻击者清除本地证据。

---

## 六、日志分析与告警

### 6.1 常用命令行分析

```bash
# 统计 SSH 失败次数
grep "Failed password" /var/log/auth.log | wc -l

# 查看最频繁的 IP 攻击者
grep "Failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head

# 按小时统计 Nginx 状态码分布
awk '{print $4" "$9}' /var/log/nginx/access.log | cut -d: -f2 | sort | uniq -c
```

### 6.2 使用 logwatch 自动报告

```bash
sudo apt install logwatch
# 生成昨天的报告
sudo logwatch --detail High --mailto admin@example.com --service All --range yesterday
# 配置 cron 每天发送
```

### 6.3 使用 swatch / fail2ban 实时响应

`fail2ban` 可以读取日志，封禁恶意 IP。安装后配置 `/etc/fail2ban/jail.local`：

```ini
[sshd]
enabled = true
port    = ssh
logpath = %(sshd_log)s
maxretry = 3
bantime = 3600
```

!!! tip "见微知著，防患未然"
    告警不是越多越好。我设定了一个原则：**只有需要人工介入的事件才发告警**。例如，`Failed password` 每分钟几十次可能只是扫描，交给 fail2ban 自动处理即可；而 `panic`、`segfault`、`out of memory` 则必须实时告警。使用 `logwatch` 的报告作为日常巡检，可以及早发现异常趋势。

---

## 七、日志安全管理

### 7.1 防止日志被篡改

- **追加权限**：`chattr +a /var/log/secure` 只允许追加，无法删除或修改已有内容。
- **远程存储**：实时发送到另一台机器。
- **使用签名**：`rsyslog` 支持 TLS 加密传输，并可以签名。

### 7.2 隐私与合规

- 敏感信息（如密码、信用卡号）不应记录到日志，或使用脱敏工具。
- 遵守数据保留期限（如 GDPR 要求 6 个月），定期清理。

### 7.3 日志审计

结合 `auditd` 监控日志文件本身的访问：

```bash
auditctl -w /var/log/auth.log -p rwa -k log_access
```

!!! tip "君子不立于危墙之下"
    入侵者通常第一步会清除痕迹。除了远程存储，还可以使用 **`systemd-journal-remote`** 将 journal 日志实时转发到安全主机。另外，用 `logrotate` 的 `create` 模式会创建新文件，如果目录权限被篡改，可能导致日志无法写入。我习惯将 `/var/log` 放在单独分区，并使用配额限制。

---

## 八、实战练习

1. **探索 journald**：
   - 查看最近 10 条 SSH 登录失败的日志：`journalctl -u ssh --grep "Failed password" -n 10`
   - 输出 JSON 格式并用 `jq` 提取时间戳和消息。

2. **配置 rsyslog 分离**：
   - 创建 `/etc/rsyslog.d/sshd.conf`，将 sshd 的所有日志写入 `/var/log/sshd.log`。
   - 重启 rsyslog，测试 SSH 登录，检查新文件。

3. **日志轮转实验**：
   - 创建一个测试日志 `/var/log/test.log`，用 `logrotate` 配置每日轮转，保留 3 份，压缩。
   - 手动运行 `logrotate -f`，观察轮转后的文件。

4. **集中式日志**：
   - 在两台虚拟机之间配置 rsyslog 转发，一台作为服务端，一台作为客户端。
   - 在客户端执行 `logger "test message"`，服务端检查 `/var/log/remote/` 目录。

5. **日志分析**：
   - 使用 `logwatch --detail High` 生成报告。
   - 写一个 shell 脚本，统计昨天 `/var/log/auth.log` 中认证失败的 IP 前 10 名。

6. **告警实验**：
   - 配置 fail2ban 监控 SSH，故意输错密码多次，检查 IP 是否被封禁。

!!! tip "实践出真知"
    你可以自己编写一个简单的日志生成器：`while true; do echo "$(date): test" >> /var/log/mylog.log; sleep 1; done`，然后用 `logrotate` 配置轮转，观察 `postrotate` 是否能正确处理。

---

## 九、总结

日志管理是系统运维的基石。高效的管理体系应包含：

- **统一收集**：journald + rsyslog 覆盖所有来源
- **合理存储**：持久化、轮转、压缩、分离
- **集中归档**：远程转发或 ELK 类系统
- **主动分析**：定期报告 + 实时告警
- **安全保护**：追加权限、远程备份、审计

### 三条经验

1. **永远不要把日志放在 root 分区**：单独挂载 `/var` 分区，并设置 inode 限制。
2. **自动化轮转和清理**：不要依赖手动 `rm`。
3. **集中存储比本地重要**：至少把认证日志（auth）发送到远程。

下一步，你可以学习 **系统故障排除**，将日志分析技能用于实际问题定位。

Happy Logging!