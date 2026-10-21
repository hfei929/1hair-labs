# 一根头发丝的宽度（1Hair Labs）

记录 Kubernetes、Linux、可观测性与云原生运维的成长之路。

**在线站点：https://1hairlabs.cn**

本仓库是站点源码，push 到 main 后由 Cloudflare Pages 自动构建发布（MkDocs + Material for MkDocs）。

## 这里有什么

个人技术知识库与实验室。内容来自我自建的测试集群（3 master + 3 worker，Debian 13 + Calico），主要方向：

* Kubernetes 架构与网络（etcd、CNI、kube-proxy、Service、存储）
* 测试集群生产化改造系列（etcd 备份恢复、监控、告警双通道）
* 可观测性系列（Prometheus、Grafana、Loki、Mimir）
* Linux 运维
* 虚拟化平台（VMware vSphere / vSAN / PVE）

写作纪律：文章里的每条命令都亲自执行过，输出落盘存档，不虚构数据。

## 目录结构

```text
docs/
├── kubernetes/      # 架构、网络、存储
├── lab/             # 实验系列（带实测声明）
├── observability/   # 监控栈
├── linux/           # Linux 基础与进阶
├── virtualization/  # 虚拟化
├── deployment/      # 系统部署手册
└── ...              # 完整结构见站点导航
```

## 本地运行

```bash
pip install -r requirements.txt
mkdocs serve
```

然后访问 http://127.0.0.1:8000

## 关于作者

公众号：**一根头发丝的宽度**

![微信公众号](./docs/assets/images/wechat-public/扫码_搜索联合传播样式-标准色版.png)

持续记录从传统运维向云原生平台工程师成长过程中的实践与思考，欢迎交流。
