---
title: CentOS Linux 8 安装教程：EOL 后配置 Vault 归档源 | 1Hair Labs
description: CentOS Linux 8.5.2111 VMware 安装与 EOL 后 Vault 归档仓库配置指南，涵盖安装准备、网络与分区、DNF/Yum 源修复、EPEL 8 归档和迁移建议；说明归档源不再提供安全维护。
keywords:
  - CentOS 8
  - CentOS Linux 8.5.2111
  - CentOS 8 安装
  - CentOS EOL
  - CentOS Vault
  - DNF 仓库修复
  - VMware Workstation
  - Linux 运维
---

# CentOS Linux 8 部署教程：安装与 EOL Vault 源修复

## 前言

CentOS Linux 8 于 2021 年 12 月 31 日结束维护。其软件包仍可从 Vault 归档仓库获取，但归档仓库不再提供安全更新或常规维护。本文用于隔离实验、复现旧环境和了解历史系统维护，不应将“能安装软件包”误认为系统仍受支持。

!!! danger "不要将 CentOS Linux 8 用于新建生产环境"
    CentOS Linux 8 不再接收安全更新和 Bug 修复。若现有业务仍依赖它，应制定迁移计划并评估应用兼容性；新建环境优先选择仍受支持的发行版，例如 [Rocky Linux](rocky-linux-9.md) 或 [Debian](debian-13.md)。

本文介绍如何在 VMware Workstation 中安装 CentOS Linux 8.5.2111，并将已失效的默认仓库切换到固定版本的 Vault 归档。文中原有安装截图均已缺失，现以文字步骤和选项说明替代；真实示意图将在后续更新中补足。

---

## CentOS 8 版本说明

| 版本 | 状态 | 说明 |
| --- | --- | --- |
| **CentOS Linux 8** | 已于 2021-12-31 结束维护 | 传统固定发行版；软件包归档在 Vault |
| **CentOS Stream 8** | 已于 2024-05 结束维护 | RHEL 的上游滚动发行版 |
| **CentOS Stream 9** | 维护状态依生命周期而定 | 与 CentOS Linux 8 是不同产品，不可直接视为同一版本 |

本文安装的是 **CentOS Linux 8.5.2111**，不是 CentOS Stream 8。两者的仓库、发行模式和维护状态不同；为避免混用，请在配置仓库前核对 `/etc/centos-release`。

---

## 部署前准备

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
| --- | --- | --- |
| CPU | 1 vCPU | 2 vCPU 起 |
| 内存 | 2 GB | 4 GB 起；图形桌面建议更多 |
| 磁盘 | 20 GB | 40-50 GB，按软件和日志需求调整 |
| 网络 | 可访问所需安装资源 | NAT、桥接或自定义网络，按实验目标选择 |

### 软件准备

