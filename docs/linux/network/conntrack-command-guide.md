---
title: conntrack 命令详解：连接追踪表的查看、解析与排障 | 1Hair Labs
description: 深入讲解 Linux conntrack 命令：连接追踪原理、conntrack -L/-E/-D/-F 等子命令、ORIGINAL/REPLY 条目格式解析、conntrack 与 NAT 的关系、nf_conntrack 表容量与内核参数调优，以及在 Kubernetes Service DNAT/SNAT 排查中的实战用法。
keywords:
  - conntrack
  - 连接追踪
  - netfilter
  - NAT
  - DNAT
  - SNAT
  - Kubernetes
  - 网络排障
---

# conntrack 命令详解：连接追踪表的查看、解析与排障

## 前言

在 Kubernetes 网络系列文章里，`conntrack` 这个词反复出现：Service 的 DNAT 靠它做反向 NAT、hairpin 和 NodePort 的 SNAT 靠它回包、DNS 查询的 UDP 流也靠它记录。但 `conntrack` 本身并不是 Kubernetes 的东西——它是 **Linux 内核连接追踪（Connection Tracking）模块的用户态查看工具**，属于 `conntrack-tools` 软件包。

理解 `conntrack`，是理解"为什么 DNAT 之后回包还能原路返回""为什么 Pod 访问 Service 不做 SNAT 而节点访问要做"这些问题的前提。本文从内核原理讲到命令实战，把散落在各篇 K8s 文章里的 conntrack 知识收拢成一篇完整的工具手册。

!!! tip "前置阅读"
    连接追踪与 iptables 的 NAT 表强相关。如果你还不熟悉五链四表，建议先读 [iptables 与 nftables 深度实战](iptables-nftables-deep.md)。

---

## 一、什么是连接追踪

### 1.1 内核里的"连接表"

Linux 内核的 Netfilter 框架里有一个 **conntrack** 模块，负责记录每一条经过本机的"流"（flow）。它不关心应用层内容，只记录这条流的**五元组**和**状态**：

| 字段 | 说明 |
| --- | --- |
| 协议 | TCP / UDP / ICMP |
| 源 IP、源端口 | 发起方向 |
| 目的 IP、目的端口 | 发起方向 |
| 反向五元组 | 回包方向（REPLY） |
| 状态 | TCP 状态机 / UDP 超时 |
| 标记 | `[ASSURED]`、`[UNREPLIED]` |

内核维护的这张表，就是 `conntrack` 命令查看的对象。`conntrack` 命令本身只是"读"（或删、或监控）这张表，真正的追踪逻辑在内核里。

### 1.2 为什么需要连接追踪

连接追踪解决两类核心问题：

1. **有状态防火墙**：只允许"已建立连接的回包"进来，而不必为每个回包单独写一条规则。这就是 iptables 里 `-m conntrack --ctstate ESTABLISHED,RELATED` 的由来。
2. **NAT 的反向转换**：做 DNAT/SNAT 时，内核必须记住"这个包原本的地址是什么"，回包才能改回原样。这条记忆就存在 conntrack 表里。

!!! info "conntrack 与 iptables 的关系"
    iptables 的 `nat` 表依赖 conntrack 才能工作——NAT 规则只匹配**流的第一个包**（NEW 状态），后续包靠 conntrack 记录自动转换，不再逐包走 NAT 规则。这也是为什么 `raw` 表的 `NOTRACK` 能"绕过连接追踪"来提升性能。

### 1.3 conntrack 条目的生命周期

一条 conntrack 条目从"第一个包"创建，到"超时回收"结束：

```mermaid
flowchart LR
    A["第一个包到达<br/>（NEW）"] --> B["创建 conntrack 条目<br/>标记 UNREPLIED"]
    B --> C["回包到达<br/>双向确认"]
    C --> D["标记 ASSURED<br/>进入稳定态"]
    D --> E["连接结束<br/>进入超时/关闭态"]
    E --> F["超时后回收<br/>释放表项"]

    classDef new fill:#DBEAFE,stroke:#2563EB,color:#0F172A
    classDef ass fill:#D1FAE5,stroke:#059669,color:#0F172A
    classDef end fill:#FEE2E2,stroke:#DC2626,color:#0F172A
    class A,B new
    class C,D ass
    class E,F end
```

