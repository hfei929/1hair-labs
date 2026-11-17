---
title: 应用交付（CI/CD）：从源码构建到集群发布
description: 应用交付（CI/CD）实践栏目：以 1hairlabs.cn 为蓝本，在 Kubernetes 1.36.1 集群里构建同构影子站，实测 GitHub Actions 构建、GHCR 与 Harbor 双仓搬运、StatefulSet 与 Ceph RBD 部署，一路走到滚动发布与 GitOps。
keywords:
  - 应用交付
  - CI/CD
  - GitHub Actions
  - Harbor 镜像仓库
  - Kubernetes 部署
  - StatefulSet
  - 滚动发布
  - GitOps
hide:
  - comments
---

# 应用交付：从源码构建到集群发布

生产站 1hairlabs.cn 永久跑在 Cloudflare Pages 上，不动它。练兵的场地在集群里：同一个仓库、同一份构建，在 worker03 上跑一套完全同构的「影子站」——改一处，两边拿到的是同一个版本。

这样安排的理由很实际：**发布要有真实的消费方**。没有第二套环境接着镜像，就练不到"源码变了之后镜像怎么出去、新版本怎么上、出问题怎么退"。

影子站现在有两位居民：

| 居民 | 形态 | 位置 |
|---|---|---|
| 静态站点 | Deployment ×2（`imagePullPolicy: Always`）+ NodePort 30002 | worker03 |
| Waline 评论系统 | StatefulSet ×1 + Ceph RBD PVC（`data-waline-0`，2Gi）+ NodePort 30001 | worker03 |

## 链路走到哪了

按 CI/CD 五阶段记账，只记实测通过的：

| 阶段 | 状态 | 说明 |
|---|---|---|
| 源码管理 | ✅ | GitHub 仓库是唯一真相，生产站与影子站共用同一个源 |
| CI 构建 | ✅ | GitHub Actions 32 行 workflow：`mkdocs build` → `docker build` → 双 tag |
| 制品库 | ✅ | GHCR（外网）+ Harbor（内网 `192.168.114.136`）双仓 |
| CD 部署 | ⚠️ 半自动 | 镜像自动更新，`kubectl apply` 还得手动 |
| 运行时运维 | ✅ | 监控、日志、告警三件套 + Ceph 存储 |

差的那一格，就是接下来的主战场。

## 系列文章

| 篇 | 文章 | 事故与结论 |
|---|---|---|
| 1 | [从零点亮 CI：GitHub Actions 构建站点镜像，和两个半小时的海关仓](ci-lightup.md) | 空 requirements.txt、`content digest not found`（provenance 套娃）、GHCR → Harbor 两小时二十七分 |
| 2 | [影子站第一位居民：Waline 开光三幕战](waline-3acts.md) | `SQLITE_PATH` 被当成目录、StatefulSet 就绪门禁死锁、SQLite 分支不兜底 `JWT_TOKEN`、exit 137 |

## 接下来

- 滚动发布：Pod 怎么排队、老版本怎么退场、出问题怎么一刀回滚
- 灰度发布：读者会不会看见 404
- GitOps 收官：ArgoCD 接管部署阶段

## 相关栏目

- [Lab 实验室](../lab/index.md)：故障演练与测试集群生产化改造的全部家底
- [可观测性](../observability/index.md)：影子站的取证工具（Prometheus / Loki / Grafana）
- [Kubernetes 架构](../kubernetes/index.md)：Deployment、StatefulSet、Service 的机制背景
