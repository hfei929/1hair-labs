---
title: Linux 完整命令参考：按功能分类的速查手册 | 1Hair Labs
description: Linux 命令大全，按文件操作、文本处理、进程管理、网络、磁盘、用户权限、系统信息七大类整理，附带常见使用场景和参数速查。
keywords:
  - Linux命令大全
  - Linux命令速查
  - Linux命令参考
  - 文本处理
  - 进程管理
  - 网络命令
  - 运维
---

# Linux 完整命令参考：按功能分类的速查手册

## 前言

这份命令参考是 [常用命令指南](common-commands.md) 的扩展版。按**功能分类**整理，适合当你需要完成某个特定任务但不记得命令时快速检索。

用法建议：收藏本页，按 `Ctrl+F` 搜索关键词（如「磁盘空间」「端口」「权限」）。

---

## 一、文件与目录操作

| 命令 | 常用参数 | 说明 | 示例 |
| --- | --- | --- | --- |
| `ls` | `-l` 详细 `-a` 隐藏 `-h` 可读 `-t` 按时间 `-S` 按大小 `-r` 倒序 | 列出目录 | `ls -lahS` |
| `cd` | `~` 家目录 `-` 上一次 `..` 上级 | 切换目录 | `cd /var/log` |
| `pwd` | — | 显示当前路径 | `pwd` |
| `mkdir` | `-p` 递归创建 `-m` 指定权限 | 创建目录 | `mkdir -p a/b/c` |
| `rmdir` | `-p` 递归删除空目录 | 删除空目录 | `rmdir empty/` |
| `rm` | `-r` 递归 `-f` 强制 `-i` 确认 | 删除 | `rm -rf /tmp/test/` |
| `cp` | `-r` 递归 `-p` 保留属性 `-a` 归档 | 复制 | `cp -a src/ dst/` |
| `mv` | `-i` 覆盖确认 | 移动/重命名 | `mv old.txt new.txt` |
| `touch` | `-t` 指定时间戳 | 创建文件/更新时戳 | `touch file.txt` |
| `ln` | `-s` 软链接 `-f` 强制 | 创建链接 | `ln -s /opt/bin/app /usr/local/bin/` |
| `find` | `-name` 按名 `-type f/d` 类型 `-size` 大小 `-mtime` 天数 `-exec` 执行 | 搜索文件 | `find . -name "*.log" -mtime +7 -delete` |
| `locate` | `-i` 忽略大小写 `-c` 计数 | 快速定位（需 updatedb） | `locate nginx.conf` |
| `tree` | `-L N` 层级 `-d` 仅目录 | 树形显示 | `tree -L 2 /etc` |
| `stat` | — | 文件详细属性 | `stat file.txt` |
| `file` | — | 识别文件类型 | `file unknown.bin` |

---

## 二、文件查看与文本处理

| 命令 | 常用参数 | 说明 | 示例 |
| --- | --- | --- | --- |
| `cat` | `-n` 行号 `-s` 压缩空行 | 输出文件内容 | `cat /etc/hostname` |
| `less` | `-N` 行号 `-S` 不折行 | 分页查看（q 退出） | `less /var/log/syslog` |
| `head` | `-n N` 前 N 行 | 查看开头 | `head -20 access.log` |
| `tail` | `-n N` 后 N 行 `-f` 实时追踪 `-F` 文件重建追踪 | 查看末尾 | `tail -f /var/log/auth.log` |
| `grep` | `-i` 忽略大小写 `-r` 递归 `-v` 反选 `-n` 行号 `-c` 计数 `-A/B/C N` 上下文 `-E` 扩展正则 | 文本搜索 | `grep -rn "error" /var/log/` |
| `sed` | `-i` 就地修改 `-e` 表达式 `-n` 静默 | 流编辑器 | `sed -i 's/old/new/g' file.txt` |
| `awk` | `-F` 分隔符 `'{print $N}'` | 文本处理语言 | `awk -F: '{print $1,$7}' /etc/passwd` |
| `cut` | `-d` 分隔符 `-f` 字段 `-c` 字符位置 | 按列切分 | `cut -d: -f1 /etc/passwd` |
| `sort` | `-n` 数值 `-r` 倒序 `-k N` 按列 `-u` 去重 `-t` 分隔符 | 排序 | `sort -rn -k2 data.txt` |
| `uniq` | `-c` 计数 `-d` 仅重复 `-u` 仅唯一 | 去重（先 sort） | `sort file \| uniq -c \| sort -rn` |
| `wc` | `-l` 行数 `-w` 单词 `-c` 字节 | 统计 | `ls \| wc -l` |
| `diff` | `-u` 统一格式 `-r` 递归 `-q` 仅报告 | 对比文件 | `diff -u old.conf new.conf` |
| `tr` | `-d` 删除 `-s` 压缩重复 | 字符转换/删除 | `echo "HELLO" \| tr 'A-Z' 'a-z'` |
| `tee` | `-a` 追加 | 分流输出（屏幕+文件） | `./app \| tee output.log` |

