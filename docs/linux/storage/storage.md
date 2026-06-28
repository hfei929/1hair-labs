# Linux 存储管理：磁盘、分区、文件系统与挂载

存储管理是 Linux 系统运维的核心技能之一。无论你是在为服务器添加新硬盘，还是想重新规划分区布局，理解 Linux 的存储体系都是必须跨过的一道门槛。

本文将从最基础的磁盘概念讲起，逐步深入到分区、文件系统创建、挂载、交换空间管理，以及 LVM 和磁盘配额等实用技术。

---

## 一、存储管理的基本概念

在动手操作之前，先理清几个关键术语：

| 术语 | 含义 |
|------|------|
| **物理磁盘** | 实际的硬件设备，如 `/dev/sda`、`/dev/nvme0n1` |
| **分区** | 将一个物理磁盘划分成多个逻辑区域，如 `/dev/sda1`、`/dev/sda2` |
| **文件系统** | 用于组织和管理文件的数据结构，如 `ext4`、`XFS`、`btrfs` |
| **挂载** | 将一个文件系统附着到 Linux 目录树中的某个目录（挂载点）的过程 |
| **交换空间** | 磁盘上的一块区域，当作“慢速内存”使用，用于缓解物理内存压力 |

!!! tip "设备命名规则"
    - IDE 硬盘：`/dev/hda`、`/dev/hdb`（已淘汰）
    - SATA / SCSI / USB 硬盘：`/dev/sda`、`/dev/sdb`...
    - NVMe SSD：`/dev/nvme0n1`（第一个 NVMe 设备）、`/dev/nvme0n1p1`（第一个分区）
    - 虚拟磁盘（虚拟机）：`/dev/vda`（virtio 驱动）

---

## 二、查看存储设备与磁盘分区

### 查看磁盘和分区

| 命令 | 作用 | 示例 |
|------|------|------|
| `lsblk` | 以树形结构列出所有块设备（推荐） | `lsblk`、`lsblk -f`（显示文件系统） |
| `fdisk -l` | 显示磁盘分区表（需要 root 权限） | `sudo fdisk -l` |
| `parted -l` | 列出分区表（支持大磁盘 GPT） | `sudo parted -l` |
| `df -h` | 查看已挂载文件系统的使用情况 | `df -h`、`df -i`（查看 inode 使用） |
| `du -sh` | 查看目录或文件占用的磁盘空间 | `du -sh /home` |

```bash
# 快速查看磁盘和分区
lsblk
# 输出示例：
# NAME          MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
# sda             8:0    0   100G  0 disk
# ├─sda1          8:1    0    1G  0 part /boot
# ├─sda2          8:2    0   50G  0 part /
# └─sda3          8:3    0   49G  0 part /home
```

---

## 三、磁盘分区

分区是将一个大磁盘划分成多个独立区域的过程。Linux 中常用的分区工具有 `fdisk`（MBR 分区表）和 `gdisk`（GPT 分区表），以及 `parted`（通用）。

### 1. MBR 与 GPT 对比

| 特性 | MBR（传统） | GPT（现代） |
|------|-------------|-------------|
| 最大磁盘容量 | 2 TiB | 9.4 ZiB（理论上） |
| 最大分区数 | 4 个主分区（或 3 主 + 1 扩展，扩展内可多个逻辑分区） | 通常 128 个（可配置） |
| 启动方式 | BIOS + Legacy 模式 | UEFI 模式（也兼容 BIOS + GPT，需特殊设置） |
| 工具 | `fdisk` | `gdisk`、`parted` |

### 2. 使用 `fdisk` 分区（示例：/dev/sdb）

```bash
# 进入交互式分区界面
sudo fdisk /dev/sdb

# 常用 fdisk 内部命令
# m - 显示帮助
# p - 打印当前分区表
# n - 新建分区
# d - 删除分区
# w - 写入并退出
# q - 不保存退出
```

**操作步骤示例**（创建一个 10GB 的主分区）：
1. `sudo fdisk /dev/sdb`
2. 输入 `n` → 选择 `p`（主分区） → 分区号默认 1 → 起始扇区默认 → 输入 `+10G`
3. 输入 `w` 保存并退出
4. 运行 `sudo partprobe` 或重启系统，让内核重新读取分区表

### 3. 使用 `parted` 分区（支持 GPT）

```bash
# 交互式 parted
sudo parted /dev/sdc

# 常用命令
mklabel gpt          # 创建 GPT 分区表
mkpart primary ext4 0% 20G   # 创建 20GB 的 ext4 分区
print                # 显示分区
quit                 # 退出
```

---

## 四、创建文件系统

分区完成后，需要在其上创建文件系统（即“格式化”）。

### 常用文件系统类型

