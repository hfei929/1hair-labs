---
title: Windows 11 部署教程：从零开始安装与配置 | 1Hair Labs
description: 面向新手的 Windows 11 详细安装教程，涵盖 TPM 2.0 绕过、离线账户创建、隐私设置优化，适用于 VMware 虚拟机与物理机。
keywords:
  - Windows 11
  - Windows安装教程
  - TPM绕过
  - VMware虚拟机
  - Rufus
  - Ventoy
  - 系统部署
  - 新手教程
---

# Windows 11 部署教程：从零开始安装与配置

## 前言

Windows 11 是微软最新的桌面操作系统，带来了全新的 UI 设计、更严格的硬件要求和更强的安全机制。相比 Windows 10，Windows 11 的安装过程在硬件验证环节增加了一些门槛，但对掌握正确方法的人来说并不是障碍。

本教程面向新手，详细说明从准备安装介质到完成系统初始配置的完整流程。本文以虚拟机和物理机通用的安装步骤为主。

!!! info "与 Windows 10 教程的关系"
    如果你已经阅读过 [Windows 10 部署教程](windows-10.md)，会发现大部分流程相似。本文重点突出 **Windows 11 特有的差异**：TPM 2.0 要求、微软账户登录、新 UI 布局等。

---

## Windows 11 版本选择

| 版本 | 适用场景 |
| --- | --- |
| **家庭版（Home）** | 个人日常使用（功能有限，不推荐） |
| **专业版（Pro）** | 远程桌面、组策略、BitLocker 加密、Hyper-V |
| **专业工作站版** | 高性能硬件、ReFS 文件系统、持久内存 |
| **企业版（Enterprise）** | 公司大规模部署、AppLocker、DirectAccess |

推荐选择 **专业版**，功能齐全且对个人用户足够。

---

## 部署前准备

### 硬件要求

Windows 11 的硬件要求比 Windows 10 更严格：

| 项目 | 最低要求 | 说明 |
| --- | --- | --- |
| **CPU** | 1 GHz，2 核以上，64 位 | 需在微软兼容列表中 |
| **内存** | 4 GB | 推荐 8 GB 及以上 |
| **存储** | 64 GB | 推荐 120 GB 及以上 |
| **TPM** | TPM 2.0 | 可绕过（见下文） |
| **安全启动** | UEFI Secure Boot | 可绕过 |
| **显卡** | DirectX 12 / WDDM 2.x | |

!!! tip "虚拟机用户注意"
    在 VMware Workstation 中安装 Windows 11 时，需在虚拟机设置中 **添加可信平台模块（TPM）**，否则安装程序会提示硬件不满足要求。也可以使用下文的方法绕过 TPM 检查。

### 安装介质准备

**物理机安装**：制作启动 U 盘