---

## 三、进程管理

| 命令 | 常用参数 | 说明 | 示例 |
| --- | --- | --- | --- |
| `ps` | `aux` 所有 `-ef` 完整 `--forest` 树形 `-eo` 自定义列 | 查看进程 | `ps aux --sort=-%mem \| head` |
| `top` | `-p PID` 指定进程 `-u USER` 按用户 `-c` 完整命令 | 动态监控 | `top -p 1234` |
| `htop` | — | 增强版 top | `htop` |
| `kill` | `-9` SIGKILL `-15` SIGTERM `-l` 列出信号 | 发送信号 | `kill -15 1234` |
| `killall` | `-9` 强杀 `-i` 确认 `-w` 等待 | 按名称终止 | `killall -9 nginx` |
| `pkill` | `-f` 匹配命令 `-u` 按用户 | 按模式终止 | `pkill -f "python app.py"` |
| `pgrep` | `-l` 显示名称 `-u` 按用户 `-f` 匹配命令 | 按名查 PID | `pgrep -u www-data` |
| `nice` | `-n N`（-20 最高，19 最低） | 指定优先级启动 | `nice -n 10 ./job` |
| `renice` | `-n N` | 调整运行中进程优先级 | `renice -n -5 -p 1234` |
| `nohup` | `&` 后台 | 忽略挂断，后台运行 | `nohup ./app > log 2>&1 &` |
| `bg` / `fg` / `jobs` | `%N` 任务号 | 后台/前台切换 | `fg %1` |
| `pidstat` | `-u` CPU `-r` 内存 `-d` I/O `1` 每秒 | 进程资源统计 | `pidstat -u 1` |
| `lsof` | `-p PID` `-i :PORT` `-u USER` | 列出打开的文件 | `lsof -i :80` |
| `strace` | `-p PID` `-c` 统计 `-e` 过滤 `-f` 跟踪子进程 | 追踪系统调用 | `strace -c -p 1234` |

---

## 四、网络

| 命令 | 常用参数 | 说明 | 示例 |
| --- | --- | --- | --- |
| `ip` | `addr` `link` `route` `neigh` | 现代网络配置 | `ip -br addr` |
| `ss` | `-t` TCP `-u` UDP `-l` 监听 `-p` 进程 `-n` 数值 | Socket 统计 | `ss -tlnp` |
| `ping` | `-c N` 次数 `-i N` 间隔 `-W N` 超时 | 连通性测试 | `ping -c 4 8.8.8.8` |
| `traceroute` | `-n` 不解析 `-m N` 最大跳数 | 路由追踪 | `traceroute -n 8.8.8.8` |
| `mtr` | `-r` 报告 `-c N` 次数 | 动态路由追踪 | `mtr -r -c 10 8.8.8.8` |
| `dig` | `+short` 简洁 `-x` 反向 `ANY` 全部记录 | DNS 查询 | `dig +short 1hairlabs.cn` |
| `nslookup` | — | 简易 DNS 查询 | `nslookup 1hairlabs.cn` |
| `curl` | `-v` 详细 `-I` 头部 `-o` 下载 `-X` 方法 `-H` 头 `-d` 数据 `-k` 忽略证书 | HTTP 客户端 | `curl -v https://1hairlabs.cn` |
| `wget` | `-O` 输出文件 `-c` 续传 `-r` 递归 | 下载工具 | `wget -c https://example.com/file.iso` |
| `tcpdump` | `-i` 接口 `-n` 不解析 `-w` 写入 `-r` 读取 `port`/`host` 过滤 | 抓包 | `tcpdump -i eth0 port 443 -w cap.pcap` |
| `nc` | `-l` 监听 `-v` 详细 `-z` 端口扫描 `-u` UDP | 网络瑞士军刀 | `nc -zv 192.168.1.1 22` |
| `iptables` | `-L` 列出 `-A` 追加 `-I` 插入 `-D` 删除 `-P` 默认 `-j` 动作 | 防火墙 | `iptables -L -n -v` |
| `ufw` | `enable/disable` `allow/deny` `status` | 简单防火墙 | `ufw allow 22/tcp` |
| `firewall-cmd` | `--list-all` `--add-service` `--add-port` `--reload` | firewalld 管理 | `firewall-cmd --add-service=http --permanent` |

