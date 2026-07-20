---
title: Linux 内核模块管理：lsmod、modprobe 与 DKMS | 1Hair Labs
description: 深入讲解 Linux 内核模块机制，涵盖模块加载/卸载/黑名单、modprobe/modinfo/depmod 命令、内核参数 sysctl、DKMS 动态模块管理、常见驱动问题排查。
keywords:
  - 内核模块
  - modprobe
  - lsmod
  - DKMS
  - sysctl
  - 内核参数
  - 驱动
---

# Linux 内核模块管理：lsmod、modprobe 与 DKMS

## 前言

Linux 内核采用**模块化**设计——大部分功能（驱动、文件系统、网络协议）都可以按需加载或卸载，而不需要重新编译整个内核。这让你可以在不重启的情况下加载新驱动，或卸载有问题的模块。

本文从基本的 `lsmod`/`modprobe` 到 DKMS 动态模块管理，覆盖日常运维中的常见场景。

---

## 模块基础命令

### 查看模块

```bash
# 列出所有已加载模块
lsmod | head

# 查看模块详细信息
modinfo overlay
# filename:     /lib/modules/5.15.0/kernel/fs/overlayfs/overlay.ko
# description:  Overlay filesystem
# depends:
# license:      GPL

# 查看模块依赖关系
modprobe --show-depends kvm
```

### 加载模块

```bash
# 加载模块（推荐——自动处理依赖）
sudo modprobe overlay

# 加载时传递参数
sudo modprobe kvm_intel nested=1

# 底层命令（不处理依赖）
sudo insmod /path/to/module.ko
```

### 卸载模块

```bash
# 卸载模块（推荐）
sudo modprobe -r overlay

# 强制卸载（危险！）
sudo rmmod -f module_name
```

### 开机自动加载

```bash
# /etc/modules-load.d/my-modules.conf
overlay
br_netfilter
kvm
```

---

## 模块参数设置

```bash
# 查看模块当前参数
cat /sys/module/kvm_intel/parameters/nested
# N → 未启用嵌套虚拟化

# 查看模块所有参数
modinfo -p kvm_intel

# 运行中设置（/sys 接口）
echo 1 | sudo tee /sys/module/kvm_intel/parameters/nested

# 永久设置（modprobe.d）
# /etc/modprobe.d/kvm.conf
options kvm_intel nested=1
```

---

## 模块依赖与 depmod

模块之间有依赖关系——`overlay` 依赖 `overlayfs`，加载 `overlay` 时内核自动先加载依赖。

```bash
# 重建模块依赖数据库（安装新内核/新模块后）
sudo depmod -a

# 数据库位置
ls /lib/modules/$(uname -r)/modules.*
```

---

## 黑名单：禁止加载模块

当你不希望某个模块自动加载时（例如用厂商驱动替代开源驱动）：

```bash
# /etc/modprobe.d/blacklist.conf
blacklist nouveau        # 禁止开源 NVIDIA 驱动
blacklist pcspkr         # 禁止蜂鸣器
```

---

## 内核参数（sysctl）

区别于模块参数，sysctl 控制内核的**运行时行为**：

```bash
# 查看所有参数
sudo sysctl -a | head

# 查看特定参数
sysctl net.ipv4.ip_forward
# net.ipv4.ip_forward = 0

# 临时修改
sudo sysctl -w net.ipv4.ip_forward=1

# 永久修改
# /etc/sysctl.d/99-custom.conf
net.ipv4.ip_forward = 1
vm.swappiness = 1

# 应用配置
sudo sysctl -p /etc/sysctl.d/99-custom.conf
```

### 常用内核参数速查

| 参数 | 推荐值 | 说明 |
| --- | :---: | --- |
| `net.ipv4.ip_forward` | `1`（路由器/容器） | 启用 IP 转发 |
| `vm.swappiness` | `1`（数据库） | Swap 倾向 |
| `kernel.pid_max` | `4194304` | 最大 PID |
| `fs.file-max` | `2097152` | 最大文件句柄 |
| `net.core.somaxconn` | `1024` | TCP 监听队列长度 |
| `vm.overcommit_memory` | `1`（数据库推荐） | 内存过量分配策略 |

---

## DKMS：动态内核模块支持

DKMS 让你安装的第三方模块在**内核升级后自动重新编译**：

```bash
# 安装 DKMS
sudo apt install dkms

# 查看已注册的 DKMS 模块
dkms status
# virtualbox/7.0.0, 5.15.0-91-generic, x86_64: installed

# 添加一个 DKMS 模块
sudo dkms add -m mydriver -v 1.0

# 为当前内核编译
sudo dkms build -m mydriver -v 1.0

# 安装
sudo dkms install -m mydriver -v 1.0
```

典型使用场景：VirtualBox 驱动、NVIDIA 驱动、ZFS——这些模块不在内核树中，需要随内核升级而重建。

---

## 常见问题

### 模块加载失败：`modprobe: FATAL: Module not found`

```bash
# 1. 确认模块是否存在
find /lib/modules/$(uname -r) -name "xxx.ko"

# 2. 更新依赖数据库
sudo depmod -a

# 3. 如果是编译的模块，需要先安装到正确路径
sudo make modules_install
```

### 模块被使用中无法卸载

```bash
# 查看哪些进程在用
lsmod | grep module_name
# Used by 列显示依赖此模块的其他模块和计数

# 先卸载依赖方
sudo modprobe -r dependent_module
sudo modprobe -r target_module
```

---

## 总结

内核模块管理虽不频繁，但关键时刻很关键：

1. **`modprobe` 优于 `insmod`**——自动处理依赖
2. **`/etc/modules-load.d/`** 管理开机加载
3. **`/etc/modprobe.d/`** 管理模块参数和黑名单
4. **`sysctl`** 管理内核运行时行为（不是模块参数！）
5. **DKMS** 让你不再畏惧内核升级

内核模块是 Linux 灵活性的核心体现——理解它，你就理解了 Linux 如何支持海量硬件。🚀
