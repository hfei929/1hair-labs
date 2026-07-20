---
title: Shell 基础入门：从命令行到脚本编程 | 1Hair Labs
description: 面向新手的 Shell 完整入门教程，涵盖 Bash/Zsh 环境、变量与 PATH、重定向与管道、脚本编写（变量/条件/循环/函数）、配置文件与别名，从零掌握 Linux 命令行。
keywords:
  - Shell
  - Bash
  - Zsh
  - Linux命令行
  - Shell脚本
  - 环境变量
  - 管道
  - 重定向
  - 新手教程
---

# Shell 基础入门：从命令行到脚本编程

## 前言

如果你刚刚安装好 Linux 系统，打开终端看到的就是一个黑底白字的窗口，上面显示着一行类似这样的文字：

```text
user@hostname:~$
```

这就是 **Shell**——你和 Linux 操作系统之间最直接的对话通道。

很多人对命令行的第一印象是「难学」「记不住」「不如鼠标点」。但当你真正掌握它之后，你会发现命令行是最高效的计算机操作方式——它不需要图形界面、可以批量处理、可以写成脚本自动化运行，是运维、开发和 DevOps 工程师的日常核心工具。

本文从零开始，系统讲解 Shell 的核心概念和实用技能，帮助你从「害怕命令行」变成「离不开命令行」。

!!! info "这篇文章适合谁？"
    -   刚安装好 Linux、第一次打开终端的新手
    -   会几条命令但想系统理解 Shell 机制的进阶者
    -   需要编写 Shell 脚本进行自动化运维的开发者

---

## 什么是 Shell？

### 一句话理解

**Shell 是一个命令解释器**——你输入命令，它负责理解并交给操作系统执行。

```mermaid
flowchart LR
    U[用户] -->|输入命令| S[Shell]
    S -->|翻译并执行| K[操作系统内核]
    K -->|返回结果| S
    S -->|显示输出| U
```

### Shell 不是终端

很多新手把「终端窗口」和「Shell」混为一谈。这里有一个重要的区分：

| 概念 | 是什么 | 类比 |
| --- | --- | --- |
| **终端（Terminal）** | 一个**窗口程序**，提供输入输出的界面 | 聊天软件的窗口 |
| **Shell** | 窗口里运行的**命令解释器**，负责解析和执行命令 | 聊天窗口里和你对话的人 |

打开 GNOME Terminal、iTerm2、Windows Terminal——这些是**终端模拟器**。终端里跑着的 `bash` 或 `zsh` 才是 Shell。

---

## 常见的 Shell

Linux 世界中有多种 Shell 实现，各有千秋：

| Shell | 全称 | 特点 | 常见位置 |
| --- | --- | --- | --- |
| **Bash** | Bourne Again Shell | Linux 默认 Shell，兼容性最好，社区资料最多 | `/bin/bash` |
| **Zsh** | Z Shell | Bash 的超集，插件丰富（oh-my-zsh），macOS 默认 | `/bin/zsh` |
| **Fish** | Friendly Interactive Shell | 开箱即用的语法高亮和自动补全，但语法不兼容 Bash | `/usr/bin/fish` |
| **Dash** | Debian Almquist Shell | 极致轻量，用于系统脚本（`/bin/sh` 常指向它） | `/bin/dash` |
| **Sh** | Bourne Shell | Unix 原始 Shell，现代系统 `/bin/sh` 通常是指向 Bash 或 Dash 的符号链接 | `/bin/sh` |

!!! tip "我该用哪个？"
    新手建议从 **Bash** 开始——它是 Linux 世界的事实标准，所有服务器上都有，学会后终身受用。macOS 用户如果喜欢更好的自动补全体验，Zsh 是很自然的选择。**注意**：如果写脚本给其他人用，尽量用 Bash 语法，避免 Zsh/Fish 特有语法。

查看当前 Shell：

```bash
echo $SHELL
```

查看系统上安装的所有 Shell：

```bash
cat /etc/shells
```

---

## Shell 提示符解读

当你打开终端，看到的第一行文字就是**提示符（Prompt）**。以最常见的 Bash 提示符为例：

```text
user@hostname:~$
```

| 部分 | 含义 |
| --- | --- |
| `user` | 当前登录用户名 |
| `@` | 分隔符 |
| `hostname` | 主机名 |
| `:` | 分隔符 |
| `~` | 当前所在目录（`~` 代表用户的家目录，如 `/home/user`） |
| `$` | **关键**：`$` 表示普通用户，`#` 表示 root 超级用户 |