---

## 五、磁盘与文件系统

| 命令 | 常用参数 | 说明 | 示例 |
| --- | --- | --- | --- |
| `df` | `-h` 可读 `-i` inode `-T` 类型 | 磁盘空间 | `df -h` |
| `du` | `-h` 可读 `-s` 汇总 `--max-depth=N` 深度 | 目录空间 | `du -sh /var/log/*` |
| `lsblk` | `-f` 文件系统 `-o` 自定义列 | 列出块设备 | `lsblk -f` |
| `fdisk` | `-l` 列出 | MBR 分区 | `sudo fdisk -l` |
| `gdisk` | `-l` 列出 | GPT 分区 | `sudo gdisk -l /dev/sda` |
| `parted` | `-l` 列出 | 通用分区 | `sudo parted -l` |
| `mkfs.*` | `-t` 类型 | 创建文件系统 | `sudo mkfs.ext4 /dev/sdb1` |
| `mount` | `-t` 类型 `-o` 选项 `-a` 全挂载 | 挂载 | `sudo mount /dev/sdb1 /mnt/data` |
| `umount` | `-f` 强制 `-l` 延迟 | 卸载 | `sudo umount /mnt/data` |
| `fsck` | `-y` 自动修复 `-n` 仅检 `-f` 强制 | 文件系统检查 | `sudo fsck -f /dev/sda1` |
| `tune2fs` | `-l` 查看 `-c`/`-i` 调整 | ext4 参数 | `sudo tune2fs -l /dev/sda1` |
| `dd` | `if=` 输入 `of=` 输出 `bs=` 块 `count=` 数量 `status=progress` | 块复制 | `dd if=img.iso of=/dev/sdb bs=4M status=progress` |
| `sync` | — | 刷缓存到磁盘 | `sync` |

### LVM 命令

| 层 | 查看 | 创建 | 扩展 | 缩减 |
| --- | --- | --- | --- | --- |
| PV | `pvs` `pvdisplay` | `pvcreate` | — | `pvremove` |
| VG | `vgs` `vgdisplay` | `vgcreate` | `vgextend` | `vgreduce` |
| LV | `lvs` `lvdisplay` | `lvcreate` | `lvextend` | `lvreduce` |

---

## 六、用户与权限

| 命令 | 常用参数 | 说明 | 示例 |
| --- | --- | --- | --- |
| `useradd` | `-m` 家目录 `-s` Shell `-G` 附加组 `-u` UID | 添加用户 | `sudo useradd -m -s /bin/bash alice` |
| `usermod` | `-aG` 追加组 `-s` 改 Shell `-L/-U` 锁定/解锁 | 修改用户 | `sudo usermod -aG docker alice` |
| `userdel` | `-r` 删除家目录 | 删除用户 | `sudo userdel -r alice` |
| `passwd` | `-l/-u` 锁定/解锁 `-e` 强制改密 `-S` 状态 | 密码管理 | `sudo passwd alice` |
| `groupadd` / `groupdel` | `-g` 指定 GID | 组管理 | `sudo groupadd developers` |
| `chmod` | 数字 `755/644` 或 `u/g/o ± r/w/x` | 修改权限 | `chmod 755 script.sh` |
| `chown` | `-R` 递归 | 修改所有者 | `chown -R alice:staff /home/alice` |
| `chgrp` | `-R` 递归 | 修改所属组 | `chgrp -R developers code/` |
| `umask` | — | 默认权限掩码 | `umask 022` |
| `getfacl` / `setfacl` | `-m` 修改 `-x` 删除 `-R` 递归 | ACL 控制 | `setfacl -m u:alice:rw file.txt` |
| `sudo` | `-u` 用户 `-i` 登录 Shell `-l` 列出权限 | 提权执行 | `sudo -u www-data whoami` |
| `visudo` | — | 安全编辑 `/etc/sudoers` | `sudo visudo` |
| `id` | — | 查看 UID/GID/组 | `id alice` |
| `who` / `w` / `last` | — | 登录用户/历史 | `last -10` |

