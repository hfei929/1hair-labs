---
title: LVM 实战：逻辑卷管理从创建到灾难恢复 | 1Hair Labs
description: LVM 完整实战指南，涵盖 PV/VG/LV 创建与管理、在线扩容与缩容、快照备份恢复、条带化与镜像、磁盘替换与迁移、常见故障排查。
keywords:
  - LVM
  - 逻辑卷
  - LVM快照
  - 磁盘扩容
  - 存储管理
  - Linux
  - 运维
---

# LVM 实战：逻辑卷管理从创建到灾难恢复

## 前言

传统磁盘分区最让人头疼的问题是什么？分小了不够用，分大了浪费。LVM（Logical Volume Manager）通过在磁盘和文件系统之间加一层抽象，解决了这个痛点——你可以随时在线扩展或缩减存储空间。

本文从零开始，带你完成 LVM 的创建、扩容、快照、磁盘替换和灾难恢复的全流程。

!!! tip "LVM 公式记忆"
    ```
    PV（物理卷）= 砖块      pvcreate /dev/sdX
    VG（卷组） = 砖堆      vgcreate vg_name /dev/sdX
    LV（逻辑卷）= 从砖堆里分出的一块空间   lvcreate -L 10G -n lv_name vg_name
    ```

---

## 从零创建 LVM

### 场景

服务器有一块新磁盘 `/dev/sdb`（100 GB），需要创建 LVM 管理的存储空间。

### Step 1：创建 PV

```bash
# 将磁盘标记为 LVM 物理卷
sudo pvcreate /dev/sdb

# 查看 PV
sudo pvs
# PV         VG     Fmt  Attr PSize   PFree
# /dev/sdb          lvm2 ---  100.00g 100.00g
```

### Step 2：创建 VG

```bash
sudo vgcreate vg_data /dev/sdb

sudo vgs
# VG      #PV #LV #SN Attr   VSize   VFree
# vg_data   1   0   0 wz--n- 100.00g 100.00g
```

### Step 3：创建 LV

```bash
# 创建一个 30 GB 的逻辑卷
sudo lvcreate -L 30G -n lv_home vg_data

# 或使用剩余空间百分比
sudo lvcreate -l 100%FREE -n lv_data vg_data

sudo lvs
# LV       VG      Attr       LSize  Pool Origin
# lv_home  vg_data -wi-a----- 30.00g
```

### Step 4：格式化并挂载

```bash
sudo mkfs.ext4 /dev/vg_data/lv_home
sudo mkdir /mnt/home
sudo mount /dev/vg_data/lv_home /mnt/home

# 永久挂载（/etc/fstab）
echo '/dev/vg_data/lv_home /mnt/home ext4 defaults 0 2' | sudo tee -a /etc/fstab
```

---

## 在线扩容

### 场景

`lv_home`（30 GB）快满了，VG 还有剩余空间：

```bash
# 检查 VG 剩余空间
sudo vgs

# 扩展 LV（加 20 GB）
sudo lvextend -L +20G /dev/vg_data/lv_home

# 扩展文件系统（ext4）
sudo resize2fs /dev/vg_data/lv_home

# 如果是 XFS
sudo xfs_growfs /mnt/home
```

### 场景：VG 也没空间了

```bash
# 加一块新磁盘 /dev/sdc
sudo pvcreate /dev/sdc
sudo vgextend vg_data /dev/sdc

# 现在 VG 有空间了，继续扩 LV
sudo lvextend -L +50G /dev/vg_data/lv_home
sudo resize2fs /dev/vg_data/lv_home
```

---

## LVM 快照

快照是某个时间点 LV 的只读/可写副本，用于备份和恢复：

### 创建快照

```bash
# 创建 5 GB 的快照（只记录变化量，不需要等于 LV 大小）
sudo lvcreate -L 5G -s -n lv_home_snap /dev/vg_data/lv_home

# 挂载查看快照内容
sudo mkdir /mnt/snap
sudo mount /dev/vg_data/lv_home_snap /mnt/snap
ls /mnt/snap
```