| 文件系统 | 特点 | 适用场景 |
|----------|------|----------|
| `ext4` | Linux 默认，成熟稳定，性能良好 | 通用桌面、服务器 |
| `XFS` | 大文件和高性能，支持在线扩容 | 大型文件服务器、数据中心 |
| `btrfs` | 支持快照、压缩、子卷等高级功能 | 需要数据管理功能的场景 |
| `swap` | 交换分区专用 | 虚拟内存 |

### 格式化命令

```bash
# 格式化为 ext4
sudo mkfs.ext4 /dev/sdb1

# 格式化为 XFS（需要先安装 xfsprogs）
sudo mkfs.xfs /dev/sdb1

# 创建交换分区（先设置分区类型为 82，然后格式化）
sudo mkswap /dev/sdb2
```

!!! tip "文件系统标签"
    可以为文件系统添加标签，方便识别：
    ```bash
    sudo mkfs.ext4 -L mydata /dev/sdb1
    sudo e2label /dev/sdb1 mydata   # 修改标签
    ```

---

## 五、挂载文件系统

创建好文件系统后，需要将其“挂载”到一个目录上，才能访问其中的内容。

### 临时挂载

```bash
# 创建一个挂载点目录
sudo mkdir /mnt/data

# 挂载 /dev/sdb1 到 /mnt/data
sudo mount /dev/sdb1 /mnt/data

# 查看挂载结果
df -h /mnt/data

# 卸载
sudo umount /mnt/data
# 或者 umount /dev/sdb1
```

### 永久挂载（/etc/fstab）

编辑 `/etc/fstab` 文件，让系统启动时自动挂载。

**fstab 每一行的格式**：
```
<设备>   <挂载点>   <文件系统类型>   <挂载选项>   <dump>   <pass>
```

**示例**：
```bash
# 使用设备名（不推荐，设备名可能变化）
/dev/sdb1  /mnt/data  ext4  defaults  0  2

# 使用 UUID（推荐，更稳定）
UUID=123e4567-e89b-12d3-a456-426614174000  /mnt/data  ext4  defaults  0  2
```

**如何获取 UUID**：
```bash
sudo blkid
# 或
lsblk -f
```

**挂载选项常见值**：
- `defaults`：默认选项（rw、suid、dev、exec、auto、nouser、async）
- `noatime`：不更新文件访问时间，提升性能
- `ro`：只读挂载

**测试 fstab 是否正确**：
```bash
sudo mount -a   # 挂载所有 fstab 中尚未挂载的设备
```

!!! warning "重要提醒"
    修改 `/etc/fstab` 前务必备份（`sudo cp /etc/fstab /etc/fstab.bak`）。错误的 fstab 可能导致系统无法正常启动。

---

## 六、交换空间（Swap）

当物理内存不足时，系统会将不常用的内存页写入交换分区或交换文件。

### 查看当前 Swap 使用情况
```bash
swapon --show
free -h
```

### 创建交换分区
```bash
# 1. 分区（类型设为 Linux swap，代码 82）
sudo fdisk /dev/sdc   # 创建分区，类型 82

# 2. 格式化为 swap
sudo mkswap /dev/sdc1

# 3. 启用
sudo swapon /dev/sdc1

# 4. 永久启用（添加到 /etc/fstab）
UUID=xxxx  none  swap  sw  0  0
```

### 创建交换文件（无需重新分区）
```bash
# 创建一个 2GB 的交换文件
sudo fallocate -l 2G /swapfile
# 或使用 dd: sudo dd if=/dev/zero of=/swapfile bs=1M count=2048

# 设置正确权限
sudo chmod 600 /swapfile

# 格式化为 swap
sudo mkswap /swapfile

# 启用
sudo swapon /swapfile

# 永久启用（添加到 /etc/fstab）
/swapfile  none  swap  sw  0  0
```

!!! tip "Swap 大小建议"
    - 内存 < 2GB：Swap  = 内存的 2 倍
    - 内存 2-8GB：Swap = 与内存相同
    - 内存 > 8GB：Swap = 4-8GB（取决于是否需要休眠）
    - 休眠到磁盘：Swap >= 物理内存

---

## 七、逻辑卷管理（LVM）

LVM 是 Linux 下的一个高级存储管理工具，它允许你动态调整分区大小、跨多个磁盘创建逻辑卷等。

### LVM 基本概念

| 组件 | 说明 |
|------|------|
| **物理卷（PV）** | 可以是整个磁盘、一个分区，LVM 的底层单元 |
| **卷组（VG）** | 由一个或多个 PV 组成，相当于一个存储池 |
| **逻辑卷（LV）** | 从 VG 中划分出来的“虚拟分区”，可在其上创建文件系统 |

### LVM 常用操作流程

```bash
# 1. 准备物理卷（例如 /dev/sdb1 和 /dev/sdc1）
sudo pvcreate /dev/sdb1 /dev/sdc1

# 2. 创建卷组（名为 myvg）
sudo vgcreate myvg /dev/sdb1 /dev/sdc1

# 3. 创建逻辑卷（大小 10G，名为 mylv）
sudo lvcreate -L 10G -n mylv myvg

# 4. 在逻辑卷上创建文件系统
sudo mkfs.ext4 /dev/myvg/mylv

# 5. 挂载
sudo mkdir /mnt/lvm
sudo mount /dev/myvg/mylv /mnt/lvm
```