---

## 七、系统信息与管理

| 命令 | 常用参数 | 说明 | 示例 |
| --- | --- | --- | --- |
| `uname` | `-a` 全部 `-r` 内核 `-m` 架构 | 系统信息 | `uname -a` |
| `hostnamectl` | `set-hostname` | 主机名管理 | `hostnamectl set-hostname myserver` |
| `uptime` | — | 运行时间+负载 | `uptime` |
| `date` | `+%Y-%m-%d` 格式化 | 日期时间 | `date +"%F %T"` |
| `timedatectl` | `list-timezones` `set-timezone` | 时区管理 | `timedatectl set-timezone Asia/Shanghai` |
| `free` | `-h` 可读 `-s N` 间隔刷新 | 内存查看 | `free -h` |
| `vmstat` | `N M` 每 N 秒 M 次 | 虚拟内存统计 | `vmstat 1 5` |
| `dmesg` | `-T` 可读时间 `--level=err` 级别过滤 | 内核日志 | `dmesg \| tail -20` |
| `journalctl` | `-u UNIT` `-f` 跟踪 `-b` 本次启动 `-p err` 级别 `--since` 时间 | systemd 日志 | `journalctl -u ssh -f` |
| `systemctl` | `start/stop/restart` `enable/disable` `status` `list-units` | 服务管理 | `systemctl status nginx` |
| `sysctl` | `-a` 全部 `-w` 写入 `-p` 加载 | 内核参数 | `sysctl net.ipv4.ip_forward` |
| `lsmod` / `modprobe` | — / `-r` 移除 | 内核模块 | `lsmod \| grep kvm` |
| `lscpu` / `lspci` / `lsusb` | `-v` 详细 | 硬件信息 | `lscpu` |

---

## 八、压缩与归档

| 命令 | 说明 | 压缩 | 解压 |
| --- | --- | --- | --- |
| `tar` | 归档 | `tar -czf a.tar.gz dir/` | `tar -xzf a.tar.gz` |
| `gzip` | .gz | `gzip file` | `gunzip file.gz` |
| `zip` | .zip | `zip -r a.zip dir/` | `unzip a.zip` |
| `xz` | .xz | `xz file` | `unxz file.xz` |
| `zstd` | .zst | `zstd file` | `unzstd file.zst` |

---

## 九、软件包管理速查

| 发行版 | 搜索 | 安装 | 卸载 | 更新 |
| --- | --- | --- | --- | --- |
| **Debian/Ubuntu** | `apt search <pkg>` | `apt install <pkg>` | `apt remove <pkg>` | `apt update && apt upgrade` |
| **RHEL/Rocky 9+** | `dnf search <pkg>` | `dnf install <pkg>` | `dnf remove <pkg>` | `dnf update` |
| **CentOS 7** | `yum search <pkg>` | `yum install <pkg>` | `yum remove <pkg>` | `yum update` |
| **Arch** | `pacman -Ss <pkg>` | `pacman -S <pkg>` | `pacman -R <pkg>` | `pacman -Syu` |
| **Alpine** | `apk search <pkg>` | `apk add <pkg>` | `apk del <pkg>` | `apk update && apk upgrade` |

---

## 参考资源

-   [Linux 常用命令指南](common-commands.md) — 高频命令精选 + 实战示例
-   [软件包管理详解](package-management.md) — apt/yum/dnf 深入使用
-   [系统监控](system-monitoring.md) — top/htop/iostat/vmstat 实战
-   [Shell 基础](../shell/index.md) — 从命令行到脚本编程
