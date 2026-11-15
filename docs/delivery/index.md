# 应用交付

以 1hairlabs.cn 为蓝本的 SRE 实践系列：生产站跑在 Cloudflare Pages 不动，
同一个仓库在集群里构建一套完全同构的"影子站"，让它走完 CI、制品库、
部署、灰度、GitOps 的全链路。

影子站的两位居民：静态站点（Deployment 双副本）和 Waline 评论系统
（StatefulSet + Ceph RBD 持久卷），都住在 worker03。

## 系列文章

- [从零点亮 CI：GitHub Actions 构建站点镜像，和两个半小时的海关仓](ci-lightup.md)

## 进行中

- 第一位居民 Waline 的入住排障（StatefulSet 死锁、500 误译、僵死循环）
- 滚动发布实验
- 灰度发布
- GitOps 收官