### 动态扩展逻辑卷

```bash
# 查看当前 VG 剩余空间
sudo vgdisplay myvg

# 扩展逻辑卷（增加 5G）
sudo lvextend -L +5G /dev/myvg/mylv

# 扩展文件系统（ext4 用 resize2fs，XFS 用 xfs_growfs）
sudo resize2fs /dev/myvg/mylv

# 对于 XFS
sudo xfs_growfs /mnt/lvm
```

!!! info "LVM 快照"
    LVM 支持创建快照，用于备份或测试：
    ```bash
    sudo lvcreate -L 1G -s -n mysnap /dev/myvg/mylv
    ```

---

## 八、磁盘配额（Quota）

配额用于限制用户或组在文件系统上可使用的磁盘空间和文件数量（inode）。

### 启用配额支持（以 /home 分区为例）

1. **确保文件系统挂载时启用配额选项**：在 `/etc/fstab` 中添加 `usrquota`、`grpquota`
   ```
   UUID=xxx  /home  ext4  defaults,usrquota,grpquota  0  2
   ```

2. **重新挂载文件系统**
   ```bash
   sudo mount -o remount /home
   ```

3. **创建配额数据库文件**
   ```bash
   sudo quotacheck -cug /home
   sudo quotacheck -avug
   ```

4. **启用配额**
   ```bash
   sudo quotaon /home
   ```

### 设置配额限制

```bash
# 编辑用户 alice 的配额
sudo edquota -u alice

# 设置硬限制和软限制（单位：KB 和 inode 个数）
# blocks soft hard  inodes soft hard
```

### 查看配额

```bash
# 用户自查
quota -v

# 管理员查看所有用户的配额
sudo repquota -a
```

---

## 九、磁盘监控与维护

### 常用监控工具

| 命令 | 作用 |
|------|------|
| `iostat` | 查看 CPU 和磁盘 I/O 统计（需安装 `sysstat`） |
| `iotop` | 实时显示每个进程的 I/O 使用情况 |
| `df -h` | 文件系统空间使用 |
| `du -sh *` | 目录占用 |
| `ncdu` | 交互式磁盘使用分析（需安装） |
| `lsblk` | 查看设备和分区布局 |

### 检查文件系统一致性

```bash
# 检查 ext4 文件系统（需要先卸载）
sudo umount /dev/sdb1
sudo fsck.ext4 -f /dev/sdb1

# 检查 XFS（通常不需要手动运行，xfs_repair 会修复）
sudo xfs_repair /dev/sdb1
```

### SSD TRIM 优化

对于 SSD 磁盘，定期执行 TRIM 可以延长寿命并保持性能。

```bash
# 手动 TRIM
sudo fstrim -v /

# 启用自动 TRIM（systemd 服务会自动运行）
sudo systemctl enable fstrim.timer
sudo systemctl start fstrim.timer
```

---

## 十、实战练习

建议你在虚拟机中增加一块虚拟硬盘（如 20GB），然后完成以下操作：

1. 使用 `lsblk` 识别新硬盘（如 `/dev/sdb`）
2. 用 `fdisk` 或 `parted` 创建一个主分区 `/dev/sdb1`，大小为 5GB
3. 在 `/dev/sdb1` 上创建 `ext4` 文件系统，标签为 `DATA`
4. 创建挂载点 `/mnt/data`，并临时挂载该分区
5. 在 `/mnt/data` 下创建一个测试文件，然后卸载
6. 将分区设置为开机自动挂载（编辑 `/etc/fstab`，使用 UUID）
7. 重启或执行 `mount -a`，验证自动挂载成功
8. 创建一个 2GB 的交换文件并启用，用 `free -h` 验证
9. （选做）创建 LVM：将一个分区或磁盘设为 PV，创建 VG 和 LV，挂载并动态扩展大小
10. 查看磁盘使用情况：`df -h`、`du -sh /home`

通过这些练习，你将掌握 Linux 存储管理中最实用、最核心的操作。

---

## 总结

Linux 存储管理的知识体系可以概括为：

- **磁盘 → 分区 → 文件系统 → 挂载** 是基本链路
- 使用 `lsblk`、`df`、`du` 随时监控存储状态
- 通过 `/etc/fstab` 实现永久挂载
- 交换空间可以用分区或文件形式
- LVM 提供了极大的灵活性（动态调整、跨磁盘）
- 配额和 I/O 监控是管理多用户环境的关键

掌握这些技能后，你就能从容应对日常的磁盘扩容、新硬盘添加、故障排查等任务。下一步可以学习 **RAID（磁盘阵列）** 和 **网络文件系统（NFS、Samba）**。

Happy Storing!
