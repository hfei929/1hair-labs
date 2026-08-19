---
title: LVM 进阶实战：快照、缩容、换盘与灾难恢复 | 1Hair Labs
description: LVM 进阶实战指南，涵盖快照备份恢复、缩容、磁盘替换与迁移、条带化、常用命令速查与灾难恢复。PV/VG/LV 创建与在线扩容请见《磁盘挂载与 LVM 配置》。
keywords:
  - LVM
  - 逻辑卷
  - LVM快照
  - 磁盘扩容
  - 存储管理
  - Linux
  - 运维
---

# LVM 进阶实战：快照、缩容、换盘与灾难恢复

## 前言

传统磁盘分区最让人头疼的问题是什么？分小了不够用，分大了浪费。LVM（Logical Volume Manager）通过在磁盘和文件系统之间加一层抽象，解决了这个痛点——你可以随时在线扩展或缩减存储空间。

!!! note "本文是 LVM 进阶篇"
    PV/VG/LV 创建、格式化挂载、fstab 持久化、在线扩容这些**基础操作**，已经拆到了 [磁盘挂载与 LVM 配置](disk-mount-lvm.md)。本文聚焦进阶场景：**快照、缩容、磁盘替换、条带化与灾难恢复**。下文示例默认已有一个 `vg_data` 卷组和 `lv_home` 逻辑卷。

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

进阶场景的要点：

1. **快照**：升级前必做，出事能回滚，但它不是备份
2. **磁盘替换**：`pvmove` 让数据迁移在线完成，无需停机
3. **缩容谨慎**：XFS 不支持，ext4 可但需 `umount`，操作前必须备份
4. **条带化**：`lvcreate -i` 提升吞吐，但不提供冗余
5. **灾难恢复**：`vgcfgrestore` + `vgchange -ay` 找回丢失的 VG

---

## 相关阅读

- [磁盘挂载与 LVM 配置](disk-mount-lvm.md) — PV/VG/LV 创建、格式化挂载、在线扩容的基础实操
- [Linux 存储管理](storage.md) — 分区表、swap 与磁盘配额
- [Linux 文件系统原理](filesystem-internals.md) — inode、ext4 与 XFS 内部机制
