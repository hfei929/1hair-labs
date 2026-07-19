---
title: CentOS 8 部署教程：EOL 后系统安装与 Yum 源修复 | 1Hair Labs
description: 详细讲解 CentOS 8 在 VMware 虚拟机中的安装步骤，以及 EOL（生命周期终止）后 Yum 源失效的完整修复方案，包含阿里云 Vault 归档源配置。
keywords:
  - CentOS 8
  - CentOS安装教程
  - CentOS EOL
  - Yum源修复
  - Vault源
  - VMware虚拟机
  - Linux教程
---

# CentOS 8 部署教程：EOL 后系统安装与 Yum 源修复

## 前言

CentOS 8 于 2021 年 12 月 31 日正式 **EOL（End of Life，生命周期终止）**，官方镜像源已下线。但这并不意味着 CentOS 8 没有学习价值——许多企业内网仍运行着 CentOS 8 系统，掌握其安装与源修复方法依然是运维工程师的必备技能。

!!! warning "CentOS 8 已停止维护"
    CentOS 8 不再接收安全更新和 Bug 修复。对于**生产环境**，强烈建议迁移到 [Rocky Linux 9.x](rocky-linux-9.md) 或 [Debian 13](debian-13.md)。本文主要面向**学习和实验场景**。

本教程将带领大家完成两件事：
1.  在 VMware Workstation 中安装 CentOS 8
2.  修复 EOL 后失效的 Yum 源，恢复软件包安装能力

---

## CentOS 8 版本说明

| 版本 | 状态 | 说明 |
| --- | --- | --- |
| **CentOS Linux 8** | EOL（2021.12） | 传统 CentOS，已停更 |
| **CentOS Stream 8** | 维护中（至 2024.5） | RHEL 的上游滚动版 |
| **CentOS Stream 9** | 活跃维护 | 当前主流 Stream 版本 |

本教程安装的是 **CentOS Linux 8**（传统版本），这也是大多数教程和资料中提到的 CentOS 8。

---

## 部署前准备

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
| --- | --- | --- |
| CPU | 1 Core | 2 Core |
| 内存 | 2 GB | 4 GB |
| 磁盘 | 20 GB | 50 GB |
| 网络 | 可联网 | 桥接模式 |

### 软件准备

