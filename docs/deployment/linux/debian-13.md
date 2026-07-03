---
title: Debian 13（Trixie）虚拟机安装全流程教程（VMware + APT源配置）
description: 详细讲解 Debian 13（Trixie）在 VMware 虚拟机中的安装步骤，并提供系统初始化与国内 APT 换源配置，适用于 Linux 运维与云原生基础学习。
tags:
  - Debian 13
  - Linux安装
  - VMware
  - APT换源
  - Trixie
  - 运维基础
---

# Debian 13（Trixie）虚拟机安装全流程教程（VMware + APT源配置）

> 💡 **说明**：:contentReference[oaicite:0]{index=0} 是目前最稳定、最经典的 Linux 发行版之一。  
Debian 13（代号 Trixie）属于其稳定分支版本，广泛用于服务器、云计算基础环境以及开发测试系统。

本教程将完整讲解：

- VMware 中安装 Debian 13
- 系统基础初始化配置
- APT 软件源配置（国内加速）
- 基础环境验证

---

## 一、Debian 13 安装前准备

### 1. 虚拟化环境

推荐使用：

- VMware Workstation Pro / Player
- VirtualBox

---

### 2. Debian 13 ISO 镜像

推荐下载：

- `debian-13.0.0-amd64-netinst.iso`（网络安装版，推荐）

> 📌 netinst 版本优势：
> - 镜像小（约几百 MB）
> - 安装过程自动下载最新软件包
> - 更适合服务器环境

---

### 3. 推荐虚拟机配置

| 项目 | 推荐配置 |
|------|--------|
| CPU | 2 Core |
| 内存 | ≥ 2 GB |
| 硬盘 | ≥ 20 GB |
| 网络 | NAT |

---

## 二、创建 Debian 13 虚拟机

### 1. 新建虚拟机流程

在 VMware 中：

- 创建新的虚拟机
- 选择“典型（推荐）”
- 选择“稍后安装操作系统”

---

### 2. 系统类型选择

- Guest OS：Linux
- Version：Debian 12+ / 64-bit（兼容 Debian 13）

---

### 3. 虚拟机基础设置

- 名称：`Debian13-Lab`
- 存储路径：非系统盘
- 磁盘：20GB~50GB（推荐拆分）

---

### 4. 硬件配置（关键）

- 内存：2048MB
- CPU：1-2 Core
- 网络：NAT
- CD/DVD：挂载 Debian ISO

---

## 三、Debian 13 安装流程

启动虚拟机后进入安装界面。

---

### 1. 选择安装模式

建议选择：`Graphical install`


---

### 2. 语言与区域设置

- 语言：简体中文
- 地区：中国
- 键盘：默认美式键盘

---

### 3. 网络配置

系统自动配置 DHCP：

- 若成功获取 IP：继续
- 若失败：检查 VMware NAT 网络

---

### 4. 主机名配置

示例：`debian13.local`


---

### 5. 用户与密码

设置：

- root 密码（可选启用）
- 创建普通用户（推荐用于日常操作）

---

### 6. 磁盘分区（重点）

推荐选择：

- ❗ 使用整个磁盘（新手）
- ❗ 自动分区（推荐）

分区结构：

- `/`
- `swap`
- `/home`（可选）

---

### 7. 软件选择（重要）

建议选择：

| 场景 | 选择 |
|------|------|
| 服务器学习 | SSH server + standard system utilities |
| 桌面环境 | GNOME |

---

### 8. 安装 GRUB 引导

- 选择：Yes
- 安装到：`/dev/sda`

---

### 9. 完成安装并重启

安装完成后：`Reboot`


---

## 四、系统首次登录与基础检查

登录系统后执行：

```bash
whoami
```

查看系统版本：
```bash
cat /etc/os-release
```

## 五、🔥 Debian 13 APT 换源（国内加速）

默认 Debian 源在国内访问较慢，因此建议更换为国内镜像源。

1. 备份原始源
```bash
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak
```

2. 使用清华大学镜像源（推荐）

编辑 `sources.list`：
```bash
sudo nano /etc/apt/sources.list
```
替换为：
```bash
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie-updates main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security trixie-security main contrib non-free non-free-firmware
```

3. 更新软件索引
```bash
sudo apt update
sudo apt upgrade -y
```

## 六、基础工具安装验证

1. 安装常用工具
```bash
sudo apt install -y net-tools curl wget vim
```

2. 查看 IP 地址
```bash
ip addr
```

3. 网络测试
```bash
ping -c 4 qq.com
```

## 七、Debian 13 运维基础建议

Debian 13 适合以下场景：

- 云服务器基础系统
- Docker / Kubernetes 节点
- CI/CD 构建环境
- 安全性要求较高的系统

**与 CentOS 对比（重要认知）**
|项目	|Debian 13	|CentOS 7|
|---|---|---|
|包管理|	apt	|yum|
|更新频率	|更快|	已 EOL|
|社区	|Debian Project|	Red Hat 体系|
|适用场景	|云原生 / 新系统|	遗留系统维护|

## 八、总结

Debian 13（Trixie）是一个非常适合作为：

✔ 云原生基础系统
✔ Kubernetes 节点环境
✔ 生产级 Linux 学习平台

相比 CentOS 7，它更现代、更活跃，也更适合未来技术栈演进。

![微信公众号](../../assets/images/wechat-public/扫码_搜索联合传播样式-标准色版.png)
