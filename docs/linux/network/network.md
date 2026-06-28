# Linux 网络管理：从配置到排障的十八般武艺

网络是 Linux 系统的命脉。无论是配置 IP 地址、诊断连接问题，还是设置防火墙规则，网络管理都是每位 Linux 管理员的基本功。本文将带你掌握现代 Linux 网络栈的核心工具（`ip`、`ss`、`nftables` 等），并分享真实运维中的经验与教训。

!!! tip "工欲善其事，必先利其器"
    还在用 `ifconfig` 和 `route`？这些工具虽然经典，但在现代 Linux 发行版中已逐渐被 `ip` 命令取代。我的习惯是：**新系统只用 `ip` 系列**（`ip addr`、`ip link`、`ip route`），因为它的输出更一致，脚本友好。当然，`ifconfig` 顺手也可以，但建议尽早切换。

---

## 一、网络接口与地址配置

### 查看网络接口

```bash
# 现代方式
ip addr show          # 或简写 ip a
ip link show          # 查看接口状态（UP/DOWN）
ip -br addr           # 简洁输出（仅 IP）

# 传统方式（需安装 net-tools）
ifconfig -a
```

### 配置 IP 地址（临时，重启失效）

```bash
# 给 eth0 添加 IP
sudo ip addr add 192.168.1.100/24 dev eth0

# 启用/禁用接口
sudo ip link set eth0 up
sudo ip link set eth0 down

# 删除 IP
sudo ip addr del 192.168.1.100/24 dev eth0
```

### 永久配置（不同发行版差较大）

#### Debian

Debian 默认使用 `/etc/network/interfaces` 文件进行网络配置（即使安装了 NetworkManager，服务器版通常仍保留此方式）。

```bash
# 编辑 /etc/network/interfaces
sudo vim /etc/network/interfaces
```

配置示例（静态 IP）：

```bash
# 回环接口
auto lo
iface lo inet loopback

# 以太网接口 eth0
auto eth0
iface eth0 inet static
    address 192.168.1.100/24
    gateway 192.168.1.1
    dns-nameservers 8.8.8.8 1.1.1.1
```

若使用 DHCP ：

```bash
auto eth0
iface eth0 inet dhcp
```

应用配置：`sudo systemctl restart networking` 或 `sudo ifdown eth0 && sudo ifup eth0`。

#### Ubuntu（Netplan 方式）

Ubuntu 从 18.04 LTS 开始默认使用 **Netplan**，配置文件位于 `/etc/netplan/` 目录下（如 `01-netcfg.yaml`）。

```yaml
# /etc/netplan/01-netcfg.yaml
network:
  version: 2
  renderer: networkd   # 或 NetworkManager（桌面版常用）
  ethernets:
    eth0:
      dhcp4: true
      # 静态配置示例（注释掉 dhcp4，使用 addresses 等）：
      # addresses:
      #   - 192.168.1.100/24
      # gateway4: 192.168.1.1
      # nameservers:
      #   addresses: [8.8.8.8, 1.1.1.1]
```

应用配置：`sudo netplan apply`。

#### RHEL / Fedora（两种配置方式）

RHEL 及衍生发行版（CentOS、Rocky、AlmaLinux）支持两种主流配置方式：**NetworkManager**（推荐，尤其桌面）和 **传统 network-scripts**（ifcfg 文件）。较新版本（RHEL 8+）已逐步废弃 network-scripts，但多数仍可用。

##### 方式一：nmcli 命令行（推荐）

```bash
# 添加一个连接（若已有连接可修改）
sudo nmcli connection add type ethernet ifname eth0 con-name myeth

# 配置静态 IP
sudo nmcli connection modify myeth ipv4.addresses 192.168.1.100/24
sudo nmcli connection modify myeth ipv4.gateway 192.168.1.1
sudo nmcli connection modify myeth ipv4.dns "8.8.8.8 1.1.1.1"
sudo nmcli connection modify myeth ipv4.method manual

# 启用连接
sudo nmcli connection up myeth
```

##### 方式二：ifcfg 文件（传统方式）

配置文件位于 `/etc/sysconfig/network-scripts/ifcfg-<接口名>`，例如 `ifcfg-eth0`。

```bash
# 编辑配置文件
sudo vim /etc/sysconfig/network-scripts/ifcfg-eth0
```

静态 IP 配置示例：

```ini
TYPE=Ethernet
BOOTPROTO=static
NAME=eth0
DEVICE=eth0
ONBOOT=yes
IPADDR=192.168.1.100
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
DNS1=8.8.8.8
DNS2=1.1.1.1
```