| 软件 | 说明 | 下载地址 |
| --- | --- | --- |
| **VMware Workstation Pro 17+** | 宿主机虚拟化软件 | [VMware 官网](https://www.vmware.com/products/workstation-pro.html) 或 [网盘地址（提取码：MBKT）](https://pan.quark.cn/s/14503c2e7051) |
| **CentOS Linux 8.5.2111 ISO** | EOL 归档安装镜像 | [CentOS Vault](https://vault.centos.org/8.5.2111/isos/x86_64/) |

!!! warning "仅用于旧环境复现"
    8.5.2111 是 CentOS Linux 8 的最终发行版本。下载后核对镜像来源和校验值；归档 ISO 不包含后续安全修复：
    ```text
    CentOS-8.5.2111-x86_64-dvd1.iso
    ```

---

## 创建虚拟机

VMware Workstation 创建虚拟机的通用步骤可参考 [Ubuntu 22.04 部署教程](ubuntu-22.04.md)。以下列出 CentOS Linux 8 的客户机类型和建议规格。

### 客户机操作系统

在客户机操作系统列表中选择 **Linux → Red Hat Enterprise Linux 8 64-bit**。若 Workstation 版本未提供该项，选择兼容的 RHEL 8 64 位客户机类型，并确保虚拟机固件和 ISO 架构一致。

### 虚拟机规格

学习环境可从 2 vCPU、4 GB 内存和 40-50 GB 虚拟磁盘起步。图形桌面、多项并行实验或较大的软件安装需要更多资源。网络选择应符合实验需求：NAT 适合一般联网，桥接适合需要从局域网其他设备直接访问的场景。

---

## 安装 CentOS 8

### 启动安装

将 CentOS Linux 8.5.2111 ISO 挂载到虚拟光驱并启动虚拟机。在启动菜单中选择 **Install CentOS Linux 8**；若无法进入安装程序，先检查 ISO 完整性、固件启动模式和虚拟光驱连接状态。

---

### 语言选择

按使用习惯选择安装界面语言。英文界面便于按原始错误信息检索上游资料；系统安装后仍可按需配置语言和键盘布局。

---

### 安装信息摘要

在 **Installation Summary** 页面完成安装目的地、网络、软件选择和账户设置。带警告标记的必需项目未完成前，安装程序不会开始安装；开始前逐项核对目标磁盘和网络配置。

---

### 磁盘分区

进入 **Installation Destination**，选中虚拟磁盘。新建实验虚拟机通常可选择自动分区；手动分区适用于需要单独规划 `/home`、`/var` 或 LVM 的情形。安装开始后对磁盘的更改可能覆盖原有数据，确认选择的是目标虚拟磁盘。

---

### 网络配置

在 **Network & Host Name** 中启用网卡并检查是否获得地址；NAT 或桥接环境的地址分配方式不同。为主机设置可解析且符合本地命名规范的名称。

```text
Host Name：centos8.example.test
```

`.test` 是文档示例域名；若不配置本地 DNS，应使用主机名而不要假设其他设备能解析该名称。静态 IP、网关和 DNS 应与所选虚拟网络匹配。

---

### 软件选择

在 **Software Selection** 中按用途选择安装环境：

```text
Server with GUI
```

**Server with GUI** 适合需要桌面的学习场景；无桌面服务器或轻量实验可选 **Minimal Install**。安装软件组会影响资源占用和后续维护面。

---

### 设置 root 密码

在 **Root Password** 中设置唯一且足够强的管理员密码，并通过密码管理器保存。日常管理建议创建普通用户并按需授予管理员权限，避免直接使用 root 登录图形会话或远程服务。

---

### 开始安装

确认所有必需项目已完成，尤其是安装目标磁盘、软件选择和账户设置，然后选择 **Begin Installation**。耗时取决于宿主机、虚拟磁盘和所选软件组；等待安装程序报告完成，不要依赖固定分钟数判断是否卡住。

---

### 重启系统

安装完成后选择 **Reboot System**，并在重启时断开 ISO 或调整启动顺序，避免再次进入安装程序。若首次启动显示初始配置向导，按提示确认许可并创建日常使用账户。

---

## 配置 CentOS Linux 8 Vault 归档源

```text
Error: Failed to download metadata for repo 'appstream'
```

CentOS Linux 8 的默认镜像已归档。原有 repo 配置仍指向已停用的镜像地址时，DNF（`yum` 命令在 CentOS 8 中兼容调用 DNF）无法下载仓库元数据。Vault 只保留固定版本的软件包，不提供后续安全更新。

### 1. 确认系统版本并备份仓库配置

先确认当前系统是 CentOS Linux 8.5.2111，而不是 CentOS Stream 或其他 RHEL 兼容系统：

```bash
cat /etc/centos-release
uname -m
dnf repolist --all
```

下面的仓库配置针对 CentOS Linux 8.5.2111。先备份现有配置，再仅停用 CentOS Linux 默认 repo 文件；不要移动或覆盖第三方仓库配置。

```bash
cp -a /etc/yum.repos.d "/root/yum.repos.d.backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p /etc/yum.repos.d/backup

for f in /etc/yum.repos.d/CentOS-Linux-*.repo; do
    [ -e "$f" ] || continue
    mv -- "$f" /etc/yum.repos.d/backup/
done
```

如果现有 CentOS repo 文件使用其他文件名，先检查 `dnf repolist --all` 和文件内容，只停用指向失效 CentOS 镜像的配置。

### 2. 创建固定版本的 Vault 配置

创建 `/etc/yum.repos.d/CentOS-Vault.repo`：

```bash
cat > /etc/yum.repos.d/CentOS-Vault.repo << 'EOF'
[baseos]
name=CentOS Linux 8.5.2111 - BaseOS
baseurl=https://vault.centos.org/8.5.2111/BaseOS/$basearch/os/
gpgcheck=1
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[appstream]
name=CentOS Linux 8.5.2111 - AppStream
baseurl=https://vault.centos.org/8.5.2111/AppStream/$basearch/os/
gpgcheck=1
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[extras]
name=CentOS Linux 8.5.2111 - Extras
baseurl=https://vault.centos.org/8.5.2111/extras/$basearch/os/
gpgcheck=1
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[powertools]
name=CentOS Linux 8.5.2111 - PowerTools
baseurl=https://vault.centos.org/8.5.2111/PowerTools/$basearch/os/
gpgcheck=1
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
EOF
```

PowerTools 默认关闭，仅在确实需要其中的软件包时启用。若要使用国内镜像，可在每个 `baseurl` 中将 `https://vault.centos.org` 替换为 `https://mirrors.aliyun.com/centos-vault`；镜像站可用性和同步情况可能变化。

### 3. 重建缓存并验证

```bash
dnf clean all
dnf makecache --refresh
dnf repolist --enabled
```

缓存重建成功后，可查询一个基础软件包验证元数据：

```bash
dnf info bash
```

如需更新实验系统，使用 `dnf upgrade` 并先检查将要变更的包。它只能更新到归档中的最后版本，不能为 CentOS Linux 8 提供 EOL 之后的安全修复；不要把命令成功执行当作系统恢复支持。

!!! warning "归档软件包仍应验证来源"
    保留 `gpgcheck=1`，不要为解决签名错误而关闭 GPG 校验。排错时先检查系统时间、DNS、网络连通性和仓库路径。

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

## 迁移与替代方案

如果目标是新建环境或长期运行，应评估应用、驱动、软件源和运维流程后迁移到仍受支持的发行版：

| 替代方案 | 说明 |
| --- | --- |
| [**Rocky Linux 9.x**](rocky-linux-9.md) | 面向 RHEL 兼容场景的企业级 Linux 发行版；迁移前验证应用和第三方软件支持情况 |
| [**Debian 13**](debian-13.md) | 社区发行版，采用 APT 包管理；适合希望使用 Debian 生态的环境 |
| [**Ubuntu 22.04**](ubuntu-22.04.md) | 采用 APT 包管理；部署时根据支持周期和应用兼容性选择版本 |

发行版迁移不是简单更换软件源。生产系统应先盘点服务和依赖、备份数据、制定回滚方案，并在测试环境验证后再迁移。

---

## 常见问题

### Vault 源修复后仍下载失败或速度较慢

检查 DNS、系统时间、HTTPS 连通性和 `dnf makecache` 报错中的具体仓库路径。也可将 repo 文件中的 Vault 主机名替换为可访问的镜像地址；例如阿里云镜像：

```bash
sed -i 's|https://vault.centos.org|https://mirrors.aliyun.com/centos-vault|g' /etc/yum.repos.d/CentOS-Vault.repo
```

替换后重新运行 `dnf clean all` 和 `dnf makecache --refresh`。镜像站目录和同步状态可能变化；若仍失败，核对其是否包含 8.5.2111 对应的 BaseOS、AppStream、extras 和 PowerTools 路径。

---

### EPEL 8 仓库无法安装

EPEL 8 已归档，不再提供常规维护。若旧环境确实依赖 EPEL 8，可从 Fedora 官方归档获取 `epel-release` RPM；以下地址适用于 x86_64。保留 GPG 校验，不要从不明站点下载，也不要将该仓库用于新系统：

```bash
dnf install https://archives.fedoraproject.org/pub/archive/epel/8/Everything/x86_64/Packages/e/epel-release-8-19.el8.noarch.rpm
```

安装 release RPM 不一定会自动将仓库指向归档站点。若仍无法获取元数据，按 [Fedora EPEL 8 官方归档](https://archives.fedoraproject.org/pub/archive/epel/8/)说明，将启用的 EPEL 仓库配置为 `https://archives.fedoraproject.org/pub/archive/epel/8/Everything/$basearch/`，停用对应的 metalink/mirrorlist，并保留仓库 GPG 校验；之后清理缓存并重建元数据。

---

### 图形界面启动后黑屏

先检查虚拟机控制台是否仍在启动、显示驱动是否加载，以及虚拟机是否分配足够内存。若怀疑 VMware 3D 加速兼容问题，可关机后暂时关闭 **Accelerate 3D Graphics** 再测试；不要未经验证地将显存值视为通用修复。

---

## 下一步学习

```mermaid
flowchart LR
    A[CentOS 8] --> B[Yum 源修复]
    B --> C[基础命令学习]
    C --> D[Docker]
    D --> E[Kubernetes]

    style A fill:#fef3c7,stroke:#d97706,color:#111827
    style E fill:#dbeafe,stroke:#2563eb,color:#111827
```

| 学习方向 | 推荐阅读 |
| --- | --- |
| **迁移到受支持的 RHEL 兼容发行版** | [Rocky Linux 9.x 部署教程](rocky-linux-9.md)——了解安装流程，并在迁移前验证业务兼容性。 |
| **学习 Debian 系发行版** | [Debian 13 部署教程](debian-13.md)——了解 Debian 安装及 APT 软件包管理。 |
| **复现另一代 CentOS 环境** | [CentOS 7 部署教程](centos-7.md)——参考另一篇 EOL 系统安装与归档仓库教程。 |
| **继续学习容器** | [Docker 部署教程](../docker&k8s/docker.md)——在隔离的受支持系统上学习容器基础。 |

---

## 总结

CentOS Linux 8 已结束维护。本文的安装和 Vault 配置只适合隔离实验、旧环境复现或受控迁移准备；Vault 能恢复归档软件包的访问，不会恢复安全更新。

通过本文可以理解：

1. **仓库配置机制**：DNF（兼容 `yum` 命令）如何通过 repo 文件读取仓库元数据。
2. **归档系统的限制**：固定版本仓库适用于复现旧环境，但不等于仍受支持。
3. **排错与迁移**：从元数据、DNS、网络和签名错误入手，同时规划到受支持系统的迁移。

新项目应优先选用仍在维护的发行版，并按官方生命周期规划升级；不要将 EOL 系统用于暴露在不可信网络中的服务。
