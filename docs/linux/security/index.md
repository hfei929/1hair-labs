# Linux 系统安全：筑牢防线，防患于未然

系统安全是 Linux 运维中**最容易忽视却又最关键**的一环。多数攻击并非来自高深漏洞，而是源于配置疏忽、弱密码、未打补丁等低级问题。本文将从**账户安全、文件权限、防火墙、入侵检测、安全审计**等维度，介绍一套实用的安全加固方案，帮助你构建“纵深防御”体系。

!!! tip "千里之堤，溃于蚁穴"
    我见过太多被入侵的案例，入口往往是一个弱密码的测试账号、一个未禁用的默认用户，或者一个777权限的临时目录。安全不是追求绝对不可破，而是**让攻击成本远大于收益**。以下每一条建议，都来自真实事故的教训。

---

## 一、安全基线：最小权限原则

**最小权限原则**是系统安全的基石：每个用户、进程只拥有完成其任务所必需的最小权限。

### 1.1 账户安全基线

- **删除或锁定不必要的系统账户**：如 `games`、`news`、`uucp`、`lp` 等
  ```bash
  sudo usermod -L games
  # 或彻底删除
  sudo userdel games
  ```
- **禁止 root 直接 SSH 登录**：强制使用普通用户 + `sudo`
  ```bash
  # 编辑 /etc/ssh/sshd_config
  PermitRootLogin no
  # 重启 sshd
  sudo systemctl restart sshd
  ```
- **设置强密码策略**：通过 `/etc/login.defs` 和 `pam_cracklib` 模块
  ```bash
  # 安装 libpam-pwquality（Ubuntu）
  sudo apt install libpam-pwquality
  # 编辑 /etc/pam.d/common-password，添加：
  password requisite pam_pwquality.so retry=3 minlen=8 difok=3 ucredit=-1 lcredit=-1 dcredit=-1
  ```
- **设置账户锁定策略**：多次失败登录后锁定账户（防止暴力破解）
  ```bash
  # 编辑 /etc/pam.d/common-auth，加入：
  auth required pam_tally2.so deny=5 unlock_time=600
  ```

### 1.2 文件权限基线

- **敏感文件权限检查**：
  ```bash
  # /etc/passwd 必须 644，/etc/shadow 必须 600
  sudo chmod 644 /etc/passwd
  sudo chmod 600 /etc/shadow
  # 全局可写目录不能有粘滞位以外的写权限
  find / -type d -perm -0002 -a ! -perm -1000 -ls
  ```
- **SUID/SGID 文件审计**：这些文件容易被提权利用，定期检查
  ```bash
  find / -perm /6000 -type f -ls 2>/dev/null
  # 移除不必要的 SUID（如 mount、umount）
  sudo chmod u-s /bin/mount
  ```

!!! tip "见微知著，防微杜渐"
    我会每周运行一次 `lynis audit system`（一款开源安全审计工具），自动检查上百项配置。它的报告会指出弱点和建议，非常适合批量运维。安装：`sudo apt install lynis`，运行：`sudo lynis audit system`。

---

## 二、防火墙策略：从默认拒绝开始

### 2.1 使用 UFW（Ubuntu 简易防火墙）

```bash
# 默认拒绝所有入站，允许所有出站
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许必要服务
sudo ufw allow 22/tcp          # SSH
sudo ufw allow 80/tcp          # HTTP
sudo ufw allow 443/tcp         # HTTPS

# 限制 SSH 连接频率（防暴力破解）
sudo ufw limit 22/tcp

# 启用
sudo ufw enable
sudo ufw status verbose
```

### 2.2 使用 firewalld（RHEL/Fedora）

```bash
sudo systemctl enable firewalld --now

# 默认拒绝
sudo firewall-cmd --set-default-zone=drop

# 允许指定服务
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload

# 查看活动规则
sudo firewall-cmd --list-all
```

### 2.3 使用 nftables（通用底层）

```bash
# 示例：仅允许 SSH 和 HTTP
sudo nft add table inet filter
sudo nft add chain inet filter input { type filter hook input priority 0\; }
sudo nft add rule inet filter input iif lo accept
sudo nft add rule inet filter input ct state established,related accept
sudo nft add rule inet filter input tcp dport {22,80,443} accept
sudo nft add rule inet filter input drop
sudo nft list ruleset > /etc/nftables.conf
sudo systemctl enable nftables
```

!!! tip "不怕一万，就怕万一"
    配置防火墙时，尤其在远程服务器上，**务必先放行 SSH 端口**，并保留一个已登录的会话备用。我习惯在 `crontab` 里加一条 `*/5 * * * * /usr/bin/systemctl restart sshd` 临时救急（避免修改过程中误关连接）。当然，更安全的是使用 IPMI 或 iDRAC 带外管理。

