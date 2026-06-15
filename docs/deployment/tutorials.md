---

title: 新手部署教程概览
description: Linux、VMware、Docker、Kubernetes 等系统与软件安装部署教程，从零开始学习服务器、虚拟化、容器与云原生技术。
keywords:
  - Linux安装教程
  - VMware教程
  - Docker教程
  - Kubernetes教程
  - HomeLab
  - 服务器部署
  - 新手教程

---

# 1hairlabs

欢迎来到 **1HairLabs | 一根头发丝的宽度** 新手部署教程专区。

这里专注于记录各种系统与软件的安装部署过程，帮助零基础用户快速完成环境搭建。

所有教程均基于真实实验环境验证，尽可能采用：

* 图文步骤
* 环境说明
* 命令示例
* 常见问题排查
* 部署后验证

的方式呈现。

无论你是：

* 准备学习 Linux 或 Windows
* 想搭建自己的 HomeLab（家庭实验室）
* 想体验 VMware 或 Proxmox
* 想学习 Docker 与 Kubernetes
* 想搭建 NAS、监控平台或个人服务

都可以从这里开始。

> 本系列内容持续更新中，欢迎收藏本站并关注后续文章。

---

## 学习路线推荐

如果你刚接触服务器、虚拟化和云原生技术，建议按照以下顺序学习：

```text
物理服务器
      ↓
虚拟化平台（ESXi / Proxmox）
      ↓
Linux
      ↓
Docker
      ↓
Kubernetes
      ↓
业务应用
```

在开始安装系统之前，建议先阅读：

👉 《[裸金属、虚拟机与容器的区别](./basics/baremetal-vm-container.md)》

帮助建立完整的基础认知。

---

## Linux 系统部署教程

Linux 是目前服务器领域最常见的操作系统，也是学习 Docker、Kubernetes 和云原生技术的基础。

推荐新手优先学习：

* Ubuntu 22.04
* Debian 12
* Rocky Linux 9

计划更新：

* Ubuntu 22.04 安装教程
* CentOS 7 安装教程
* Rocky Linux 9 安装教程
* Debian 12 安装教程

!!! tip "发行版部署差异"
    因为同一个发行版的各版本部署差异很小，所以每个发行版更新一版部署教程。比如 `Debian` 更新 `12` 版本，因为其他的比如 11、 13 安装部署和12基本上都是一样的，需要安装其他版本的话直接参考 Debian12 的安装教程即可。

---

## VMware 虚拟化部署教程

虚拟化技术是现代数据中心的基础能力之一。

学习虚拟化推荐从 VMware 开始。

计划更新：

* ESXi 7.0 安装教程
* ESXi 8.0 安装教程
* vCenter 7.0 安装教程
* vCenter 8.0 安装教程

适合：

* 家庭实验室
* 企业虚拟化平台
* 运维工程师学习环境

---

## Docker 与 Kubernetes

Docker 和 Kubernetes 已成为云原生时代的核心技术。

推荐学习路线：

```text
Linux
   ↓
Docker
   ↓
Docker Compose
   ↓
Kubernetes
```

计划更新：

* Docker 安装教程
* Docker Compose 部署教程
* Kubernetes 集群部署教程
* Helm 安装教程

---

## HomeLab 推荐项目

当掌握基础安装部署后，可以尝试搭建自己的实验环境。

推荐项目：

* Jellyfin 家庭影音平台
* Nextcloud 私有云盘
* Grafana + Prometheus 监控平台
* GitLab 私有代码仓库
* Harbor 镜像仓库
* Kubernetes 实验集群

通过这些项目，你可以将学到的知识真正应用到实际场景中。

---

## 常见问题

### 我的电脑配置不高，可以学习吗？

一般情况下：

* CPU：4 核以上
* 内存：16 GB 以上
* SSD：256 GB 以上

即可完成绝大多数实验。

---

### 学 Linux 必须购买服务器吗？

不需要。

对于初学者来说：

```text
Windows
   ↓
VMware Workstation
   ↓
Ubuntu
```

已经足够完成大部分学习内容。

---

### 学 Kubernetes 需要先学 Docker 吗？

建议先掌握：

* Linux 基础
* Docker 基础

再学习 Kubernetes。

这样能够更容易理解容器和集群相关概念。

---

## 推荐阅读

建议按照以下顺序继续学习：

1. [Linux 和系统安装简介](../linux/linux-and-system-installation.md)
2. [裸金属、虚拟机与容器的区别](../deployment/basics/baremetal-vm-container.md)
3. [Ubuntu 22.04 安装教程]()
4. [Docker 安装教程]()
5. [Kubernetes 集群部署教程]()

---

## 关于 1HairLabs

**1HairLabs | 一根头发丝的宽度**

记录从传统运维到平台工程师成长过程中的学习、实践与思考。

内容涵盖：

* Linux
* VMware
* Kubernetes
* Docker
* Prometheus
* Grafana
* DevOps
* 平台工程

希望通过持续输出高质量原创内容，帮助更多技术爱好者快速成长。

欢迎收藏本站，一起探索技术世界。

![微信公众号](../assets/images/wechat-public/扫码_搜索联合传播样式-标准色版.png)
