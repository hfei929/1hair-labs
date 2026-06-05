# Linux 常用命令指南

掌握了 Linux 目录结构之后，下一步就是学习最基本的命令。本文为你整理了一份 **高频实用命令清单**，涵盖文件操作、系统管理、网络、权限等常用场景。每个命令都配有简单示例，建议你打开终端边看边练。

!!! tip "提示"
    命令后的 `[ ]` 表示可选参数，`< >` 表示必须提供的参数。实际输入时不要带上尖括号或方括号。

---

## 一、文件与目录操作

这是最基础、最常用的一组命令，用于浏览、创建、复制、移动和删除文件。

| 命令 | 作用 | 示例 |
|------|------|------|
| `ls` | 列出目录内容 | `ls -l`（详细列表）、`ls -a`（显示隐藏文件） |
| `cd` | 切换目录 | `cd /etc`、`cd ..`（上级目录）、`cd ~`（回家目录） |
| `pwd` | 显示当前所在目录的完整路径 | `pwd` |
| `mkdir` | 创建目录 | `mkdir myfolder`、`mkdir -p a/b/c`（创建父目录） |
| `rmdir` | 删除**空目录** | `rmdir emptyfolder` |
| `rm` | 删除文件或目录 | `rm file.txt`、`rm -r myfolder`（递归删除） |
| `cp` | 复制文件或目录 | `cp src.txt dst.txt`、`cp -r dir1 dir2`（复制目录） |
| `mv` | 移动或重命名文件/目录 | `mv old.txt new.txt`（重命名）、`mv file /tmp/`（移动） |
| `touch` | 创建空文件或更新文件时间戳 | `touch newfile.txt` |
| `file` | 查看文件类型 | `file script.sh`（输出：Bourne-Again shell script） |
| `stat` | 显示文件的详细属性（大小、权限、时间） | `stat myfile` |

### 常用组合键（终端内）

| 快捷键 | 作用 |
|--------|------|
| `Tab` | 自动补全命令或路径 |
| `Ctrl + C` | 终止当前运行的命令 |
| `Ctrl + L` | 清屏（相当于 `clear` 命令） |
| `↑` / `↓` | 浏览历史命令 |

---

## 二、查看文件内容

除了用 `cat` 一次性输出整个文件，还有更适合查看大文件的分页命令。

| 命令 | 作用 | 示例 |
|------|------|------|
| `cat` | 输出整个文件内容（适合小文件） | `cat /etc/os-release` |
| `less` | 分页查看大文件（按 `q` 退出） | `less /var/log/syslog` |
| `head` | 查看文件前几行（默认10行） | `head -20 log.txt` |
| `tail` | 查看文件末尾几行 | `tail -f /var/log/syslog`（实时追踪日志） |
| `grep` | 在文件中搜索指定模式（支持正则） | `grep "error" log.txt`、`grep -r "TODO" src/`（递归搜索） |
| `wc` | 统计行数、单词数、字节数 | `wc -l file`（仅行数）、`ls \| wc -l`（统计目录下文件数量） |

---

## 三、权限管理

Linux 的每个文件都有 **读（r）、写（w）、执行（x）** 三组权限，分别对应 **所有者、所属组、其他用户**。

| 命令 | 作用 | 示例 |
|------|------|------|
| `chmod` | 修改文件权限 | `chmod 755 script.sh`（数字法）、`chmod u+x script.sh`（符号法） |
| `chown` | 修改文件所有者和所属组 | `chown alice:staff file.txt` |
| `chgrp` | 仅修改所属组 | `chgrp developers code/` |
| `umask` | 设置新建文件的默认权限掩码 | `umask 022`（新文件权限为 644，目录 755） |

!!! info "权限数字法速记"
    `r=4`，`w=2`，`x=1`。三者相加得到权限值，例如 `7` = rwx，`5` = r-x，`0` = ---。  
    常见数字：`755`（所有者全权，组和其他人读+执行）、`644`（所有者读写，组和其他只读）。

---

## 四、进程管理

操作系统上运行的程序称为**进程**。学习如何查看、终止进程非常重要。

| 命令 | 作用 | 示例 |
|------|------|------|
| `ps` | 查看当前终端下的进程 | `ps aux`（查看所有用户所有进程） |
| `top` | 动态显示系统资源和进程列表（交互式） | 直接输入 `top`，按 `q` 退出 |
| `htop` | 增强版的 `top`（需要安装） | `htop`（颜色丰富，支持鼠标） |
| `kill` | 终止进程 | `kill 1234`（发送 TERM 信号）、`kill -9 1234`（强制杀死） |
| `pkill` | 按名称终止进程 | `pkill firefox` |
| `jobs` | 查看当前终端后台运行的作业 | `jobs -l` |
| `bg` / `fg` | 将作业放到后台/前台运行 | `fg %1` |

---

## 五、系统信息与资源查看

| 命令 | 作用 | 示例 |
|------|------|------|
| `uname` | 显示系统内核信息 | `uname -a`（全部信息） |
| `hostname` | 显示或设置主机名 | `hostname`、`sudo hostname newname` |
| `uptime` | 查看系统运行时间和负载 | `uptime` |
| `free` | 查看内存使用情况 | `free -h`（人类可读） |
| `df` | 查看磁盘分区使用情况 | `df -h` |
| `du` | 查看文件/目录占用磁盘空间 | `du -sh /home`、`du -h --max-depth=1` |
| `whoami` | 显示当前登录的用户名 | `whoami` |
| `w` | 显示当前登录用户及其活动 | `w` |