TCP 有完整状态机（SYN_SENT → ESTABLISHED → TIME_WAIT → CLOSE），UDP 没有状态机，只有超时回收（默认 30 秒）。

---

## 二、安装 conntrack 工具

`conntrack` 命令来自 `conntrack-tools` 软件包，多数发行版默认**没装**，需要手动安装：

```bash
# Debian / Ubuntu
sudo apt install -y conntrack

# RHEL / Rocky / CentOS / Fedora
sudo dnf install -y conntrack-tools

# 验证安装
conntrack --version
# conntrack v1.4.8 (conntrack-tools): 199 flow entries have been shown.
```

!!! note "conntrack 与 conntrackd"
    `conntrack-tools` 包含两个工具：
    - `conntrack`：命令行查看/管理连接追踪表（本文主角）
    - `conntrackd`：用户态守护进程，用于**跨节点同步连接表**（高可用防火墙场景，如 Keepalived 主备切换时无缝接管连接）

---

## 三、读懂一条 conntrack 条目

先看最常用的命令和它最典型的输出：

```bash
sudo conntrack -L
```

```text
tcp      6 431999 ESTABLISHED src=10.244.5.12 dst=10.100.241.29 sport=34188 dport=80 src=10.244.5.12 dst=192.168.114.148 sport=80 dport=34188 [ASSURED] mark=0 use=1
```

这一行信息量很大，拆开看：

| 字段 | 含义 | 本例值 |
| --- | --- | --- |
| `tcp` | 协议 | TCP |
| `6` | 协议号（TCP=6，UDP=17，ICMP=1） | 6 |
| `431999` | 剩余超时时间（秒） | 431999s |
| `ESTABLISHED` | 连接状态 | 已建立 |
| 第一组 `src/dst/sport/dport` | **ORIGINAL 方向**（NAT 之前，应用层看到的地址） | Pod → ClusterIP:80 |
| 第二组 `src/dst/sport/dport` | **REPLY 方向**（NAT 之后，回包在网络上的真实地址） | Pod:80 → 节点 IP |
| `[ASSURED]` | 双向都确认过流量 | 已确认 |
| `mark` | 包标记（iptables MARK） | 0 |
| `use` | 引用计数 | 1 |

### 3.1 ORIGINAL 与 REPLY：NAT 的"前世今生"

这是理解 conntrack 最关键的约定：

- **ORIGINAL 方向**记录的是**发起方看到的地址**——NAT 之前。
- **REPLY 方向**记录的是**回包在网络上的真实地址**——NAT 之后。

以 DNAT（Service）为例：

```text
ORIGINAL: src=PodIP        dst=ClusterIP    （发起方看到 ClusterIP）
REPLY:    src=后端PodIP:80 dst=PodIP        （回包真实从后端 Pod 发出）
```

回包到达时，内核查到这条记录，执行**反向 NAT**：把 REPLY 的 `src` 从"后端 Pod IP"改回 ClusterIP，把 `dst` 从 Pod IP 改回发起方。对发起方来说，回包看起来就像 ClusterIP 直接回的。

### 3.2 状态字段：TCP 状态机

TCP 条目会经历完整的连接状态：

| 状态 | 说明 |
| --- | --- |
| `SYN_SENT` | 已发出 SYN，等待对方响应 |
| `SYN_RECV` | 已收到 SYN，连接建立中 |
| `ESTABLISHED` | 连接已建立 |
| `FIN_WAIT` / `CLOSE_WAIT` | 关闭握手进行中 |
| `TIME_WAIT` | 主动关闭方等待 2MSL（默认 120s） |
| `CLOSE` | 即将回收 |

UDP 和 ICMP 没有状态机，条目只显示超时时间。

### 3.3 `[ASSURED]` 与 `[UNREPLIED]`

- `[UNREPLIED]`：只看到了一个方向的包，回包还没来（刚创建、或丢包）。
- `[ASSURED]`：**双向都确认过流量**，条目进入稳定态，不易被提前回收。

排查"连接建不起来"时，如果条目一直停留在 `[UNREPLIED]`，通常说明回包没回来——可能是路由、防火墙或 DNAT 目标不可达。

---

## 四、常用命令与选项

### 4.1 `-L`：列出连接表