---

## 三、SELinux / AppArmor：强制访问控制

### 3.1 AppArmor（Debian/Ubuntu 默认）

```bash
# 查看状态
sudo aa-status

# 启用/禁用某个 profile
sudo aa-enforce /etc/apparmor.d/usr.sbin.nginx
sudo aa-complain /etc/apparmor.d/usr.sbin.nginx   # 仅记录违规不拦截

# 生成新 profile（交互式）
sudo aa-genprof /usr/sbin/nginx
```

### 3.2 SELinux（RHEL/Fedora 默认）

```bash
# 查看状态
getenforce
sestatus

# 临时切换模式
sudo setenforce 0   # 宽容模式（仅告警）
sudo setenforce 1   # 强制模式

# 永久配置：编辑 /etc/selinux/config
SELINUX=enforcing

# 查看违规审计日志
sudo ausearch -m avc -ts recent
# 或使用 sealert
sudo yum install setroubleshoot
sudo sealert -a /var/log/audit/audit.log
```

!!! tip "万事开头难"
    很多人一上来就 `setenforce 0` 关掉 SELinux，这等于自废武功。正确的做法：先保持宽容模式运行几天，收集违规日志并用 `audit2allow` 生成自定义策略。例如：
    ```bash
    grep denied /var/log/audit/audit.log | audit2allow -M mypol
    sudo semodule -i mypol.pp
    ```
    理解 SELinux 需要时间，但一旦掌握，你的系统安全等级会高出一个量级。

---

## 四、入侵检测与文件完整性检查

### 4.1 使用 AIDE（高级入侵检测环境）

AIDE 建立文件指纹数据库，定期比对发现被篡改的文件。

```bash
# 安装
sudo apt install aide

# 初始化数据库
sudo aideinit
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# 执行检查
sudo aide --check

# 配置 cron 每天检查
sudo crontab -e
0 2 * * * /usr/bin/aide --check | mail -s "AIDE report" admin@example.com
```

### 4.2 使用 rkhunter / chkrootkit（检测 rootkit）

```bash
sudo apt install rkhunter chkrootkit
sudo rkhunter --check --skip-keypress
sudo chkrootkit
```

### 4.3 监控可疑进程和网络连接

- **定期检查监听端口**：`ss -tuln` 对比基线
- **检查隐藏进程**：`ps auxf` 和 `unhide` 工具
- **检查计划任务**：`crontab -l`、`/etc/crontab`、`/etc/cron.*`

!!! tip "知己知彼，百战不殆"
    我会在每台服务器上部署 `osquery`，将系统状态（进程、网络连接、用户登录）实时上报到中央日志平台。这样即使攻击者清除了本地日志，远端仍有痕迹。此外，`auditd` 是更轻量的选择：可以监控关键文件（如 `/etc/passwd`、`/etc/ssh/sshd_config`）的修改。

---

## 五、日志与审计：让攻击无处遁形

### 5.1 系统日志加固

- **集中式日志**：使用 `rsyslog` 或 `syslog-ng` 将日志发送到远程服务器
  ```bash
  # /etc/rsyslog.conf 添加
  *.* @@192.168.1.100:514   # 通过 TCP 发送
  ```
- **保护日志不被篡改**：使用 `chattr +a /var/log/auth.log` 设置为只能追加
- **日志轮转**：配置 `/etc/logrotate.d/` 确保日志不会填满磁盘

### 5.2 使用 auditd 精细化审计

```bash
# 安装
sudo apt install auditd

# 审计 SSH 配置文件的读写
sudo auditctl -w /etc/ssh/sshd_config -p wa -k ssh_config

# 审计特定用户的所有操作（如 root）
sudo auditctl -a always,exit -S execve -F uid=0

# 查看审计日志
sudo ausearch -k ssh_config

# 永久规则：编辑 /etc/audit/rules.d/audit.rules
```

### 5.3 登录跟踪

- **`last`**：显示成功登录记录（从 `/var/log/wtmp` 读取）
- **`lastb`**：显示失败登录记录（从 `/var/log/btmp` 读取）
- **`journalctl`**：`journalctl _COMM=sshd` 查看 SSH 登录详情

!!! tip "桃李不言，下自成蹊"
    最好的审计不是出了问题再查，而是**实时告警**。我使用 `fail2ban` 自动屏蔽暴力破解 IP，搭配 `logwatch` 每天发送摘要邮件。只需一行安装：`sudo apt install fail2ban logwatch`，配置 `/etc/fail2ban/jail.local` 启用 SSH 防护，效果立竿见影。