-   [Rufus](https://rufus.ie/)（推荐，可自动绕过 TPM 限制）
-   [Ventoy](https://www.ventoy.net/cn/index.html)（多 ISO 共存）
-   微软官方媒体创建工具（不绕过 TPM）

**虚拟机安装**：直接挂载 ISO 即可。

### 软件准备

| 软件 | 下载地址 |
| --- | --- |
| **Windows 11 ISO** | [微软官网](https://www.microsoft.com/software-download/windows11) |
| **Rufus**（推荐） | [rufus.ie](https://rufus.ie/) |

---

## 创建虚拟机（VMware Workstation）

VMware Workstation 创建虚拟机的通用步骤请参考 [Ubuntu 22.04 部署教程](../linux/ubuntu-22.04.md#创建虚拟机)。以下仅列出 Windows 11 特有设置：

### 客户机操作系统

```text
Microsoft Windows → Windows 11 x64
```

![选择操作系统](../../assets/images/deployment/windows/win11-选择操作系统.png)

### 虚拟机规格

```text
CPU：2 Core 以上
内存：8192 MB（8 GB）
磁盘：80 GB
网络：桥接模式
```

!!! tip "添加 TPM 模块"
    创建虚拟机后，编辑虚拟机设置 → **添加** → 选择 **「可信平台模块」**。如果 VMware Workstation 版本不支持，选择 **「加密此虚拟机」** 后即可添加。或者使用下文的方法绕过 TPM。

![添加TPM](../../assets/images/deployment/windows/win11-添加TPM.png)

---

## 安装 Windows 11

### 启动安装介质

挂载 ISO → 开启虚拟机 → 看到 **「Press any key to boot from CD/DVD」** → 按任意键进入安装程序。

![启动安装](../../assets/images/deployment/windows/win11-启动安装.png)

---

### 语言和区域

选择语言、时间和键盘布局 → **「下一步」** → **「现在安装」**。

![语言选择](../../assets/images/deployment/windows/win11-语言选择.png)

---

### 绕过 TPM 2.0 检查（如需要）

如果遇到 **「此电脑无法运行 Windows 11」** 的提示：

#### 方法一：Rufus 制作启动盘（推荐）

使用 Rufus 写入 ISO 到 U 盘时，Rufus 会提示是否移除 TPM/安全启动/在线账户等限制，全部勾选即可。

#### 方法二：注册表绕过

在安装界面按 `Shift + F10` 打开命令提示符 → 输入 `regedit` → 定位到：

```text
HKEY_LOCAL_MACHINE\SYSTEM\Setup
```

右键 `Setup` → 新建 **项** → 命名为 `LabConfig` → 在 `LabConfig` 中新建以下 DWORD (32位) 值，全部设为 `1`：

```text
BypassTPMCheck
BypassSecureBootCheck
BypassRAMCheck
BypassStorageCheck
BypassCPUCheck
```

关闭注册表和命令提示符，返回安装程序继续。

![绕过TPM](../../assets/images/deployment/windows/win11-绕过TPM.png)

---

### 选择安装版本

根据需求选择版本（推荐 **Windows 11 Pro**）。

![选择版本](../../assets/images/deployment/windows/win11-选择版本.png)

---

### 接受许可条款

勾选 **「我接受许可条款」** → **「下一步」**。

---

### 选择安装类型

选择 **「自定义：仅安装 Windows（高级）」**。

![安装类型](../../assets/images/deployment/windows/win11-安装类型.png)

---

### 磁盘分区

选择目标磁盘 → 如磁盘有旧分区，全部删除后直接 **「下一步」**（系统自动创建必要分区）。

![磁盘分区](../../assets/images/deployment/windows/win11-磁盘分区.png)

安装过程约：

```text
15 ~ 30 分钟
```

期间会自动重启数次。

![安装进度](../../assets/images/deployment/windows/win11-安装进度.png)

---

## 初始设置

### 选择区域和键盘

根据实际区域选择 → 默认键盘布局 `微软拼音`。

---

### 网络连接

Windows 11 家庭版在 OOBE 阶段**强制要求联网和登录微软账户**。

#### 绕过微软账户（推荐）

在 **「让我们为你连接到网络」** 页面：

1.  按 `Shift + F10` 打开命令提示符
2.  输入以下命令并回车：

```text
OOBE\BYPASSNRO
```

3.  系统自动重启 → 再次进入网络页面时，会出现 **「我没有 Internet 连接」** 选项
4.  点击 → **「继续执行受限设置」** → 创建本地账户

!!! tip "仅家庭版需要绕过"
    专业版和企业版可直接选择 **「改为域加入」** 来创建本地账户。

---

### 隐私设置

建议全部 **关闭**，然后点击 **「接受」**。

![隐私设置](../../assets/images/deployment/windows/win11-隐私设置.png)

---

### 自定义体验

跳过所有可选设置，加快进入桌面。

---

## 首次进入桌面

Windows 11 带来了全新的居中任务栏和开始菜单：

![桌面](../../assets/images/deployment/windows/win11-桌面.png)

---

## 安装后必做配置

### 安装 VMware Tools（虚拟机）

VMware Workstation 菜单 → **「虚拟机」** → **「安装 VMware Tools」**。

安装后支持分辨率自适应、剪贴板共享、拖放文件等。

---

### 激活 Windows

```powershell
# 查看激活状态
slmgr /xpr
```

有正版密钥：设置 → 系统 → 激活 → 更改产品密钥。

---

### Windows 更新

设置 → Windows 更新 → 检查更新 → 安装所有可用更新。

---

## 常见问题

### 虚拟机中 Windows 11 卡顿

1. 确保分配了至少 4 GB 内存和 2 Core CPU
2. 安装 VMware Tools
3. 关闭 Windows 11 的视觉效果：设置 → 辅助功能 → 视觉效果 → 关闭透明效果和动画

---

### 提示「此电脑不符合 Windows 11 最低系统要求」

参考上文的 TPM 绕过方法。对于虚拟机，更推荐直接添加虚拟 TPM 模块。

---

### 安装完成后桌面没有「此电脑」图标

桌面右键 → 个性化 → 主题 → 桌面图标设置 → 勾选 **「计算机」**。

---

## 下一步学习

| 方向 | 教程 |
| --- | --- |
| **上一代系统** | [Windows 10 部署教程](windows-10.md) |
| **服务器系统** | [Windows Server 2016 部署教程](windows-server-2016.md) |
| **Linux 入门** | [Ubuntu 22.04 部署教程](../linux/ubuntu-22.04.md) |
| **虚拟化基础** | [VMware ESXi 7.0 部署教程](../vmware/esxi-7.0.md) |

---

## 总结

Windows 11 的安装流程与 Windows 10 大同小异，核心区别在于：

1. **TPM 2.0 要求**：可通过注册表或 Rufus 绕过
2. **强制微软账户**：家庭版需用 `OOBE\BYPASSNRO` 绕过
3. **新 UI**：居中任务栏、新开始菜单、圆角窗口

掌握这些差异后，你就能在虚拟机或物理机上顺利安装 Windows 11 了。 🚀