```bash
# 列出所有条目（表大时慎用，可能刷屏）
sudo conntrack -L

# 只看 TCP
sudo conntrack -L -p tcp

# 只看 UDP
sudo conntrack -L -p udp

# 过滤源/目的地址
sudo conntrack -L --src 10.244.5.12
sudo conntrack -L --dst 10.100.241.29

# 扩展格式：多显示字节数、包数
sudo conntrack -L -o extended
```

实战中更常见的做法是**直接 `grep` 关心的 IP**，例如在 K8s 节点上查某个 Service：

```bash
sudo conntrack -L | grep 10.100.241.29
```

### 4.2 `-E`：实时监控事件

`-E` 以事件流的方式输出新连接的创建、更新、销毁，适合"边造流量边看"：

```bash
sudo conntrack -E
```

输出：

```text
[NEW] tcp      6 120 SYN_SENT src=... dst=... sport=... dport=... [UNREPLIED] ...
[UPDATE] tcp   6 60 SYN_RECV src=... dst=... ...
[DESTROY] tcp  6 src=... dst=... ...
```

K8s 排查时常用它验证"这个请求到底有没有 DNAT 到预期的后端 Pod"。

### 4.3 `-C`：统计条目数

```bash
sudo conntrack -C
# 199
```

等价于读 `/proc/sys/net/netfilter/nf_conntrack_count`，但更直观。

### 4.4 `-D` 与 `-F`：删除与清空

```bash
# 删除某源 IP 的所有条目（常用于摘掉某台机器的连接）
sudo conntrack -D --src 10.244.5.12

# 删除某条具体流
sudo conntrack -D -p tcp --orig-src 10.244.5.12 --orig-dst 10.100.241.29 \
    --orig-sport 34188 --orig-dport 80

# 清空整个连接表（慎用！会中断所有已建立的 NAT 连接）
sudo conntrack -F
```

!!! danger "清空连接表有代价"
    `conntrack -F` 会立刻让所有走 NAT 的连接失去反向转换能力——正在进行的 SSH、数据库、Service 流量都会断。**生产环境不要随便执行**，除非你明确知道后果。

### 4.5 `-G`：精确查询某条流

```bash
sudo conntrack -G -p tcp --orig-src 10.244.5.12 --orig-dst 10.100.241.29 \
    --orig-sport 34188 --orig-dport 80
```

### 4.6 常用过滤参数速查

| 参数 | 说明 |
| --- | --- |
| `-p, --proto` | 按协议（tcp/udp/icmp） |
| `-s, --src` | 按源 IP |
| `-d, --dst` | 按目的 IP |
| `--sport` / `--dport` | 按源/目的端口 |
| `-o extended` | 扩展输出（字节/包数） |
| `-n` 无（默认数字输出，不做 DNS 反解） | — |

---

## 五、conntrack 与 NAT：怎么判断发生了 SNAT

这是 K8s 网络文章里最常引用的一段逻辑，单独拎出来讲清楚。

### 5.1 核心判据

**看 REPLY 方向的 `dst` 字段**：

- **没做 SNAT**：回包 `src=后端IP, dst=发起方真实IP`，REPLY 的 `dst` 就是发起方 IP。
- **做了 SNAT**：发起方源 IP 被改成节点 IP，回包 `src=后端IP, dst=节点IP`，REPLY 的 `dst` 是节点 IP。

一句话：**REPLY 方向出现节点 IP（或 tunl0 IP）= 发生了 SNAT；REPLY 方向是客户端真实 IP = 没有 SNAT。**

### 5.2 三种典型场景对照

| 场景 | ORIGINAL 方向 | REPLY 方向 | SNAT 证据 |
| --- | --- | --- | --- |
| 普通 DNAT（Pod 访问 Service） | `src=PodIP, dst=ClusterIP` | `src=后端Pod:80, dst=PodIP` | REPLY dst 是 Pod IP，无 SNAT |
| Hairpin（DNAT 选中自己） | `src=PodIP, dst=ClusterIP` | `src=Pod:80, dst=节点IP` | REPLY dst 是节点 IP，有 SNAT |
| NodePort Cluster 模式 | `src=客户端, dst=节点:NodePort` | `src=Pod:80, dst=接收节点IP` | REPLY dst 是接收节点，有 SNAT |
| NodePort Local 模式 | `src=客户端, dst=节点:NodePort` | `src=Pod:80, dst=客户端IP` | REPLY dst 是客户端，无 SNAT |