!!! warning "看到 `#` 要警惕"
    如果提示符结尾是 `#` 而不是 `$`，说明你当前是 **root 用户**（超级管理员）。root 可以删除任何文件、修改任何配置，操作失误可能导致系统瘫痪。**用完 root 权限后尽快 `exit` 回到普通用户**。

---

## 命令的基本结构

Shell 命令遵循一个统一的格式：

```text
命令 [选项] [参数]
```

```bash
ls -l /home
# │  │   │
# │  │   └── 参数：要操作的目标
# │  └────── 选项：调整命令行为（-l 表示详细列表）
# └───────── 命令：要执行的程序
```

### 选项的两种写法

| 风格 | 示例 | 说明 |
| --- | --- | --- |
| **短选项** | `ls -l -a` 或 `ls -la` | 单个字母，用 `-` 前缀，可以合并 |
| **长选项** | `ls --all` 或 `ls --human-readable` | 完整单词，用 `--` 前缀，不能合并 |

```bash
# 以下三条命令效果相同
ls -l -a -h
ls -lah
ls --all --human-readable -l
```

---

## 环境变量

### 什么是环境变量？

环境变量是 Shell 在内存中维护的键值对，用于存储配置信息和运行时状态。程序可以读取这些变量来决定自身行为。

```bash
# 查看所有环境变量
env

# 查看单个变量
echo $HOME    # /home/user
echo $USER    # user
echo $PATH    # /usr/local/bin:/usr/bin:/bin:...
```

### 最重要的环境变量

| 变量 | 含义 | 典型值 |
| --- | --- | --- |
| `$HOME` | 当前用户的家目录 | `/home/user` |
| `$USER` | 当前用户名 | `user` |
| `$PATH` | 可执行文件的搜索路径 | `/usr/local/bin:/usr/bin:/bin` |
| `$SHELL` | 当前使用的 Shell | `/bin/bash` |
| `$PWD` | 当前工作目录 | `/home/user/Documents` |
| `$OLDPWD` | 上一次所在目录 | `/home/user` |
| `$?` | 上一条命令的退出码（0=成功） | `0` |

### PATH 详解

`PATH` 是理解 Shell 工作机制的关键。当你在终端输入 `ls`，Shell 怎么知道 `ls` 这个程序在哪里？

它按 `PATH` 中列出的目录**依次查找**：

```bash
echo $PATH
# /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

查找顺序是从左到右。找到第一个匹配的程序就执行。这也是为什么：

-   自定义脚本放在 `/usr/local/bin` 会优先于系统自带的同名命令
-   如果 `PATH` 配置错误，会出现「command not found」

!!! warning "当前目录不在 PATH 中"
    出于安全原因，Linux 默认不把当前目录 `.` 加入 PATH。这意味着如果你自己写了一个脚本 `myscript.sh`，不能直接输入 `myscript.sh`——必须用 `./myscript.sh` 明确指定路径。

### 设置环境变量

```bash
# 临时设置（仅当前会话有效）
export MY_VAR="hello"

# 永久设置（写入 ~/.bashrc）
echo 'export MY_VAR="hello"' >> ~/.bashrc
source ~/.bashrc   # 立即生效
```

---

## 别名（Alias）

别名让你给长命令起一个简短的名字，减少重复输入：

```bash
# 查看所有别名
alias

# 设置别名
alias ll='ls -lah'
alias gs='git status'
alias k='kubectl'
alias please='sudo $(history -p !!)'  # 忘记加 sudo 时的补救神器
```

永久生效：

```bash
echo "alias ll='ls -lah'" >> ~/.bashrc
source ~/.bashrc
```

!!! tip "常用别名推荐"
    ```bash
    alias ll='ls -lah'
    alias la='ls -A'
    alias ..='cd ..'
    alias ...='cd ../..'
    alias grep='grep --color=auto'
    alias df='df -h'
    alias free='free -h'
    ```

---

## 输入输出重定向

Linux 中每个程序默认有三个「流」：

| 流 | 编号 | 默认目标 | 含义 |
| --- | :---: | --- | --- |
| **stdin** | 0 | 键盘 | 标准输入 |
| **stdout** | 1 | 屏幕 | 标准输出 |
| **stderr** | 2 | 屏幕 | 标准错误 |

### 重定向操作符

```bash
# 将标准输出写入文件（覆盖）
command > file.txt

# 将标准输出追加到文件
command >> file.txt

# 将标准错误重定向
command 2> error.log

# 将标准输出和标准错误都写入同一个文件
command > all.log 2>&1

# 丢弃所有输出（静默运行）
command > /dev/null 2>&1

# 从文件读取输入
command < input.txt
```

### 实际场景

```bash
# 只记录正常日志，错误显示在屏幕
./myapp > app.log

