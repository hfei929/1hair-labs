---
title: CentOS 7 虚拟机部署与EOL修复全流程教程（VMware + Yum换源）
description: 详细讲解 CentOS 7 在 VMware 虚拟机中的安装步骤，并提供 EOL 后 Yum 源失效修复方案（阿里云 Vault 归档源），适用于运维与云原生基础学习。
tags:
  - CentOS 7
  - Linux部署
  - VMware
  - Yum换源
  - 运维基础
  - Linux教程
---

# CentOS 7 虚拟机部署与EOL修复全流程教程（VMware + Yum换源）

> ⚠️ **重要说明**：CentOS 7 已于 2024 年 6 月 30 日进入 EOL（End of Life，生命周期结束）。  
> 但在企业环境中仍存在大量存量系统，因此掌握 CentOS 7 的安装与维护仍然是 Linux 运维的基础能力之一。

本教程将完整讲解：

- VMware 中安装 CentOS 7
- 系统初始化配置
- CentOS 7 EOL 后 Yum 源修复（Vault 归档源）
- 基础环境验证

---

## 一、CentOS 7 安装前准备（环境要求）

在开始部署之前，请确保具备以下环境：

### 1. 虚拟化软件
- VMware Workstation Pro / Player
- 或 VirtualBox

### 2. CentOS 7 ISO 镜像

推荐使用最终稳定版本：

- `CentOS-7-x86_64-DVD-2009.iso`

> 📌 注意：官方标准源已下线，请使用 Vault 归档版本或镜像站下载。

### 3. 推荐配置（测试环境）

| 项目 | 建议配置 |
|------|--------|
| CPU | 2 Core |
| 内存 | ≥ 2 GB |
| 硬盘 | ≥ 20 GB |
| 网络 | NAT 模式 |

---

## 二、VMware 创建 CentOS 7 虚拟机

### 1. 新建虚拟机

依次选择：

- 创建新的虚拟机
- 典型（推荐）
- 稍后安装操作系统

### 2. 选择系统类型

- Guest OS：Linux
- Version：CentOS 7 64-bit

### 3. 虚拟机基础配置

- 名称：`CentOS7-Lab`
- 存储位置：非系统盘路径
- 磁盘大小：20GB~50GB（建议拆分为多个文件）

---

### 4. 硬件自定义（关键）

进入“自定义硬件”：

- 内存：2048MB
- CPU：1 CPU / 2 Core
- CD/DVD：挂载 ISO 镜像
- 网络模式：NAT（推荐新手）

---

## 三、CentOS 7 系统安装流程

启动虚拟机后进入安装界面：

### 1. 启动安装

选择：`Install CentOS 7`

按 Enter 进入安装流程。

---

### 2. 语言选择

- 简体中文（中国）

---

### 3. 安装配置核心项（重点）

#### ① 软件选择

| 场景 | 推荐选择 |
|------|--------|
| 学习 / 运维 | 最小安装（Minimal Install） |
| 桌面使用 | GNOME 桌面 |

---

#### ② 安装位置（磁盘分区）

- 选择虚拟磁盘
- 自动分区（推荐新手）

---

#### ③ 网络与主机名

- 开启网络（必须）
- 主机名示例：`centos7.local`

---

#### ④ 时间设置

- 时区：亚洲/上海
- 启用 NTP 自动同步

---

### 4. 安装并初始化用户

点击：

- 开始安装

同时设置：

- root 密码
- 创建普通用户（推荐）

---

### 5. 重启系统

安装完成后：`Reboot`


登录方式：

- 用户名：root
- 密码：安装时设置

---

## 四、🔥 CentOS 7 EOL 后 Yum 源修复（关键步骤）

### ❗ 问题说明

由于 CentOS 7 已停止维护：

- 官方 Yum 源失效
- `yum install` 返回 404
- 无法安装任何软件包

---

### ✅ 解决方案：切换阿里云 Vault 归档源

执行以下命令：

```bash
cd /etc/yum.repos.d/

# 备份原 repo
mkdir backup
mv *.repo backup/

# 写入 Vault 源
cat > CentOS-Base.repo << 'EOF'
[base]
name=CentOS-7 - Base - Vault
baseurl=http://mirrors.aliyun.com/centos-vault/7.9.2009/os/$basearch/
gpgcheck=0
enabled=1

[updates]
name=CentOS-7 - Updates - Vault
baseurl=http://mirrors.aliyun.com/centos-vault/7.9.2009/updates/$basearch/
gpgcheck=0
enabled=1

[extras]
name=CentOS-7 - Extras - Vault
baseurl=http://mirrors.aliyun.com/centos-vault/7.9.2009/extras/$basearch/
gpgcheck=0
enabled=1
EOF

# 清理缓存
yum clean all
yum makecache
```

## 五、验证 CentOS 7 环境是否正常
1. 检查系统版本
```bash
cat /etc/redhat-release
```

2. 网络测试
```bash
ping -c 4 baidu.com
```

3. 安装基础工具
```bash
yum install -y net-tools
```

4. 查看 IP 地址
```
ip addr
```

## 六、运维补充建议（生产思维）

虽然 CentOS 7 可用于学习，但在生产环境中建议：

- 优先迁移到 Rocky Linux / AlmaLinux
- 或升级到 CentOS Stream / RHEL
- 禁止新系统继续依赖 CentOS 7

## 七、总结

CentOS 7 的核心价值已经从“新系统”转变为：

✔ 企业遗留系统维护能力
✔ Linux 基础运维训练环境
✔ 兼容性验证平台

掌握其部署与 Yum 修复，是进入云原生与 Kubernetes 领域的重要基础能力之一。

---

![微信公众号](../../assets/images/wechat-public/扫码_搜索联合传播样式-标准色版.png)