这些场景的完整 iptables 规则与实测数据，见 [Kubernetes SNAT 三种场景](../../kubernetes/architecture/network/snat-three-scenarios.md)。

---

## 六、conntrack 表容量与内核参数

### 6.1 表满了会怎样

conntrack 表是有容量上限的。满了之后内核会直接**丢弃新连接**，并在内核日志里刷：

```text
nf_conntrack: table full, dropping packet
```

在 K8s 高并发场景下（大量短连接 + NodePort + DNS 查询），这是常见的性能事故根因。每个 Pod 的每次 Service 访问至少产生 1~2 条条目，`ndots:5` 的 DNS 行为还会把 UDP 条目放大到 5 条。

### 6.2 查看当前使用量

```bash
# 当前条目数
sudo cat /proc/sys/net/netfilter/nf_conntrack_count

# 最大条目数
sudo cat /proc/sys/net/netfilter/nf_conntrack_max

# 哈希桶数量
sudo cat /proc/sys/net/netfilter/nf_conntrack_buckets
```

### 6.3 调大上限

```bash
# 临时调大（重启失效）
echo 262144 | sudo tee /proc/sys/net/netfilter/nf_conntrack_max

# 持久化：写入 sysctl 配置
echo "net.netfilter.nf_conntrack_max = 262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

!!! warning "max 与 buckets 的关系"
    在较新的内核上，`nf_conntrack_max` 与哈希桶数量 `nf_conntrack_buckets` 挂钩（`max ≈ buckets × 8`），而 `nf_conntrack_buckets` 是**模块加载时**决定的，运行期只读。若需要大幅调高，要用模块参数：

    ```bash
    # 卸载后带 hashsize 重新加载（需在无流量窗口操作）
    sudo modprobe -r nf_conntrack
    sudo modprobe nf_conntrack hashsize=32768
    ```

    并在 `/etc/modprobe.d/` 里固化该参数，否则重启后失效。

### 6.4 超时参数

各状态/协议的超时在 `/proc/sys/net/netfilter/` 下，常见的有：

```bash
# TCP TIME_WAIT 默认 120 秒
cat /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_time_wait

# UDP 流默认 30 秒
cat /proc/sys/net/netfilter/nf_conntrack_udp_timeout_stream

# ICMP 默认 30 秒
cat /proc/sys/net/netfilter/nf_conntrack_icmp_timeout
```

---

## 七、在 Kubernetes 排查中的实战

### 7.1 验证 Service DNAT 到了哪个后端

在 Node 上边造流量边查表：

```bash
# 终端 1：循环访问 Service
while true; do curl -s -o /dev/null http://10.100.241.29; done &

# 终端 2：查 conntrack，看 DNAT 到了哪个 Pod
sudo conntrack -L | grep 10.100.241.29
```

REPLY 方向的 `src` 就是被选中的后端 Pod IP。反复执行能看到 round-robin 分布到不同后端。

### 7.2 判断 hairpin / NodePort 是否做了 SNAT

按 [第五节](#conntrack-nat-snat) 的判据，看 REPLY 的 `dst` 是节点 IP 还是客户端 IP。

### 7.3 排查"偶发连接失败"

当出现偶发 `connection refused` 或超时时，按顺序查：

1. `sudo conntrack -C` 与 `nf_conntrack_max` —— 表是否接近满？
2. `dmesg | grep "table full"` —— 是否有丢包日志？
3. `sudo conntrack -L | grep <目标>` —— 条目是否一直 `[UNREPLIED]`（回包没回来）？

---

## 八、相关阅读

- [iptables 与 nftables 深度实战](iptables-nftables-deep.md)——conntrack 依赖的 netfilter 规则框架
- [Kubernetes SNAT 三种场景](../../kubernetes/architecture/network/snat-three-scenarios.md)——hairpin、节点访问、NodePort 三种 SNAT 的 conntrack 实测
- [一行 curl 的完整旅程](../../kubernetes/architecture/network/curl-full-link.md)——conntrack 证据：DNAT + round-robin + hairpin
- [Service ClusterIP 为什么 ping 不通？](../../kubernetes/architecture/network/clusterip-link-deep.md)——DNAT 与 conntrack 回包机制
