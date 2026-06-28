# Linux 用户与权限管理：用户、组与文件安全

在 Linux 这样的多用户操作系统中，**用户**和**权限**是安全模型的基石。每个文件、目录、进程都属于某个用户和组，访问权限由读、写、执行三组标记控制。本文将从用户/组的管理、文件权限的精细设置，到特殊权限和访问控制列表（ACL），为你建立一套完整的权限知识体系。

!!! tip "💡 经验之谈"
    很多初学者会忽略“默认权限掩码”的影响。在一个团队协作的服务器上，如果发现新建文件总是权限不够，请先检查 `umask`。我曾经在一次项目交付中因为忽略了 umask，导致同事无法修改我生成的配置文件——事后只用一个 `umask 002` 就解决了整个团队的协作问题。

---

## 一、Linux 的用户类型

Linux 中的用户分为三类：

| 类型 | 说明 | UID 范围 | 示例 |
|------|------|----------|------|
| **超级用户（root）** | 拥有系统最高权限，UID 为 0 | 0 | `root` |
| **系统用户** | 运行后台服务或守护进程，通常不能登录 | 1-999（不同发行版有差异） | `daemon`、`sshd`、`nobody` |
| **普通用户** | 日常使用的用户，权限受限 | 1000-60000 | `alice`、`bob` |

查看当前登录用户：`whoami`、`w`、`id`。

!!! tip "💡 经验之谈"
    创建系统用户时，很多人直接 `useradd -r`。我的习惯是：对于自建服务（如 Nginx、PostgreSQL）专用账户，一定要加上 `-M -s /sbin/nologin`，防止它被意外登录。曾经因为一个 Tomcat 账户被我错误地赋予了 bash，导致被入侵者通过弱口令提权——血的教训。

---

## 二、用户管理基础命令

### 创建用户

```bash
# 基本创建（会自动创建家目录 /home/username，使用默认 shell）
sudo useradd -m alice

# 指定 shell 和附加组
sudo useradd -m -s /bin/bash -G sudo,developers alice

# 创建后设置密码（必须）
sudo passwd alice
```

!!! tip “useradd 常用选项”
    | 选项 | 作用 |
    |------|------|
    | `-m` | 创建家目录（强烈建议） |
    | `-s` | 指定登录 shell（如 `/bin/bash`） |
    | `-G` | 指定附加组（逗号分隔） |
    | `-u` | 指定 UID |
    | `-c` | 添加注释（如用户全名） |

### 修改用户

```bash
# 修改用户家目录
sudo usermod -d /new/home alice

# 修改登录 shell
sudo usermod -s /bin/zsh alice

# 将用户加入或移出附加组（注意 -a 选项表示追加，否则会覆盖）
sudo usermod -aG docker alice      # 追加到 docker 组
sudo usermod -G "" alice           # 清空所有附加组

# 锁定/解锁用户（禁止登录）
sudo usermod -L alice
sudo usermod -U alice
```

### 删除用户

```bash
# 仅删除用户，保留家目录和邮件池
sudo userdel alice

# 同时删除家目录和邮件池
sudo userdel -r alice
```

### 查看用户信息

| 命令 | 作用 |
|------|------|
| `id alice` | 显示 UID、GID 和所属组 |
| `who` | 当前登录的用户列表 |
| `last` | 最近登录记录 |
| `finger alice` | 用户详细信息（需安装 `finger`） |

!!! tip "💡 经验之谈"
    我曾长期困惑为什么删除用户后同名目录还在。后来才意识到 `userdel` 默认不删除家目录，需要 `-r` 参数。现在我会习惯先 `tar` 备份旧家目录再删除，以防遗留重要数据。另外，对于临时账号，建议用 `useradd -e 2025-12-31 alice` 设置到期时间，避免僵尸账号。

---

## 三、组管理基础

组用于将多个用户归类，方便统一分配权限。每个用户都有一个**主组**（创建用户时默认创建的同名组），并可加入多个**附加组**。

### 创建和删除组

```bash
# 创建组
sudo groupadd developers
sudo groupadd -g 2000 designers   # 指定 GID

# 删除组（组内不能有用户为主组）
sudo groupdel developers
```