若使用 DHCP：

```ini
BOOTPROTO=dhcp
ONBOOT=yes
```

重启网络服务（RHEL 7/8/9）：

```bash
sudo systemctl restart network
# 或者重启 NetworkManager（如果使用 NM 接管）
sudo systemctl restart NetworkManager
```

!!! tip "殊途同归，各有所爱"
    有些老运维习惯 ifcfg 文件，因为简单直观、无依赖；而 nmcli 更强大，支持复杂配置（bond、bridge、team）。我的经验是：**服务器如果不需要频繁变更网络，用 ifcfg 文件足够；如果需要动态切换（VPN、容器网络），nmcli 更胜一筹**。另外，两种方式不可混用：如果你通过 nmcli 配置了连接，再手动修改 ifcfg 文件可能被 NetworkManager 覆盖。可以用 `nmcli device status` 查看接口是否被 NM 管理。

## 二、路由与默认网关

### 查看路由表

```bash
ip route show          # 或 ip r
route -n               # 传统
```

### 添加/删除静态路由

```bash
# 添加通过 192.168.1.1 到 10.0.0.0/24 的路由
sudo ip route add 10.0.0.0/24 via 192.168.1.1 dev eth0

# 删除
sudo ip route del 10.0.0.0/24

# 添加默认网关
sudo ip route add default via 192.168.1.1 dev eth0
```

### 永久路由配置

- Debian/Ubuntu (Netplan)：在配置中加入 `routes:`
  ```yaml
  routes:
    - to: 10.0.0.0/24
      via: 192.168.1.1
  ```
- RHEL/Fedora (nmcli)：`sudo nmcli connection modify myeth +ipv4.routes "10.0.0.0/24 192.168.1.1"`

!!! tip "路漫漫其修远兮，吾将上下而求索"
    当网络不通时，**`traceroute`（或 `mtr`）** 是你的好朋友。它能告诉你数据包在哪一跳丢失或延迟高。我曾经遇到一个奇怪的问题：能 ping 通外网 IP，但无法 SSH 到某台云服务器。最后用 `mtr --report` 发现是运营商某节点丢包严重，后来切了 VPN 就好了。

---

## 三、网络连接与端口监听

### 查看监听端口和连接状态

```bash
# 现代方式（推荐）
ss -tuln              # 显示所有 TCP/UDP 监听端口（-t tcp, -u udp, -l listening, -n numeric）
ss -tunp              # 显示所有连接，并显示进程名（需 sudo）

# 传统方式（netstat，可能需安装）
netstat -tuln
netstat -tunp
```

### 检查某端口是否被占用

```bash
ss -tlnp | grep :80
lsof -i :80           # 也可以使用 lsof
```

### 发起连接测试

```bash
# 测试 TCP 端口连通性
nc -zv 192.168.1.1 22        # -z 只扫描不发送数据，-v 详细
telnet 192.168.1.1 22        # 传统工具，Ctrl+] 退出

# 测试 HTTP 服务
curl -I http://example.com
wget -O- http://example.com | head
```

!!! tip "未雨绸缪，防患于未然"
    在部署服务前，先 `ss -tlnp` 确认端口没有被占用，避免端口冲突。同时，记得检查防火墙（详见后面章节）。一个常见陷阱：服务进程正在运行，`ss` 也能看到监听端口，但从外部就是连不上——90% 的情况是防火墙或云安全组没放行。所以排障顺序：本地 `ss` → 本机防火墙 → 外部防火墙。

---

## 四、DNS 解析与配置

### 查看 DNS 配置

```bash
cat /etc/resolv.conf
systemd-resolve --status        # 如果使用 systemd-resolved
resolvectl status                # 新版命令
```

### 修改 DNS 服务器（临时）

```bash
sudo echo "nameserver 8.8.8.8" > /etc/resolv.conf
# 注意：重启网络服务或 DHCP 更新后会覆盖
```

### 永久配置

- **Netplan**：在 `nameservers` 下设置
- **NetworkManager**：`nmcli con mod myeth ipv4.dns "8.8.8.8 1.1.1.1"`
- **传统 ifupdown**：编辑 `/etc/network/interfaces`，添加 `dns-nameservers 8.8.8.8`

### 测试 DNS

```bash
# 使用 dig 或 nslookup
dig baidu.com
nslookup baidu.com

# 指定 DNS 服务器查询
dig @8.8.8.8 google.com
```

