---
title: vCenter 8.0 部署教程：新一代 VMware 集中管理平台 | 1Hair Labs
description: 面向新手的 vCenter Server 8.0（VCSA）详细部署教程，涵盖 vSphere 8 新特性、VCSA 两阶段安装、SSO 配置、ESXi 主机纳管，适用于 HomeLab 和虚拟化进阶学习。
keywords:
  - vCenter 8.0
  - VCSA 8.0
  - vSphere 8
  - vCenter部署
  - ESXi集中管理
  - SSO配置
  - HomeLab
  - 新手教程
---

# vCenter 8.0 部署教程：新一代 VMware 集中管理平台

## 前言

vCenter Server 8.0 与 vSphere 8.0 同步发布，是 VMware 虚拟化平台的新一代管理核心。相比 7.0，8.0 在架构简化、性能优化和用户体验方面都有显著提升。

如果你已经学习过 [vCenter 7.0 部署教程](vcenter-7.0.md)，会发现 8.0 的部署流程基本一致，但对目标 ESXi 主机版本有更严格的要求。

!!! info "vCenter 8.0 重要变化"
    -   **仅支持 Embedded PSC**：不再支持外部 Platform Services Controller
    -   **部署目标要求**：必须部署到 ESXi 7.0 U3 或 ESXi 8.0 主机
    -   **VCSA 底层升级**：基于 Photon OS 5.0（7.0 基于 Photon OS 3.0）
    -   **安装程序 UI 更新**：界面更现代化，流程更简洁

---

## vCenter 8.0 新特性速览

| 特性 | 说明 |
| --- | --- |
| **简化的架构** | 取消 External PSC，全部 Embedded 部署 |
| **vSphere Client 增强** | 更快的响应速度、新版主题、全局搜索优化 |
| **Tanzu 深度集成** | 在 vCenter 控制台直接管理 K8s 集群生命周期 |
| **vSAN 8.0 ESA** | 全新 Express Storage Architecture，性能大幅跃升 |
| **DPU 生命周期管理** | 在 vCenter 中管理配备 DPU 的 ESXi 主机 |
| **Green Metrics** | 碳排放和能效仪表板 |
| **安全增强** | 基于令牌的身份验证（替代 SAML 令牌）、LDAPS 默认启用 |

---

## 部署前准备

### 环境要求

| 项目 | 要求 |
| --- | --- |
| **目标 ESXi 主机** | ESXi 7.0 U3 或 ESXi 8.0，且正常运行 |
| **ESXi 主机可用资源** | 至少 14 GB 内存 + 580 GB 磁盘（Tiny） |
| **网络** | 安装程序的机器需能访问 ESXi 主机 IP |
| **DNS 解析** | 建议配置 |

### 部署规模选择

| 规模 | vCPU | 内存 | 磁盘 | 适用场景 |
| --- | --- | --- | --- | --- |
| **Tiny** | 2 | 14 GB | 600 GB | 最多 10 台主机、100 台 VM |
| **Small** | 4 | 24 GB | 680 GB | 最多 100 台主机、1000 台 VM |
| **Medium** | 8 | 32 GB | 960 GB | 最多 400 台主机、4000 台 VM |
| **Large** | 16 | 45 GB | 1420 GB | 最多 1000 台主机、10000 台 VM |

!!! warning "8.0 磁盘要求更大"
    相比 7.0，vCenter 8.0 每种规模的磁盘需求都增加了约 30~40%。Tiny 从 415 GB 增加到 600 GB，实验环境务必检查 ESXi 数据存储剩余空间。

### 软件准备