### 修改用户所属组

```bash
# 修改用户的主组
sudo usermod -g developers alice

# 添加/移除附加组
sudo gpasswd -a alice designers   # 添加到 designers 组
sudo gpasswd -d alice designers   # 从 designers 组移除
```

### 查看组信息

```bash
# 列出所有组
getent group

# 查看某个用户所属的组
groups alice

# 查看某个组包含的用户
getent group developers
```

!!! tip "💡 经验之谈"
    团队协作时，我的铁律：**永远不要修改现有用户的主组**。主组一旦改动，该用户已创建的文件权限可能全部错乱。正确的做法是使用附加组（`-aG`），并通过 ACL 或目录 SetGID 来确保新文件继承正确的组。我曾在一个项目里直接改了十几个人的主组，结果共享目录权限爆炸，花了半天才恢复。

---

## 四、文件权限基础

执行 `ls -l` 时，第一列形如 `-rwxr-xr--`，这就是文件权限。

### 权限位解析

```
-  rwx  r-x  r--
^  ^^^  ^^^  ^^^
|   |    |    └── 其他用户权限 (other)
|   |    └─────── 组用户权限 (group)
|   └──────────── 所有者权限 (user)
└──────────────── 文件类型 (- 普通文件, d 目录, l 符号链接, etc.)
```

每个权限组中的字母含义：

| 字母 | 含义（对文件） | 含义（对目录） |
|------|----------------|----------------|
| `r` | 可读取文件内容 | 可列出目录内容（需 `x` 配合） |
| `w` | 可修改文件内容 | 可在目录中创建/删除/重命名文件（需 `x` 配合） |
| `x` | 可执行文件（脚本/二进制） | 可进入目录（`cd`） |

### 修改权限：`chmod`

数字法（每位权限值 = r(4)+w(2)+x(1)）：

```bash
chmod 755 script.sh   # 所有者 rwx(7)，组 r-x(5)，其他 r-x(5)
chmod 644 file.txt    # 所有者 rw-，组 r--，其他 r--
chmod 600 secret.txt  # 所有者 rw-，其他人无任何权限
```

符号法：

```bash
chmod u+x file        # 所有者增加执行权限
chmod g-w file        # 组用户去掉写权限
chmod o=r file        # 其他用户权限设为只读
chmod a-x file        # 所有用户去掉执行权限
```

### 修改所有者与组：`chown` / `chgrp`

```bash
# 更改文件所有者
sudo chown alice file.txt

# 同时更改所有者和组
sudo chown alice:developers file.txt

# 仅更改所属组
sudo chgrp developers file.txt

# 递归修改目录及其内容
sudo chown -R alice:developers /home/alice/project
```

!!! tip "💡 经验之谈"
    递归 `chown -R` 非常危险！我曾经在 `/` 目录下不小心执行了 `chown -R alice:alice /`（漏了当前路径的点），系统几乎瘫痪。从那时起，我养成了两个习惯：1) 永远用绝对路径或先 `cd` 到目标目录再 `chown -R .`；2) 对于关键目录（如 `/etc`、`/var`）从不批量递归修改。另外，如果你看到文件权限变成 `-rwS---`（大S），说明 setuid 位设置在了不可执行文件上，这是错误的，应该用 `chmod u-s` 修复。

---

## 五、目录特殊权限

目录比文件多两个特殊权限：**粘滞位（Sticky Bit）** 和 **SetGID**。

### 粘滞位（Sticky Bit）

**作用**：在具有粘滞位的目录中，用户只能删除属于自己的文件，即使该目录对所有用户可写。

典型场景：`/tmp` 目录（权限 `drwxrwxrwt`）。最后一位 `t` 表示粘滞位。

```bash
# 设置粘滞位
sudo chmod +t /shared

# 示例效果：用户 alice 无法删除 /shared 下 bob 创建的文件
```

### SetGID（目录）

**作用**：在设置了 SetGID 的目录中，**新建的文件和子目录**自动继承该目录的所属组，而不是继承创建者的主组。