!!! tip "差之毫厘，谬以千里"
    DNS 配置错误会导致域名无法解析，但 `ping 8.8.8.8` 却是通的。我总是首先检查 `/etc/resolv.conf` 是否正确。另外，如果你使用了 VPN，它可能会覆盖 DNS 设置，导致内网域名解析异常。此时可以尝试 `nmcli con mod your_vpn ipv4.ignore-auto-dns yes` 来手动指定。

---

## 五、网络诊断工具集

| 工具 | 作用 | 常用示例 |
|------|------|----------|
| `ping` | 测试连通性和延迟 | `ping -c 4 8.8.8.8` |
| `traceroute` | 跟踪路由路径 | `traceroute -n google.com` |
| `mtr` | 实时结合 ping 和 traceroute | `mtr 8.8.8.8` |
| `nmap` | 端口扫描和安全审计 | `nmap -sS -p 1-1000 192.168.1.1` |
| `tcpdump` | 抓包分析 | `sudo tcpdump -i eth0 -n port 80` |
| `tshark` | 命令行版 Wireshark | `sudo tshark -i eth0 -Y "http.request"` |
| `iperf3` | 测速带宽 | `iperf3 -c server_ip` |

### 综合排障示例

```bash
# 1. 检查接口是否 UP
ip link show eth0

# 2. 检查 IP 配置
ip addr show eth0

# 3. 检查默认路由
ip route show

# 4. 测试到网关的连通性
ping -c 3 192.168.1.1

# 5. 测试外网 IP
ping -c 3 8.8.8.8

# 6. 测试 DNS
dig google.com +short

# 7. 测试具体服务端口
nc -zv 1.1.1.1 53
```

!!! tip "他山之石，可以攻玉"
    当常规命令无法定位问题时，**`tcpdump` 或 `wireshark`** 能让你看到数据包的“庐山真面目”。例如，SSH 连接不上，抓包发现服务器返回了 RST，说明服务拒绝连接，可能是防火墙或服务未启动。我习惯在怀疑网络层问题时，直接 `sudo tcpdump -i any host <目标IP> -nn -v`，观察三次握手是否完成。

---

## 六、防火墙管理（nftables / iptables / firewalld）

现代 Linux 发行版逐步从 `iptables` 迁移到 `nftables`。RHEL 8+、Fedora 使用 `firewalld`（基于 nftables），Ubuntu 22.04+ 仍常用 `ufw` 或直接 `nftables`。

### UFW（Ubuntu 简单防火墙）

```bash
# 启用
sudo ufw enable

# 默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许 SSH
sudo ufw allow 22/tcp

# 允许特定 IP
sudo ufw allow from 192.168.1.100 to any port 80

# 查看状态
sudo ufw status verbose
```

### firewalld（RHEL/Fedora）

```bash
# 查看当前区域和规则
sudo firewall-cmd --list-all

# 永久开放端口
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# 添加源 IP 白名单
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" accept'
```

### nftables（通用底层）

nftables 语法更清晰，支持集合、映射等。

```bash
# 查看当前规则集
sudo nft list ruleset

# 添加简单规则（允许 SSH）
sudo nft add rule inet filter input tcp dport 22 accept
```

!!! tip "小心驶得万年船"
    配置防火墙时，**永远不要把自己锁在外面**。尤其是在远程管理的服务器上，先放行 SSH（端口 22），或者通过带外管理（iDRAC、IPMI）保持一个备用通道。我有个习惯：`ufw allow from <我的IP> to any port 22`，然后再 `ufw enable`，这样就算不小心禁止了 SSH，我自己的 IP 仍能连上。如果是 firewalld，可以先设置 `--runtime-to-permanent` 确认无误再永久生效。

---

## 七、网络性能与监控

### 查看网络统计

```bash
# 接口流量统计
ip -s link show eth0
# 或使用 ifconfig
ifconfig eth0

# 实时流量（nload、iftop、bmon）
sudo iftop -i eth0
sudo nload eth0

# 查看网络连接数
ss -s

# 查看套接字内存
ss -m
```

### 修改网络内核参数（sysctl）