| 软件 | 说明 | 下载地址 |
| --- | --- | --- |
| **VCSA 8.0 ISO** | vCenter 安装镜像 | [VMware 评估中心](https://customerconnect.vmware.com/evalcenter) |

```text
VMware-VCSA-all-8.0.x-xxxx.iso
```

ISO 大小约 8~9 GB，下载耗时较长。

---

## 安装概览

VCSA 8.0 安装流程与 7.0 一致，分为两个阶段：

| 阶段 | 任务 | 耗时 |
| --- | --- | --- |
| **阶段一：部署** | 将 VCSA 虚拟机部署到目标 ESXi 主机 | 约 10 分钟 |
| **阶段二：配置** | 配置 SSO、网络、时间同步等服务 | 约 15 分钟 |

---

## 阶段一：部署 VCSA 虚拟机

### 启动安装程序

挂载 VCSA ISO → 进入 `vcsa-ui-installer/win32/` → 右键 `installer.exe` **以管理员身份运行**。

!!! tip "macOS/Linux 用户"
    使用 CLI 安装程序：进入 `vcsa-cli-installer/mac/` 或 `linux64/`，执行：
    ```bash
    ./vcsa-deploy install --template <JSON模板>
    ```

![VCSA安装程序](../../assets/images/deployment/vmware/vcenter8-安装程序.png)

---

### 连接目标 ESXi 主机

输入目标 ESXi 主机信息：

| 字段 | 示例 |
| --- | --- |
| ESXi 主机 FQDN 或 IP | `192.168.1.101` |
| 用户名 | `root` |
| 密码 | ESXi root 密码 |

![连接ESXi主机](../../assets/images/deployment/vmware/vcenter8-连接ESXi主机.png)

信任 ESXi 主机证书 → 确认。

---

### 设置 VCSA 虚拟机

VM 名称建议保持默认 `VMware vCenter Server`。

设置 VCSA 操作系统 **root 密码**（注意：非 vCenter SSO 密码）。

![VCSA虚拟机设置](../../assets/images/deployment/vmware/vcenter8-设置虚拟机.png)

---

### 选择部署规模

选择 **「Tiny vCenter Server」**（HomeLab 推荐）。

!!! tip "Tiny 足够用"
    即使选择 Tiny 规模，在 HomeLab 中管理 2~5 台 ESXi 主机 + 数十台 VM 完全够用。

![选择部署规模](../../assets/images/deployment/vmware/vcenter8-选择部署规模.png)

---

### 选择数据存储

选择目标数据存储 → 勾选 **「Enable Thin Disk Mode」**（推荐，节省空间）。

![选择数据存储](../../assets/images/deployment/vmware/vcenter8-选择数据存储.png)

---

### 配置网络

填入 VCSA 的网络参数：

| 字段 | 示例值 |
| --- | --- |
| **FQDN** | `vcenter8.local` |
| **IP Address** | `192.168.1.210` |
| **Subnet Mask** | `255.255.255.0` |
| **Default Gateway** | `192.168.1.1` |
| **DNS Server** | `192.168.1.1` |

![配置网络](../../assets/images/deployment/vmware/vcenter8-配置网络.png)

---

### 确认并开始部署

核对所有配置 → 点击 **「FINISH」**。

部署过程约 8~12 分钟。

![阶段一进度](../../assets/images/deployment/vmware/vcenter8-阶段一进度.png)

---

## 阶段二：配置 vCenter 服务

阶段一完成后，自动进入阶段二。

### NTP 时间同步

建议填入国内 NTP 服务器：

```text
ntp.aliyun.com
```

---

### 配置 SSO

| 字段 | 示例值 | 说明 |
| --- | --- | --- |
| **SSO Domain** | `vsphere.local` | 默认域名 |
| **SSO Administrator** | `administrator@vsphere.local` | SSO 管理员用户名 |
| **SSO Password** | 你的密码 | 这是登录 vCenter 的最重要凭证 |

!!! danger "保管好 SSO 管理员密码"
    `administrator@vsphere.local` 的密码是你管理整个虚拟化平台的钥匙。建议使用密码管理器保存。

![SSO配置](../../assets/images/deployment/vmware/vcenter8-SSO配置.png)

---

### 完成配置

核对配置 → 勾选备份确认 → **「FINISH」**。

配置过程约 10~15 分钟。

![阶段二完成](../../assets/images/deployment/vmware/vcenter8-安装完成.png)

---

## 访问 vCenter 8.0

浏览器访问：

```text
https://<VCSA-IP>/ui
```

使用 `administrator@vsphere.local` 登录。

![vCenter8登录](../../assets/images/deployment/vmware/vcenter8-登录.png)

vCenter 8.0 的 vSphere Client 界面相比 7.0 更现代化、响应更快。

![vCenter8首页](../../assets/images/deployment/vmware/vcenter8-首页.png)

---

## 添加 ESXi 主机到 vCenter

创建数据中心 → 右键数据中心 → **「Add Host」** → 输入 ESXi IP、root 密码 → 完成添加。

具体流程与 [vCenter 7.0](vcenter-7.0.md#将-esxi-主机加入-vcenter) 完全一致，不再赘述。

---

## 7.0 升级到 8.0 注意事项

如果你已有 vCenter 7.0 环境，升级到 8.0 前请注意：

1. **备份**：务必备份 VCSA（vCenter 管理界面 → 备份 → 立即备份）
2. **兼容性检查**：确保所有 ESXi 主机为 7.0 U3 或更高版本
3. **外部 PSC 迁移**：如果使用 External PSC，需先迁移到 Embedded 模式
4. **升级路径**：vCenter 7.0 → 8.0 直接升级，无需中间版本
5. **回滚准备**：保留 7.0 的备份，以便出问题时回滚

---

## 常见问题

### 阶段一提示「目标 ESXi 主机版本不满足要求」

vCenter 8.0 只能部署到 **ESXi 7.0 U3 或 ESXi 8.0** 主机。如果目标主机是 7.0 U2 或更低版本，需先升级 ESXi。

---

### 阶段二 NTP 配置失败

如果 NTP 配置阶段连接超时，可以跳过。安装完成后可在 VCSA 的 VAMI 管理界面 (`https://<VCSA>:5480`) 中重新配置。

---

### VCSA 磁盘空间不足

8.0 的 Tiny 需要 600 GB。如果 ESXi 数据存储空间紧张：
1. 务必勾选 Thin Disk Mode（精简置备）
2. 安装后可清理数据存储上的旧 ISO 和快照

---

## 下一步学习

```mermaid
flowchart LR
    A[ESXi 8.0] --> B[vCenter 8.0]
    B --> C[vSAN 8.0 ESA]
    B --> D[Tanzu K8s]
    C --> E[超融合实战]

    style B fill:#fef3c7,stroke:#d97706
    style A fill:#dbeafe,stroke:#2563eb
```

| 方向 | 教程 |
| --- | --- |
| **上一代对比** | [vCenter 7.0 部署教程](vcenter-7.0.md) |
| **基础平台** | [ESXi 8.0 部署教程](esxi-8.0.md) |
| **上一代 ESXi** | [ESXi 7.0 部署教程](esxi-7.0.md) |
| **版本概念** | [裸金属、虚拟机与容器](../basics/baremetal-vm-container.md) |

---

## 总结

vCenter 8.0 在 7.0 的基础上简化了架构、提升了性能、增强了云原生集成。部署流程与 7.0 高度一致，主要区别在于：

1. **必须部署到 ESXi 7.0 U3+**：对目标主机版本有硬性要求
2. **磁盘需求更大**：Tiny 从 415 GB 增至 600 GB
3. **仅支持 Embedded PSC**：架构更加简洁
4. **UI 与性能提升**：vSphere Client 更快、更现代

对于新建 HomeLab 的用户，建议直接选择 ESXi 8.0 + vCenter 8.0 组合，享受最新特性。如果你已有 7.0 环境，也完全可以先用 7.0 学习，后续平滑升级。 🚀