```bash
# 设置 SetGID（目录权限中显示为 s）
sudo chmod g+s /project
```

### SetUID（仅限文件，且通常是可执行文件）

作用：用户执行该文件时，临时获得文件所有者的权限（典型例子：`/usr/bin/passwd` 所有者 root，普通用户执行时能修改 `/etc/shadow`）。

```bash
# 设置 SetUID（显示为 s，文件所有者执行位）
sudo chmod u+s /path/to/program
```

!!! warning “安全提醒”
    SetUID 非常强大，设置不当可能导致权限提升漏洞。尽量避免在自定义脚本上设置 SetUID。

!!! tip "💡 经验之谈"
    我最喜欢用的组合是 `chmod 2770 shared_dir`（SetGID + 权限 770）。这样团队目录下任何人新建的文件都自动继承组权限，不会出现“我传的文件你看不到”的尴尬。另外，粘滞位不仅适用于 `/tmp`，在公司内部的“公共上传区”也非常有用——允许所有人写，但不允许互相删除。我曾用这个特性为测试团队搭建了一个共享目录，再也没有人误删过同事的测试报告。

---

## 六、访问控制列表（ACL）

当传统的 “所有者-组-其他” 权限不够用时，ACL 允许为多个用户或组单独设置权限。

### 启用 ACL

大多数 Linux 文件系统（ext4、XFS）默认支持 ACL。如果不确定，可以检查挂载选项：

```bash
tune2fs -l /dev/sda1 | grep "Default mount options"
```

### 常用 ACL 命令

| 命令 | 作用 |
|------|------|
| `getfacl file` | 查看文件的 ACL 列表 |
| `setfacl -m u:alice:rwx file` | 为用户 alice 添加权限 |
| `setfacl -m g:developers:r-x file` | 为组 developers 添加权限 |
| `setfacl -x u:alice file` | 移除用户 alice 的 ACL 条目 |
| `setfacl -b file` | 清除所有 ACL 条目 |

### 示例

```bash
# 为目录 /data 设置默认 ACL，使得以后新增的文件自动给 alice 读权限
setfacl -m d:u:alice:r /data

# 查看结果
getfacl /data
```

!!! tip "💡 经验之谈"
    ACL 虽好，但不要滥用。我曾在一个大型项目中，每个目录都设了五六条 ACL，最后导致 `getfacl` 输出长达一屏，维护起来简直是噩梦。经验是：优先用普通权限 + 组 + SetGID；只有跨组、特殊个人权限才用 ACL。另外，`setfacl` 默认会覆盖原有 ACL，记得用 `-m` 而不是 `-s`（完全设置）。还有一个坑：`cp` 默认不保留 ACL，除非用 `cp --preserve=all`。

---

## 七、密码与账户策略

### 密码管理

```bash
# 修改自己的密码
passwd

# 管理员修改他人密码
sudo passwd alice

# 强制用户下次登录时修改密码
sudo chage -d 0 alice

# 查看账户过期信息
sudo chage -l alice
```

### 账户锁定与解锁

```bash
# 锁定账户（禁止登录）
sudo passwd -l alice

# 解锁
sudo passwd -u alice

# 使用 usermod 也可以
sudo usermod -L alice
```

### 禁用登录方式

- 设置 shell 为 `/sbin/nologin`：用户无法登录，但可以执行某些服务
- 设置 shell 为 `/bin/false`：直接拒绝登录
- 锁定密码：`passwd -l`

!!! tip "💡 经验之谈"
    日常运维中，不要随便删除离职员工账号。我习惯先锁定（`usermod -L`）并将 shell 改为 `/sbin/nologin`，保留家目录和文件半年。这样既能阻止登录，又不会影响已经归属到其他用户的文件（因为 UID 被释放会导致文件变成数字 ID，难以追溯）。另外，`/etc/shadow` 中第二个字段为 `!` 或 `*` 表示账户被锁定——检查这个比猜密码锁定状态更可靠。

---

## 八、sudo 权限管理

普通用户执行特权命令通常使用 `sudo`。`/etc/sudoers` 文件定义了谁可以执行什么命令。