---

## 六、安全更新与漏洞管理

### 6.1 自动安全更新

- **Debian/Ubuntu**：
  ```bash
  sudo apt install unattended-upgrades
  sudo dpkg-reconfigure --priority=low unattended-upgrades
  # 配置文件 /etc/apt/apt.conf.d/50unattended-upgrades
  ```
- **RHEL/Fedora**：使用 `dnf-automatic`
  ```bash
  sudo dnf install dnf-automatic
  sudo systemctl enable --now dnf-automatic.timer
  ```

### 6.2 漏洞扫描

- **`lynis`** 不仅做基线检查，也能发现未打补丁的软件包。
- **`vuls`**：一款无代理漏洞扫描器，对比 NVD 数据库。
- **`oscap`**：使用 OpenSCAP 检查系统是否符合安全基线（如 CIS Benchmark）。

```bash
# 安装 oscap
sudo apt install openscap-utils

# 下载并运行 CIS 检查脚本（需要获取对应内容）
oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
```

!!! tip "未雨绸缪，曲突徙薪"
    安全更新是性价比最高的防御手段。我会在测试服务器上开启自动更新，生产环境则每周手动审查后统一应用。要特别注意内核更新后需要重启，可以配合 `needrestart` 工具检查哪些服务需要重启。

---

## 七、其他实用安全措施

### 7.1 SSH 加固

```bash
# /etc/ssh/sshd_config 推荐配置
Protocol 2
PermitRootLogin no
PasswordAuthentication no         # 仅使用密钥登录
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 0
AllowUsers alice bob               # 白名单
DenyUsers badguy
```

### 7.2 禁用未使用的网络服务

```bash
sudo systemctl list-unit-files --type=service --state=enabled
sudo systemctl disable --now rpcbind  # 示例
```

### 7.3 使用 `sudo` 而非 `su`

- 为每个管理员分配独立的 sudo 权限，不要共享 root 密码。
- 使用 `sudo -l` 定期审计。

### 7.4 内核参数加固（`/etc/sysctl.conf`）

```bash
# IP 欺骗防护
net.ipv4.conf.all.rp_filter = 1
# 禁用 ICMP 重定向
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
# 限制 SYN 队列
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_syn_retries = 2
```

!!! tip "曲突徙薪，防患于未然"
    以上所有配置都建议先在本机测试，然后用自动化工具（如 Ansible）批量部署。我维护一个“安全加固剧本”，每新装一台服务器就跑一遍，能省去无数重复劳动和遗漏风险。

---

## 八、实战练习

1. **基线检查**：运行 `lynis audit system`，阅读报告并修复至少 5 项警告。
2. **防火墙实验**：配置 UFW 或 firewalld，仅允许 SSH 和 HTTP，测试从外部无法访问其他端口。
3. **文件完整性**：初始化 AIDE 数据库，然后修改 `/etc/passwd` 文件，再次运行 AIDE 观察差异。
4. **入侵检测**：使用 `chkrootkit` 扫描本机，了解其输出。
5. **审计规则**：设置 auditd 监控 `/etc/ssh/sshd_config`，修改该文件后查看审计日志。
6. **SSH 密钥登录**：生成密钥对，禁用密码登录，验证仅密钥能登录。
7. **fail2ban 模拟**：故意多次输错 SSH 密码，观察 IP 是否被临时封禁（`sudo fail2ban-client status sshd`）。

!!! tip "实践出真知"
    你可以搭建一个蜜罐虚拟机，开放弱密码 SSH，观察攻击者行为（记得快照）。很多攻击脚本会自动尝试常见用户名和密码。通过分析攻击日志，你会深刻理解为什么需要以上所有措施。

---

## 九、总结

Linux 系统安全是一个**纵深防御**体系，没有单点防护能确保万无一失。你需要：

- **减少攻击面**：最小化服务、账户、端口
- **强制访问控制**：SELinux/AppArmor
- **持续监控**：日志、文件完整性、入侵检测
- **及时更新**：自动安全更新 + 漏洞扫描
- **主动防御**：fail2ban、ssh 加固、防火墙

### 三条安全黄金法则

1. **默认拒绝，显式允许**：所有非必须的服务、端口、权限，一律关闭。
2. **假设已经被入侵**：因此需要多层防御，单一突破不影响全局。
3. **自动化但不盲目信任**：定期审计自动化工具的任务，确保没有引入新漏洞。

下一步，你可以学习 **系统故障排除** 与 **应急响应**，将安全理念贯穿到日常运维的每个环节。

Stay secure, stay vigilant!