---

## 六、网络相关命令

| 命令 | 作用 | 示例 |
|------|------|------|
| `ip` | 显示或配置网络接口、路由等（替代 `ifconfig`） | `ip addr show`、`ip route` |
| `ping` | 测试网络连通性 | `ping google.com`（按 `Ctrl+C` 停止） |
| `curl` | 通过 URL 传输数据（HTTP 请求） | `curl ifconfig.me`（获取公网 IP） |
| `wget` | 从网络下载文件 | `wget https://example.com/file.zip` |
| `ss` | 查看网络连接状态（替代 `netstat`） | `ss -tuln`（显示监听端口） |
| `ssh` | 远程登录到另一台机器 | `ssh user@192.168.1.100` |
| `scp` | 通过 SSH 复制文件 | `scp file.txt user@remote:/path/` |
| `nc` | 网络调试工具（发送/接收原始数据） | `nc -zv 8.8.8.8 53`（测试端口是否开放） |

---

## 七、压缩与归档

| 命令 | 作用 | 示例 |
|------|------|------|
| `tar` | 打包/解包 `.tar` 文件 | `tar -czvf archive.tar.gz folder/`（创建）、`tar -xzvf archive.tar.gz`（解压） |
| `gzip` / `gunzip` | 压缩/解压 `.gz` 文件 | `gzip large.log`、`gunzip large.log.gz` |
| `zip` / `unzip` | 处理 `.zip` 文件 | `zip -r my.zip folder/`、`unzip my.zip -d target/` |

!!! note "tar 常用选项"
    - `-c`：创建归档
    - `-x`：解包
    - `-z`：通过 gzip 压缩/解压
    - `-v`：显示详细过程
    - `-f`：指定归档文件名

---

## 八、用户与组管理

需要 `sudo` 权限来执行大部分操作。

| 命令 | 作用 | 示例 |
|------|------|------|
| `useradd` | 创建新用户 | `sudo useradd -m -s /bin/bash alice` |
| `passwd` | 修改用户密码 | `passwd alice` |
| `userdel` | 删除用户 | `sudo userdel -r alice`（同时删除家目录） |
| `groupadd` | 创建新组 | `sudo groupadd developers` |
| `usermod` | 修改用户属性（如添加附加组） | `sudo usermod -aG sudo alice` |
| `id` | 显示用户的 UID、GID 和所属组 | `id alice` |
| `su` | 切换用户 | `su - alice`（切换并加载环境） |
| `sudo` | 以 root 权限执行命令 | `sudo apt update` |

---

## 九、软件包管理（常见发行版）

不同发行版使用不同的包管理器，下表列出常用操作。

| 操作 | Debian/Ubuntu (apt) | RHEL/Fedora (dnf) | Arch (pacman) |
|------|---------------------|-------------------|---------------|
| 更新软件源列表 | `sudo apt update` | `sudo dnf check-update` | `sudo pacman -Sy` |
| 升级所有已安装包 | `sudo apt upgrade` | `sudo dnf upgrade` | `sudo pacman -Su` |
| 搜索软件包 | `apt search keyword` | `dnf search keyword` | `pacman -Ss keyword` |
| 安装软件 | `sudo apt install <pkg>` | `sudo dnf install <pkg>` | `sudo pacman -S <pkg>` |
| 卸载软件 | `sudo apt remove <pkg>` | `sudo dnf remove <pkg>` | `sudo pacman -R <pkg>` |
| 卸载并删除配置文件 | `sudo apt purge <pkg>` | `sudo dnf erase <pkg>` | `sudo pacman -Rn <pkg>` |

!!! tip "记忆技巧"
    日常使用中，你只需要记住 `apt install`、`dnf install`、`pacman -S` 这三个对应关系即可。大部分发行版的包管理器都有类似逻辑。

---

## 十、帮助与文档

当你忘记某个命令的用法时，Linux 提供了非常完善的内置帮助系统。

| 命令 | 作用 | 示例 |
|------|------|------|
| `man` | 查看命令的手册页（最详细） | `man ls` |
| `--help` | 大部分命令支持此选项，输出简要帮助 | `ls --help` |
| `info` | 比 `man` 更详细的文档（某些命令） | `info coreutils` |
| `whatis` | 显示命令的一行简介 | `whatis grep` |
| `which` | 查找命令的可执行文件路径 | `which python` |
| `type` | 判断命令是内置还是外部程序 | `type cd`（输出 `cd is a shell builtin`） |

---

## 总结与实战小练习

建议你将以下练习在虚拟机或 WSL 中动手操作一遍：

1. 使用 `mkdir -p` 创建多级目录 `~/linux_learn/commands`
2. 进入该目录，用 `touch` 创建 `test.txt`
3. 用 `echo "Hello Linux" > test.txt` 写入内容
4. 用 `cat` 和 `less` 分别查看内容
5. 用 `cp` 复制一份为 `test_backup.txt`
6. 用 `grep "Linux" test.txt` 搜索单词
7. 查看当前进程：`ps aux | grep bash`
8. 查看磁盘使用情况：`df -h`
9. 用 `tar` 将整个目录打包压缩：`tar -czvf commands.tar.gz commands/`
10. 解压到另一个位置，验证压缩包正确性。

通过这些练习，你会迅速熟悉 Linux 命令行的工作方式。下一步可以学习 **重定向（`>`、`>>`、`<`）**、**管道（`|`）** 和 **脚本编写**，让命令行真正发挥威力。

---

Happy Hacking!