### 编辑 sudoers（必须使用 visudo）

```bash
sudo visudo
```

### 常用配置行

```bash
# 允许 alice 执行所有命令
alice ALL=(ALL) ALL

# 允许 developers 组执行所有命令
%developers ALL=(ALL) ALL

# 允许 bob 执行特定命令，无需密码
bob ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx

# 允许 alice 以某个用户身份执行命令
alice ALL=(postgres) /usr/bin/psql
```

### 查看当前用户的 sudo 权限

```bash
sudo -l
```

!!! tip "💡 经验之谈"
    `NOPASSWD` 很方便，但只应用在非交互式脚本或绝对安全的命令上。我见过有人写 `bob ALL=(ALL) NOPASSWD: ALL` —— 这等同于给了 bob 完整的 root 权限且不记录密码，完全绕过了 sudo 的审计价值。更实用的写法是限制命令并加上日志：`Defaults log_output`。另外，如果多个用户需要相同的 sudo 权限，最好定义一个 `Cmnd_Alias` 和 `User_Alias`，而不是复制多行。这样后期维护省心很多。比如：
    ```
    User_Alias DEVOPS = alice, bob, carol
    Cmnd_Alias SERVICE_CMDS = /bin/systemctl start, /bin/systemctl stop, /bin/systemctl restart
    DEVOPS ALL=(ALL) NOPASSWD: SERVICE_CMDS
    ```

---

## 九、实战练习

建议在虚拟机或 WSL 中创建测试用户和组，完成以下操作：

1. 创建两个用户 `alice` 和 `bob`，并设置密码
2. 创建一个组 `project`，将 alice 加入该组（作为附加组），bob 的主组设置为 `project`
3. 在 `/tmp` 下创建目录 `teamwork`，使该目录的所属组为 `project`，权限为 `2770`（SetGID + 读写执行给所有者和组）
4. 分别用 alice 和 bob 登录，在 `/tmp/teamwork` 中创建文件，观察文件的所属组是否为 `project`
5. 设置粘滞位：`sudo chmod +t /tmp/teamwork`，然后用 bob 尝试删除 alice 创建的文件，观察结果
6. 使用 ACL：`setfacl -m u:bob:r-- /tmp/teamwork/alice-file`，查看 `getfacl`
7. 修改 `/etc/sudoers`（通过 `visudo`），让 alice 可以执行 `systemctl restart cron` 而无需密码
8. 用 `sudo -l` 验证权限
9. 锁定 bob 账户，尝试登录，确认失败后解锁

!!! tip "🔔 提示"
    如果是在生产环境的真实机器上练习，请务必使用 `--dry-run` 类选项（部分命令没有，则先备份）。尤其是 `chown`、`chmod` 递归操作，建议先用 `ls -lR` 查看当前状态，想清楚再执行。另一个实用技巧：在修改 `/etc/sudoers` 之前，打开另一个 root shell 窗口作为“救生索”，万一语法错误导致 sudo 无法使用，还能从另一个窗口修复。

---

## 十、总结与最佳实践

用户与权限管理是 Linux 系统安全的起点。核心要点：

- **用户**有 UID 分类（root、系统用户、普通用户）
- **组**用于批量分配权限，每个用户有一个主组和多个附加组
- **文件权限**由 r、w、x 组成，可通过 `chmod`、`chown` 修改
- **目录特殊权限**（粘滞位、SetGID）和多用户协作密切相关
- **ACL** 提供更精细的控制，但需适量使用
- **sudo** 管理特权命令的执行权限，应遵循最小权限原则

### 三条黄金实践法则

1. **先锁定，后删除**：离职或临时账号永远先 `usermod -L`、改 shell，观察一两周再决定是否删除。
2. **权限越简单越好**：能用普通权限+组解决就不用 ACL，能用 ACL 就不用特殊权限（SetUID）。
3. **记录每一次权限变更**：在团队 wiki 或变更日志里记录 `chown` / `chmod` / `setfacl` 的详细命令及原因，三个月后你一定会感谢当时的自己。

掌握这些知识，你就能安全、规范地管理多用户环境。

Happy Learning & Safe Admin!
