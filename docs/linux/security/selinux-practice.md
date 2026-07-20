---
title: SELinux 深入实践：从概念到排障 | 1Hair Labs
description: SELinux 实战指南，涵盖三种模式、上下文与类型强制、布尔值调优、audit2allow 生成自定义策略、容器环境适配与常见故障排查。
keywords:
  - SELinux
  - 安全上下文
  - MAC
  - audit2allow
  - Linux安全
  - RHEL
  - 容器安全
---

# SELinux 深入实践：从概念到排障

## 前言

SELinux（Security-Enhanced Linux）是 Linux 内核中的强制访问控制（MAC）机制。与传统的自主访问控制（DAC，即用户/组/权限）不同，SELinux 在内核层面为**每个进程和文件**定义了精细的安全策略——即使 root 权限也不能越界。

很多运维人员的第一反应是 `setenforce 0`（关掉它）。但如果你花一点时间理解它，SELinux 是你最强大的安全盟友。

!!! tip "SELinux 不是「碍事的」"
    你在 `/var/log/nginx` 放了个自定义日志目录，Nginx 报 Permission denied，`chmod 777` 了也不行——这是 SELinux 在保护你。它不是阻碍，是「额外的安全检查」。

---

## 核心概念

### 三种模式

```bash
# 查看当前模式
getenforce

# 临时切换
sudo setenforce 0    # Permissive（只记录不拦截）
sudo setenforce 1    # Enforcing（拦截+记录）

# 永久修改 /etc/selinux/config
SELINUX=enforcing    # or permissive or disabled
```

| 模式 | 行为 | 日志 | 用途 |
| --- | --- | :---: | --- |
| **Enforcing** | 拦截违规操作 | ✓ | **生产环境** |
| **Permissive** | 仅记录不拦截 | ✓ | 调试、策略开发 |
| **Disabled** | 完全关闭 | ✗ | 不推荐 |

!!! warning "Disabled vs Permissive 的重大区别"
    Disabled 模式下系统不会给文件打标签。从 Disabled 切到 Enforcing 需要**重新打标签**（重启时会自动做），而 Permissive → Enforcing 是即时的。

---

### 安全上下文（Context）

每个文件、进程、端口都有一个 SELinux 上下文：

```bash
ls -Z /var/www/html/index.html
# -rw-r--r--. root root system_u:object_r:httpd_sys_content_t:s0 index.html

ps -eZ | grep nginx
# system_u:system_r:httpd_t:s0    1234 ?  00:00:00 nginx
```

上下文的四段格式：

```text
user:role:type:level
```

其中 **`type`** 是最关键的部分——95% 的 SELinux 策略都基于 type 进行控制。

| 常见 type | 含义 |
| --- | --- |
| `httpd_sys_content_t` | Web 服务器可读的内容 |
| `httpd_t` | Web 服务器进程 |
| `ssh_home_t` | SSH 相关的用户文件 |
| `container_file_t` | 容器使用的文件 |

---

## 日常操作

### 修改文件上下文

```bash
# 临时修改（文件系统重打标签后恢复）
sudo chcon -t httpd_sys_content_t /custom/webroot/index.html

# 永久修改（推荐）
sudo semanage fcontext -a -t httpd_sys_content_t "/custom/webroot(/.*)?"
sudo restorecon -Rv /custom/webroot
```

### 查看和修改端口

```bash
# Nginx 想用 8080 端口但 SELinux 不允许
sudo semanage port -l | grep http_port_t
# http_port_t   tcp   80, 81, 443, 488, 8008, 8009, 8443, 9000

# 添加 8080 到允许列表
sudo semanage port -a -t http_port_t -p tcp 8080
```

### 布尔值开关

SELinux 提供了很多「布尔值」开关，用于快速调整预定义策略：

```bash
# 查看所有布尔值
sudo getsebool -a | grep http

# 允许 Nginx 连接外部网络（反向代理需要）
sudo setsebool -P httpd_can_network_connect on

# 允许 Nginx 发送邮件
sudo setsebool -P httpd_can_sendmail on
```

`-P` 表示永久生效（写入策略文件）。

---

## 排障流程

遇到 Permission denied，但 `ls -la` 显示权限正确时——**先怀疑 SELinux**：

### Step 1：确认是否是 SELinux

```bash
# 临时切到 Permissive 测试
sudo setenforce 0
# 重试你的操作 → 如果成功了，就是 SELinux 拦截

# 恢复 Enforcing
sudo setenforce 1
```

### Step 2：查审计日志

```bash
# SELinux 拦截都会记入 audit.log
sudo grep "denied" /var/log/audit/audit.log | tail -20

# 或通过 sealert 友好化查看
sudo sealert -a /var/log/audit/audit.log
```

### Step 3：用 audit2allow 分析

```bash
# 从审计日志中提取被拦截的操作，生成策略建议
sudo grep "denied" /var/log/audit/audit.log | audit2allow -w
# 输出：为什么被拦截的解释

sudo grep "denied" /var/log/audit/audit.log | audit2allow -a
# 输出：允许这些操作需要的策略规则
```

### Step 4：应用自定义策略

```bash
# 生成策略模块
sudo grep "denied" /var/log/audit/audit.log | audit2allow -a -M myapp

# 安装策略
sudo semodule -i myapp.pp

# 验证
sudo semodule -l | grep myapp
```

---

## SELinux 与容器

### Podman/Docker 的 SELinux 集成

容器运行时默认配合 SELinux，每个容器有独立的安全上下文：

```bash
# 挂载宿主目录到容器时，用 :Z 或 :z 标签
docker run -v /host/data:/data:Z nginx
# :Z 为私有标签（仅此容器可访问）
# :z 为共享标签（多个容器可共享）
```

### 排查容器 SELinux 问题

```bash
# 查看容器的 SELinux 上下文
ps -eZ | grep container

# 容器的审计日志可能在宿主机的 audit.log 中
sudo ausearch -m avc -ts recent

# 或通过 journalctl
journalctl -t setroubleshoot
```

---

## SELinux 备份与恢复

```bash
# 备份自定义策略
sudo semodule -l | grep -v "^permissive" > selinux-modules.txt

# 备份文件上下文（fcontext）
sudo semanage fcontext -l > fcontext-backup.txt

# 恢复默认上下文（修复文件系统标签）
sudo restorecon -Rv /
```

---

## 常见问题

### 能不能直接关掉 SELinux？

**不推荐。** SELinux 已经阻止过无数 0-day 漏洞的利用。关掉它等于拆掉了一道防线。遇到问题应该排查、修复策略，而不是关掉。

### 应用程序不兼容 SELinux

1. 先切到 Permissive，确认是 SELinux 的问题
2. 用 `audit2allow` 生成自定义策略
3. 如果是商业软件，联系厂商获取 SELinux 策略包

---

## 总结

SELinux 的投入产出比很高——花几小时学会排障流程，换来的是内核级的持续安全防护：

1. **三种模式**：生产用 Enforcing，调试用 Permissive，永远不用 Disabled
2. **排障三步**：`setenforce 0` 确认 → `audit.log` 找原因 → `audit2allow` 生成策略
3. **日常操作**：`semanage fcontext` + `restorecon` 管理文件标签
4. **容器**：挂载卷用 `:Z` 标签，避免容器突破 SELinux 边界

SELinux 不是你的敌人——它是最勤快的安全卫士。 🚀
