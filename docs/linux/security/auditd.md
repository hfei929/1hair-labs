---
title: Linux 审计系统：auditd 配置与安全事件追踪 | 1Hair Labs
description: 深入讲解 Linux auditd 审计框架，涵盖审计规则编写、ausearch/aureport 日志分析、关键文件变更监控、用户行为追踪与合规审计报告生成。
keywords:
  - auditd
  - ausearch
  - aureport
  - Linux审计
  - 安全审计
  - 文件监控
  - 合规
---

# Linux 审计系统：auditd 配置与安全事件追踪

## 前言

SELinux 告诉你谁被拒绝了，但 auditd 告诉你**谁做了什么**。作为 Linux 内核级的审计框架，auditd 可以记录文件访问、系统调用、用户登录、命令执行等几乎所有安全相关的事件。

对于等保合规、入侵检测和事后溯源，auditd 是不可替代的工具。

---

## 安装与基础配置

```bash
sudo apt install auditd        # Debian/Ubuntu
sudo dnf install audit         # RHEL/Rocky

sudo systemctl enable auditd --now

# 验证
sudo auditctl -s
# enabled 1
# pid 1234
```

### 配置文件 `/etc/audit/auditd.conf`

```ini
log_file = /var/log/audit/audit.log
log_format = ENRICHED
max_log_file = 100       # 单个日志文件最大 MB
max_log_file_action = ROTATE  # 超过后轮转
num_logs = 10            # 保留 10 个轮转文件
```

---

## 审计规则

### 规则类型

| 类型 | 说明 | 示例 |
| --- | --- | --- |
| **文件监控** | 监控文件的读/写/执行/属性变更 | 监控 `/etc/passwd` |
| **系统调用** | 监控特定系统调用的使用 | 监控 `chmod`、`chown` 调用 |
| **可执行文件** | 监控特定程序被执行 | 谁执行了 `sudo` |

### 文件监控规则

```bash
# 监控 /etc/passwd 的所有写入和属性变更
sudo auditctl -w /etc/passwd -p wa -k passwd_changes

# 监控 /etc/shadow 的读取（-p r）
sudo auditctl -w /etc/shadow -p r -k shadow_read

# 监控 SSH 密钥目录
sudo auditctl -w /home -p rwxa -k home_access

# -p 参数：r=读 w=写 x=执行 a=属性变更
# -k：给规则打标签，方便后续搜索
```

### 系统调用规则

```bash
# 监控所有 chmod 调用
sudo auditctl -a always,exit -F arch=b64 -S chmod -F auid>=1000 -k chmod_calls

# 监控用户创建/删除
sudo auditctl -a always,exit -F arch=b64 -S useradd,userdel -k user_management

# -a always,exit: 总是记录，在系统调用退出时
# -F arch=b64: 64 位架构
# -F auid>=1000: 仅记录普通用户（非系统用户）
```

### 永久规则

`/etc/audit/rules.d/custom.rules`：

```bash
# 关键系统文件
-w /etc/passwd -p wa -k passwd_changes
-w /etc/shadow -p r -k shadow_read
-w /etc/sudoers -p wa -k sudoers_changes
-w /etc/ssh/sshd_config -p wa -k sshd_config

# 关键命令执行
-a always,exit -F arch=b64 -S execve -F euid=0 -k root_commands

# 用户切换
-a always,exit -F arch=b64 -S setuid -F auid>=1000 -k privilege_escalation
```

```bash
# 加载永久规则
sudo auditctl -R /etc/audit/rules.d/custom.rules

# 查看当前生效的规则
sudo auditctl -l
```

---

## 日志分析

### ausearch：搜索审计日志

```bash
# 搜索特定标签的事件
sudo ausearch -k passwd_changes

# 搜索特定用户的操作
sudo ausearch -ua alice

# 搜索特定时间范围
sudo ausearch -ts 07/20/2026 14:00:00 -te 07/20/2026 15:00:00

# 搜索失败的权限事件
sudo ausearch -m USER_LOGIN --success no

# 搜索特定命令的执行
sudo ausearch -c sudo

# 格式化输出（更友好）
sudo ausearch -k passwd_changes --format text
```

### aureport：生成审计报告

```bash
# 登录报告
sudo aureport -l
# Login Report
# ============
# # date       time     auid    host      term  exe         success event
# 1. 07/20/26  14:30:00 alice   192.168.1.100  ssh  /usr/sbin/sshd yes    1234

# 认证报告
sudo aureport -au

# 文件访问报告
sudo aureport -f

# 异常事件报告
sudo aureport --failed

# 汇总统计
sudo aureport --summary
```

### 实时监控

```bash
# 实时输出审计事件
sudo ausearch -i -f /etc/passwd --just-one

# 或 tail audit.log
sudo tail -f /var/log/audit/audit.log
```

---

## 实用审计场景

### 场景 1：谁改了 /etc/passwd？

```bash
sudo auditctl -w /etc/passwd -p wa -k passwd_changes
# ... 过一段时间 ...
sudo ausearch -k passwd_changes -i
# type=CONFIG_CHANGE msg=audit(07/20/2026 14:30:00.123:456) :
# auid=alice ses=1 op=updated_rules
```

### 场景 2：谁在凌晨 3 点登录？

```bash
sudo ausearch -ts 07/20/2026 03:00:00 -te 07/20/2026 04:00:00 \
    -m USER_LOGIN,USER_START -i
```

### 场景 3：sudo 使用记录

```bash
sudo ausearch -c sudo -i | grep -E "comm=sudo|proctitle"
```

---

## 审计日志轮转

`/etc/audit/auditd.conf` 中的 `max_log_file_action=ROTATE` 已启用自动轮转。也可以手动：

```bash
# 手动轮转
sudo service auditd rotate

# 查看轮转后的日志
ls -la /var/log/audit/
```

---

## 性能考量

auditd 的规则越多，对系统性能影响越大：

-   文件监控（`-w`）开销很小
-   系统调用监控（`-a`）开销中等
-   对所有 `execve` 记录开销较大，建议只对 root 或敏感命令开启

```bash
# 查看 auditd 的 CPU 和内存占用
ps -eo pid,comm,%cpu,%mem | grep auditd
```

---

## 总结

auditd 是你部署在服务器上的「安全摄像头」：

1. **文件监控**：`-w /path -p wa -k tag`
2. **系统调用监控**：`-a always,exit -S syscall -k tag`
3. **日志分析**：`ausearch` 搜索、`aureport` 报告
4. **合规**：等保要求的关键文件变更审计，auditd 天然支持

安装后先配置关键文件的监控规则（`/etc/passwd`、`/etc/sudoers`、`/etc/ssh/sshd_config`），这是安全基线的最低要求。 🚀