```bash
# 查看当前 TCP 相关参数
sysctl net.ipv4.tcp_keepalive_time

# 临时修改（重启失效）
sudo sysctl -w net.ipv4.tcp_tw_reuse=1

# 永久修改（编辑 /etc/sysctl.conf）
echo "net.ipv4.tcp_tw_reuse = 1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

!!! tip "冰冻三尺，非一日之寒"
    网络性能问题往往由多个小问题累积而成。比如高并发下 `TIME_WAIT` 连接过多导致端口耗尽，需要调整 `net.ipv4.ip_local_port_range` 和 `net.ipv4.tcp_tw_reuse`。我曾在压测时遇到连接失败，用 `ss -s` 发现大量 TIME_WAIT，通过调优这些内核参数才解决。

---

## 八、无线网络与网络管理器

对于笔记本或工作站，通常会使用 NetworkManager 来管理 WiFi 和移动网络。

```bash
# 查看 WiFi 设备状态
nmcli radio wifi

# 扫描 WiFi
nmcli dev wifi list

# 连接 WiFi
nmcli dev wifi connect "SSID" password "password"

# 查看所有连接
nmcli con show

# 删除连接
nmcli con delete "SSID"
```

!!! tip "入乡随俗"
    在服务器上，通常禁用 NetworkManager，使用 `systemd-networkd` 或传统网络脚本，减少资源占用。但在桌面环境，NetworkManager 是很好的助手。如果你在笔记本上使用 Linux，建议保留 NetworkManager，并安装 `network-manager-applet` 图形界面。

---

## 九、常见网络故障与解决案例

| 现象 | 可能原因 | 排查命令 | 解决方法 |
|------|----------|----------|----------|
| `ping 8.8.8.8` 不通 | 网线未插、接口 down | `ip link show` | `sudo ip link set eth0 up` |
| 能 ping IP，无法解析域名 | DNS 配置错误 | `cat /etc/resolv.conf` | 修改 DNS 服务器 |
| 端口被占用 | 服务已在运行 | `ss -tlnp \| grep :80` | 修改服务端口或停止冲突进程 |
| SSH 连接缓慢 | DNS 反向解析 | `systemctl status sshd` | 在 `/etc/ssh/sshd_config` 中设置 `UseDNS no` |
| 大量丢包 | 网络拥塞或硬件问题 | `mtr` | 升级链路或更换网卡 |
| IP 冲突 | 静态 IP 被占用 | `arping -I eth0 192.168.1.100` | 更换 IP 或 DHCP |

!!! tip "亡羊补牢，犹未迟也"
    记录每次故障和解决过程。我维护一个“网络排障笔记”，按现象归档命令和配置。比如“VPN 连接后路由表混乱”的解决方案，已经帮我解决了很多次重复问题。建议你也用 Markdown 维护一个类似文档。

---

## 十、实战练习

1. **配置静态 IP**：在虚拟机中为第二块网卡配置静态 IP，并测试 ping 网关。
2. **端口监听实验**：用 `nc -l -p 12345` 监听一个端口，从另一台机器 `telnet` 连接，用 `ss` 查看连接状态。
3. **防火墙规则**：设置 UFW 或 firewalld，仅允许 22 端口，然后尝试用 `nmap` 扫描。
4. **抓包分析**：启动 `tcpdump -i lo -nn`，然后执行 `curl localhost`，观察三次握手和 HTTP 包。
5. **路由追踪**：运行 `mtr --report baidu.com`，分析哪一跳延迟最高。
6. **DNS 调试**：用 `dig +trace` 查看域名解析完整过程。

!!! tip "实践出真知"
    以上练习最好在两台虚拟机或 Docker 容器之间进行。我建议你搭建一个最小实验环境：一个 Ubuntu + 一个 Fedora，互相 ping 通，然后逐步添加路由、防火墙、隧道等。遇到问题时的痛苦和解决后的喜悦，才是真正的学习过程。

---

## 总结

Linux 网络管理涵盖配置、诊断、防火墙、性能调优等多个层面。核心工具演变到今天，`ip`、`ss`、`nftables` 是新一代的“三驾马车”。记住以下几点：

- **分层排查**：物理层（网卡灯/up）→ 链路层（ARP）→ 网络层（路由）→ 传输层（端口）→ 应用层（服务）
- **善用现代工具**：`ip` 代替 `ifconfig`，`ss` 代替 `netstat`，`nft` 代替 `iptables`
- **防火墙规则要谨慎**：特别是远程机器，先放行管理通道
- **记录排障过程**：形成自己的知识库

下一步，你可以学习 **系统监控**（Prometheus、node_exporter）、**日志管理**（journald、rsyslog）或 **系统安全**（SELinux、AppArmor）。网络是所有上层服务的基础，掌握好它，你会走得更远。

Happy Networking!