# 后台运行，完全静默
nohup ./myapp > /dev/null 2>&1 &

# 将错误也追加到日志
./myapp >> app.log 2>&1
```

---

## 管道（Pipe）

管道 `|` 是 Shell 最强大的特性之一——它将**前一个命令的输出**作为**后一个命令的输入**：

```bash
command1 | command2 | command3
```

### 经典管道组合

```bash
# 统计当前目录下有多少文件
ls | wc -l

# 查看占用磁盘最多的 10 个目录
du -sh * | sort -rh | head -10

# 查找包含 "error" 的进程
ps aux | grep error

# 查看 Nginx 访问量最高的 5 个 IP
cat /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -5

# 查看监听 80 端口的进程
ss -tlnp | grep :80
```

!!! tip "管道 vs 重定向"
    -   **管道 `|`**：把一个命令的输出送给另一个命令（命令之间传递）
    -   **重定向 `>`**：把输出写入文件（命令到文件）
    
    两者可以组合使用：
    ```bash
    ps aux | grep nginx > nginx_processes.txt
    ```

---

## Shell 脚本基础

当你需要反复执行一系列命令时，把它们写成脚本：

### 第一个脚本

创建 `hello.sh`：

```bash
#!/bin/bash
# 上面这行叫 shebang，告诉系统用什么解释器执行这个脚本

echo "Hello, 1HairLabs!"
echo "当前时间: $(date)"
echo "当前用户: $USER"
echo "当前目录: $PWD"
```

运行：

```bash
chmod +x hello.sh   # 赋予执行权限
./hello.sh          # 运行
```

!!! info "Shebang 是什么？"
    `#!/bin/bash` 告诉系统：用 `/bin/bash` 来解释执行本文件。你也可以用 `#!/usr/bin/env bash` 来提高可移植性（自动在 PATH 中找 bash）。

---

### 变量

```bash
#!/bin/bash

# 定义变量（等号两边不能有空格！）
name="1HairLabs"
count=42

# 使用变量
echo "名称: $name"
echo "数量: $count"

# 命令替换：把命令的输出赋给变量
today=$(date +%Y-%m-%d)
files_count=$(ls | wc -l)

echo "今天日期: $today"
echo "当前目录文件数: $files_count"

# 只读变量
readonly PI=3.14159

# 特殊变量
echo "脚本名: $0"
echo "第一个参数: $1"
echo "第二个参数: $2"
echo "所有参数: $@"
echo "参数个数: $#"
echo "当前进程 PID: $$"
```

---

### 条件判断

```bash
#!/bin/bash

# if 语句
age=18

if [ "$age" -ge 18 ]; then
    echo "成年人"
elif [ "$age" -ge 13 ]; then
    echo "青少年"
else
    echo "儿童"
fi

# 常用条件测试
# 数值比较：-eq(等于) -ne(不等于) -gt(大于) -lt(小于) -ge(≥) -le(≤)
# 字符串比较：= != -z(为空) -n(非空)
# 文件测试：-f(是文件) -d(是目录) -x(可执行) -r(可读) -w(可写)

if [ -f "/etc/passwd" ]; then
    echo "passwd 文件存在"
fi

if [ -d "/tmp" ] && [ -w "/tmp" ]; then
    echo "/tmp 目录存在且可写"
fi

# 现代写法：[[ ]] 比 [ ] 更安全（Bash 专属）
if [[ -f "/etc/hosts" && -r "/etc/hosts" ]]; then
    echo "hosts 文件存在且可读"
fi
```

---

### 循环

```bash
#!/bin/bash

# for 循环：遍历列表
for i in 1 2 3 4 5; do
    echo "数字: $i"
done

# for 循环：遍历范围
for i in {1..5}; do
    echo "第 $i 次"
done

# for 循环：遍历文件
for file in *.txt; do
    echo "处理文件: $file"
done

# while 循环
counter=1
while [ "$counter" -le 5 ]; do
    echo "计数器: $counter"
    counter=$((counter + 1))
done

# 逐行读取文件
while IFS= read -r line; do
    echo "行内容: $line"
done < /etc/hostname
```

---

### 函数

```bash
#!/bin/bash

# 定义函数
greet() {
    local name="$1"        # local 限制变量作用域
    echo "你好, $name!"
}

# 调用函数
greet "1HairLabs"
greet "World"

# 带返回值的函数
is_even() {
    if [ $(($1 % 2)) -eq 0 ]; then
        return 0    # 成功（偶数）
    else
        return 1    # 失败（奇数）
    fi
}

if is_even 42; then
    echo "42 是偶数"
fi
```

---