| 软件 | 说明 | 下载地址 |
| --- | --- | --- |
| **VMware Workstation Pro 17+** | 宿主机虚拟化软件 | [VMware 官网](https://www.vmware.com/products/workstation-pro.html) 或 [网盘地址（提取码：MBKT）](https://pan.quark.cn/s/14503c2e7051) |
| **CentOS 8 ISO** | 安装镜像 | [阿里云镜像站](https://mirrors.aliyun.com/centos-vault/8.5.2111/isos/x86_64/) |

!!! tip "下载最新版 CentOS 8"
    虽然已 EOL，但 ISO 文件仍在各大镜像站保留。推荐下载 CentOS 8 最后一个版本（8.5.2111）：
    ```text
    CentOS-8.5.2111-x86_64-dvd1.iso
    ```

---

## 创建虚拟机

VMware Workstation 创建虚拟机的通用步骤请参考 [Ubuntu 22.04 部署教程](ubuntu-22.04.md#创建虚拟机)。以下仅列出 CentOS 8 特有设置：

### 客户机操作系统

```text
Linux → Red Hat Enterprise Linux 8 64-bit
```

![选择操作系统](../../assets/images/deployment/linux/centos8-选择操作系统.png)

### 虚拟机规格

```text
CPU：2 Core
内存：4096 MB
磁盘：50 GB
网络：桥接模式
```

---

## 安装 CentOS 8

### 启动安装

挂载 ISO → 开启虚拟机 → 选择 **「Install CentOS Linux 8」**。

![安装界面](../../assets/images/deployment/linux/centos8-安装界面.png)

---

### 语言选择

推荐：

```text
English (United States)
```

原因：英文环境更利于查看报错日志和搜索解决方案。

![语言选择](../../assets/images/deployment/linux/centos8-语言选择.png)

---

### 安装信息摘要

进入安装信息摘要（Installation Summary）页面，需要依次配置带图标的项目：

![安装摘要](../../assets/images/deployment/linux/centos8-安装摘要.png)

---

### 磁盘分区

选择 **「Installation Destination」** → 选中磁盘 → **Storage Configuration** 选择 **「Automatic」**（自动分区）。

对于学习环境，自动分区完全够用。如需手动分区，选择 `Custom`。

![磁盘分区](../../assets/images/deployment/linux/centos8-磁盘分区.png)

---

### 网络配置

选择 **「Network & Host Name」** → 打开以太网开关 → 确认 IP 已获取。

```text
Host Name：centos8.local
```

![网络配置](../../assets/images/deployment/linux/centos8-网络配置.png)

---

### 软件选择

选择 **「Software Selection」** → 建议：

```text
Server with GUI
```

对于新手，带图形界面更方便学习。生产环境通常选择 `Minimal Install`。

![软件选择](../../assets/images/deployment/linux/centos8-软件选择.png)

---

### 设置 root 密码

选择 **「Root Password」** → 设置密码 → 点击 **「Done」**。

![设置root密码](../../assets/images/deployment/linux/centos8-设置root密码.png)

---

### 开始安装

所有项目配置完成后，点击 **「Begin Installation」**。

![开始安装](../../assets/images/deployment/linux/centos8-开始安装.png)

安装过程约：

```text
10 ~ 20 分钟
```

（带 GUI 的安装比 Minimal 慢）

---

### 重启系统

安装完成后点击 **「Reboot System」**。

![安装完成](../../assets/images/deployment/linux/centos8-安装完成.png)

首次启动需完成初始设置（License 同意、创建用户等），按向导操作即可。

---

## 修复 Yum 源（EOL 后必做）

CentOS 8 安装完成后，默认 Yum 源已全部失效。执行 `yum update` 会报错：

```text
Error: Failed to download metadata for repo 'appstream'
```

### 原因分析

CentOS 8 EOL 后，官方将镜像从 `mirror.centos.org` 迁移到 `vault.centos.org`（归档仓库）。系统默认指向旧地址，需要手动切换到 Vault 源。

---

### 修复步骤

#### Step 1：备份原有 repo 文件

```bash
mkdir -p /etc/yum.repos.d/backup
mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/backup/
```

#### Step 2：创建新的 Vault 源配置

创建 `/etc/yum.repos.d/CentOS-Vault.repo`：

```bash
cat > /etc/yum.repos.d/CentOS-Vault.repo << 'EOF'
[baseos]
name=CentOS Linux $releasever - BaseOS
baseurl=http://vault.centos.org/centos/8/BaseOS/$basearch/os/
gpgcheck=1
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[appstream]
name=CentOS Linux $releasever - AppStream
baseurl=http://vault.centos.org/centos/8/AppStream/$basearch/os/
gpgcheck=1
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[extras]
name=CentOS Linux $releasever - Extras
baseurl=http://vault.centos.org/centos/8/extras/$basearch/os/
gpgcheck=1
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[powertools]
name=CentOS Linux $releasever - PowerTools
baseurl=http://vault.centos.org/centos/8/PowerTools/$basearch/os/
gpgcheck=1
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
EOF
```

!!! tip "国内用户推荐阿里云 Vault 镜像"
    将上述配置中的 `http://vault.centos.org` 替换为 `https://mirrors.aliyun.com/centos-vault/8.5.2111` 可加速下载。

#### Step 3：清理缓存并重建

```bash
yum clean all
yum makecache
```

#### Step 4：验证修复

```bash
yum update -y
```

如果正常下载并更新，说明源修复成功。

---

## 安装后检查

```bash
cat /etc/redhat-release    # 查看系统版本
uname -r                    # 查看内核版本
ip addr                     # 查看 IP 地址
df -h                       # 查看磁盘使用情况
free -h                     # 查看内存使用情况
```

---

## CentOS 8 的替代方案

如果你正在学习 Linux 并需要一个长期受支持的系统，推荐以下选项：

| 替代方案 | 说明 |
| --- | --- |
| [**Rocky Linux 9.x**](rocky-linux-9.md) | CentOS 创始人的新项目，与 RHEL 9 100% 兼容 |
| [**Debian 13**](debian-13.md) | 社区驱动，稳定性极高，APT 生态丰富 |
| [**Ubuntu 22.04**](ubuntu-22.04.md) | 用户量最大，社区资料最丰富 |
| **AlmaLinux 9** | 另一个 RHEL 9 兼容发行版 |

---

## 常见问题

### Yum 源修复后仍下载很慢

Vault 官方服务器在海外，国内访问慢。建议使用阿里云镜像替换 baseurl：

```bash
sed -i 's|http://vault.centos.org|https://mirrors.aliyun.com/centos-vault/8.5.2111|g' /etc/yum.repos.d/CentOS-Vault.repo
```

---

### 安装 EPEL 源也失败了

EPEL 8 同样已归档，需使用归档地址：

```bash
yum install -y https://archives.fedoraproject.org/pub/archive/epel/8/Everything/x86_64/Packages/e/epel-release-8-19.el8.noarch.rpm
```

---

### 图形界面启动后黑屏

VMware Workstation 中 CentOS 8 的 GNOME 桌面可能与 3D 加速不兼容。尝试：
1. 关闭虚拟机 → 编辑设置 → 显示器 → 取消 **「加速 3D 图形」**
2. 增加显存至 256 MB 以上

---

## 下一步学习

```mermaid
flowchart LR
    A[CentOS 8] --> B[Yum 源修复]
    B --> C[基础命令学习]
    C --> D[Docker]
    D --> E[Kubernetes]

    style A fill:#fef3c7,stroke:#d97706
    style E fill:#dbeafe,stroke:#2563eb
```

| 方向 | 教程 |
| --- | --- |
| **现代化替代** | [Rocky Linux 9.x 部署教程](rocky-linux-9.md) |
| **另一经典** | [CentOS 7 部署教程](centos-7.md) |
| **容器入门** | [Docker 部署教程](../docker&k8s/docker.md) |

---

## 总结

虽然 CentOS 8 已停止维护，但通过学习它的安装和源修复流程，你能够深入理解：

1. **Linux 包管理机制**：Yum/DNF 如何通过 repo 文件定位软件源
2. **EOL 系统管理**：企业中有大量「过期但仍在运行」的系统需要维护
3. **排错能力**：从报错信息定位问题并找到解决方案

对于新项目和学习路线，建议优先选择仍在维护的发行版（如 Rocky Linux 9 或 Debian 13），但掌握 CentOS 8 的修复技巧会让你在面试和实际工作中占得先机。 🚀