### 用快照恢复

```bash
# 方式 1：将 LV 回滚到快照状态
sudo lvconvert --merge /dev/vg_data/lv_home_snap

# 方式 2：把快照内容 rsync 回去
sudo rsync -av /mnt/snap/ /mnt/home/
```

### 删除快照

```bash
sudo umount /mnt/snap
sudo lvremove /dev/vg_data/lv_home_snap
```

!!! warning "快照不是备份"
    快照依赖原始 LV 存在。如果原始 LV 的数据块损坏，快照也无法恢复。快照适合做**临时保护**（升级前、重大变更前），真正的备份还是要 `rsync`/`tar` 到其他设备。

---

## 缩容（ext4 可用，XFS 不行）

```bash
# ⚠️ 缩容前必须备份！
# 1. 卸载
sudo umount /mnt/home

# 2. 检查文件系统
sudo e2fsck -f /dev/vg_data/lv_home

# 3. 缩小文件系统（比目标小一点更安全）
sudo resize2fs /dev/vg_data/lv_home 20G

# 4. 缩小 LV
sudo lvreduce -L 20G /dev/vg_data/lv_home

# 5. 如果 resize2fs 缩得过小，再扩满
sudo resize2fs /dev/vg_data/lv_home

# 6. 重新挂载
sudo mount /dev/vg_data/lv_home /mnt/home
```

---

## 磁盘替换

### 场景：/dev/sdb 预报故障，需要换到 /dev/sdc

```bash
# 1. 新磁盘加入 VG
sudo pvcreate /dev/sdc
sudo vgextend vg_data /dev/sdc

# 2. 将旧磁盘的数据迁移到新磁盘
sudo pvmove /dev/sdb /dev/sdc

# 3. 从 VG 中移除旧磁盘
sudo vgreduce vg_data /dev/sdb
sudo pvremove /dev/sdb

# 全程在线，无需停机！
```

---

## 条带化（RAID 0）

将数据分散到多块磁盘，提升读写性能：

```bash
# 在 3 块磁盘上创建条带化 LV（64 KB 条带）
sudo lvcreate -L 100G -i 3 -I 64 -n lv_stripe vg_data
# -i 3: 跨 3 块磁盘
# -I 64: 64 KB 条带大小
```

---

## 常用命令速查

| 层 | 查看 | 创建 | 扩展 | 缩减 | 删除 |
| --- | --- | --- | --- | --- | --- |
| PV | `pvs` `pvdisplay` | `pvcreate` | — | — | `pvremove` |
| VG | `vgs` `vgdisplay` | `vgcreate` | `vgextend` | `vgreduce` | `vgremove` |
| LV | `lvs` `lvdisplay` | `lvcreate` | `lvextend` | `lvreduce` | `lvremove` |

---

## 灾难恢复：VG 丢失怎么办？

如果 VG 没有正常显示，可能是 LVM 元数据损坏：

```bash
# 扫描所有磁盘的 LVM 签名
sudo pvscan
sudo vgscan
sudo lvscan

# 查看 LVM 归档备份
ls /etc/lvm/archive/

# 恢复 VG 配置到指定时间
sudo vgcfgrestore -f /etc/lvm/archive/vg_data_00001.vg vg_data

# 激活 VG
sudo vgchange -ay vg_data
```

---

## 总结

LVM 是 Linux 存储管理员最核心的技能之一：

1. **PV → VG → LV**：三层抽象让存储灵活自如
2. **在线扩容**：`lvextend` + `resize2fs`/`xfs_growfs`
3. **快照**：升级前必做，出事能回滚
4. **磁盘替换**：`pvmove` 让数据迁移在线完成
5. **缩容谨慎**：XFS 不支持，ext4 可但需 `umount`

掌握 LVM，你就再也不用为「分区太小」或「磁盘要坏」而焦虑。 🚀