## Shell 配置文件

Shell 启动时会自动加载一系列配置文件。不同场景加载的文件不同：

| 文件 | 加载时机 | 用途 |
| --- | --- | --- |
| `~/.bashrc` | 每次打开交互式终端 | 别名、函数、PS1 提示符、PATH |
| `~/.profile` | 登录 Shell（SSH 登录、控制台登录） | 环境变量、启动程序 |
| `~/.bash_profile` | 登录 Shell（仅 Bash） | 如果存在，`~/.profile` 被忽略 |
| `~/.bash_logout` | 退出登录 Shell 时 | 清理临时文件 |
| `/etc/bash.bashrc` | 全局，所有用户生效 | 系统级默认配置 |

!!! tip "修改后如何生效？"
    ```bash
    source ~/.bashrc   # 或 . ~/.bashrc
    ```
    修改配置文件后执行此命令，无需重新登录即可生效。

### 典型的 `~/.bashrc` 内容

```bash
# ~/.bashrc 示例

# 别名
alias ll='ls -lah'
alias ..='cd ..'
alias grep='grep --color=auto'

# PATH 扩展
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"

# 提示符定制
export PS1='\u@\h:\w\$ '
# \u=用户名, \h=主机名, \w=当前目录

# 历史记录设置
export HISTSIZE=10000          # 内存中保存的命令数
export HISTFILESIZE=20000      # 文件中保存的命令数
export HISTCONTROL=ignoredups  # 忽略连续重复命令
```

---

## 实用技巧

### 命令行快捷键

| 快捷键 | 作用 |
| --- | --- |
| `Ctrl + A` | 跳到行首 |
| `Ctrl + E` | 跳到行尾 |
| `Ctrl + U` | 删除光标前所有内容 |
| `Ctrl + K` | 删除光标后所有内容 |
| `Ctrl + W` | 删除光标前一个单词 |
| `Ctrl + R` | **反向搜索历史命令**（最常用！） |
| `Ctrl + L` | 清屏 |
| `!!` | 重复上一条命令 |
| `!$` | 上一条命令的最后一个参数 |

### 命令历史

```bash
history              # 查看历史命令
history | grep ssh   # 搜索历史中的 ssh 命令
!42                  # 执行历史中第 42 条命令
!!                   # 重复上一条命令
sudo !!              # 用 sudo 重新执行上一条命令
```

### 前后台切换

```bash
# 后台运行（命令后加 &）
./long_task.sh &

# 查看后台任务
jobs

# 把后台任务调到前台
fg

# 把正在运行的任务放到后台
# Ctrl + Z（暂停）→ bg（放入后台继续运行）

# 断开会话后仍继续运行
nohup ./long_task.sh &
# 或使用 tmux/screen（更推荐）
```

---

## 常见问题

### `command not found`

最常见的新手错误。原因通常是：

1.  **命令未安装**：`apt install <package>` 安装
2.  **PATH 不包含该程序**：用绝对路径或添加到 PATH
3.  **拼写错误**：Linux 区分大小写，`LS` ≠ `ls`
4.  **脚本没加执行权限**：`chmod +x script.sh`

```bash
# 查看命令在哪里
which python3
# 或
type python3
```

---

### `Permission denied`

```bash
# 原因 1：没有执行权限
chmod +x script.sh

# 原因 2：需要 root 权限
sudo ./script.sh

# 原因 3：文件系统挂载为 noexec
mount | grep noexec
```

---

### 脚本变量中的空格陷阱

```bash
# 错误：等号两边有空格
name = "hello"    # Bash 会把 name 当作命令执行，= 和 "hello" 当作参数

# 正确：等号两边不能有空格
name="hello"

# 错误：变量赋值中的空格导致单词拆分
files=*.txt       # 如果当前目录有 a.txt b.txt，files 的值是 "a.txt b.txt"

# 正确：使用引号或数组
files="*.txt"     # 保持字面值
```

---

## 总结

Shell 是 Linux 世界中最值得投入时间学习的技能之一。本文覆盖了从基础到脚本的完整知识链：

1. **Shell 本质**：命令解释器，用户与内核之间的桥梁
2. **环境变量**：存储配置信息，`PATH` 决定命令查找路径
3. **重定向与管道**：控制输入输出流，串联命令协同工作
4. **脚本编程**：变量、条件、循环、函数——让重复工作自动化
5. **配置文件**：`~/.bashrc` 是你个性化定制的起点

最有效的学习方式不是死记硬背——打开终端，每条命令都亲自敲一遍。当你能用一行管道命令解决别人需要点 20 次鼠标的问题时，你就真正掌握了 Shell。 🚀
