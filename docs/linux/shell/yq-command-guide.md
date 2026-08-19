---
title: yq 命令详解：从 YAML/JSON 处理到 Kubernetes 配置自动化
description: 深入介绍 yq 的核心语法、过滤器、管道、YAML/JSON 处理方法和 Kubernetes 场景中的实战用法，帮助你高效处理配置文件和自动化脚本。
authors:
  - hfei
date: 2026-08-02
categories:
  - Linux
  - Shell
  - Kubernetes
tags:
  - yq
  - YAML
  - JSON
  - Shell
  - Linux
  - Kubernetes
  - 运维
---

# yq 命令详解：从 YAML/JSON 处理到 Kubernetes 配置自动化

YAML 是 Kubernetes、Helm、Ansible 等工具的核心配置格式。`grep` 和 `awk` 处理 YAML 的嵌套结构往往很痛苦——缩进层级、数组索引、多文档分隔，这些都不是文本工具擅长的。

`yq` 把 YAML 当作数据结构来处理，支持按层级提取字段、条件筛选、格式转换和原地修改。如果你已经熟悉 [jq](jq-command-guide.md)，yq 的学习曲线会非常顺滑。

本文以 mikefarah/yq（Go 版）v4 为例，所有命令均在测试集群（3 Master + 3 Worker，K8s 1.36.1）上实际运行验证。

## 准备数据

```bash
# 导出 kube-system 下所有 Deployment 的 YAML
kubectl get deployment -n kube-system -o yaml > /tmp/deploy.yaml

# 生成一个真正的多文档 YAML（Deployment + Service）
{ kubectl get deployment coredns -n kube-system -o yaml; \
  echo "---"; \
  kubectl get service kube-dns -n kube-system -o yaml; } > /tmp/multi.yaml
```

## 安装与版本陷阱

### 两个 yq，完全不同的工具

yq 有两个主流版本，语法不兼容：

| 版本 | 仓库 | 语言 | 语法风格 |
|------|------|------|----------|
| Go 版 | mikefarah/yq | Go | 自有语法，与 jq 类似但不完全一致 |
| Python 版 | kislyuk/yq | Python | jq 的 YAML 包装器，底层调用 jq |

**本文以 Go 版（mikefarah/yq v4）为例。** Python 版的语法不在本文讨论范围内。

### apt install yq 的坑

Ubuntu/Debian 仓库里的 `yq` 是 Python 版，不是 Go 版。直接 `apt install yq` 会装到错误的版本：

```bash
sudo apt update
sudo apt install yq
yq --version
```

输出看起来像版本号，但仔细看没有 `mikefarah` 字样。运行一下就能发现问题：

```bash
yq '.' /tmp/deploy.yaml | head -5
```

Python 版的输出是 **JSON 格式**（因为它底层就是 jq 的包装器），而 Go 版应该输出 **YAML 格式**。更明显的问题出现在使用 yq 专属语法时：

```bash
yq '.spec.replicas' /tmp/deploy.yaml
# null
```

返回 null，因为 `deploy.yaml` 是 `kubectl get deployment -n kube-system -o yaml` 的输出，根结构是列表（`items: []`），不是单个 Deployment。需要 `.items[0].spec.replicas` 才能取到值。这个问题两个版本都存在，但 Python 版还会报 jq 的错误：

```bash
yq '.spec.template.spec.containers[].image' /tmp/deploy.yaml
# jq: error (at <stdin>:1): Cannot iterate over null (null)
```

报错信息是 `jq: error`，因为 Python 版底层就是 jq。

### 正确安装 Go 版

从 GitHub Releases 下载二进制文件：

```bash
# 下载最新版（Linux amd64）
sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
sudo chmod +x /usr/local/bin/yq

# 验证版本
yq --version
```

输出应包含 `mikefarah` 和版本号：

```
yq (https://github.com/mikefarah/yq/) version v4.53.3
```

!!! warning "PATH 冲突"

    如果之前通过 `apt install yq` 安装过 Python 版，`/usr/bin/yq` 可能还在。`/usr/local/bin` 通常在 PATH 中优先级更高，但建议确认：

    ```bash
    which yq
    # /usr/local/bin/yq
    ```

    如果显示 `/usr/bin/yq`，说明 Python 版优先，需要 `sudo apt remove yq` 卸载。

### 其他平台

=== "macOS"

    ```bash
    brew install yq
    ```

=== "CentOS / Rocky / RHEL"

    ```bash
    # EPEL 仓库中的 yq 可能是 Python 版，建议用二进制方式安装
    sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
    sudo chmod +x /usr/local/bin/yq
    ```

## 基本工作方式

yq 的基本结构和 jq 一致：

```bash
yq '<过滤器>' <文件>
```

过滤器是用单引号包裹的表达式，描述"要从 YAML 中取什么数据"。例如：

```bash
yq '.' /tmp/deploy.yaml              # 输出整个文档
yq '.items[0].metadata.name' /tmp/deploy.yaml  # 取第一个 Deployment 的名称
```

yq 也可以从标准输入读取，方便和 kubectl 管道配合：

```bash
kubectl get deployment coredns -n kube-system -o yaml | yq '.spec.replicas'
```

## 核心过滤器

### 输出整个文档（`.`）

```bash
yq '.' /tmp/deploy.yaml | head -20
```

输出：

```yaml
apiVersion: v1
items:
  - apiVersion: apps/v1
    kind: Deployment
    metadata:
      annotations:
        deployment.kubernetes.io/revision: "1"
        kubectl.kubernetes.io/last-applied-configuration: |
          {"apiVersion":"apps/v1","kind":"Deployment",...}
      creationTimestamp: "2026-05-12T15:08:34Z"
```

Go 版输出 YAML 格式，Python 版输出 JSON 格式——这是区分两个版本最直观的方法。

### 取字段（`.field`）

`deploy.yaml` 是列表结构，需要通过 `.items[0]` 访问第一个元素：

```bash
yq '.items[0].spec.replicas' /tmp/deploy.yaml
# 1
```

!!! tip "先看结构再取字段"

    `kubectl get deployment -o yaml` 输出的是 `kind: List`，根字段是 `apiVersion`/`items`/`kind`/`metadata`。如果直接写 `.spec.replicas` 会返回 null，因为根对象没有 `spec` 字段——`spec` 在每个 `items[]` 元素里面。

### 取嵌套字段（`.field1.field2...`）

```bash
yq '.items[0].spec.selector.matchLabels."k8s-app"' /tmp/deploy.yaml
# calico-kube-controllers
```

!!! warning "字段名含特殊字符"

    字段名包含 `-` 时，必须用引号包裹：`."k8s-app"` 或 `.["k8s-app"]`。直接写 `.k8s-app` 会被解析为减法运算。

### 遍历数组（`.[]`）

```bash
yq '.items[] | .metadata.name' /tmp/deploy.yaml
```

输出：

```
calico-kube-controllers
coredns
headlamp
```

### 管道（`|`）

管道将前一个表达式的输出作为后一个表达式的输入，和 Shell 管道概念一致：

```bash
yq '.items[] | "\(.metadata.name): replicas=\(.spec.replicas)"' /tmp/deploy.yaml
```

输出：

```
calico-kube-controllers: replicas=1
coredns: replicas=2
headlamp: replicas=1
```

### 条件筛选（`select()`）

```bash
yq '.items[].spec.template.spec.containers[] | select(.image | test("calico")) | .name' /tmp/deploy.yaml
# calico-kube-controllers
```

这条命令遍历所有 Deployment 的所有容器，筛选出镜像名包含 "calico" 的容器，输出容器名。

### 提取所有容器镜像

```bash
yq '.items[].spec.template.spec.containers[].image' /tmp/deploy.yaml
```

输出：

```
m.daocloud.io/docker.io/calico/kube-controllers:v3.28.2
swr.cn-east-3.myhuaweicloud.com/coredns/coredns:v1.11.4
swr.cn-east-3.myhuaweicloud.com/helm/headlamp:v0.25.1
```

从镜像地址可以看出集群使用了多个镜像仓库——DaoCloud、华为云 SWR。升级前拿这个清单逐一确认兼容性。

### 构造新对象

和 jq 一样，yq 可以用 `{}` 构造新的输出对象：

```bash
yq '.items[] | {"name": .metadata.name, "replicas": .spec.replicas, "namespace": .metadata.namespace}' /tmp/deploy.yaml
```

输出：

```yaml
name: calico-kube-controllers
replicas: 1
namespace: kube-system
name: coredns
replicas: 2
namespace: kube-system
name: headlamp
replicas: 1
namespace: kube-system
```

### 其他常用操作

| 操作 | 语法 | 示例 |
|------|------|------|
| 数组长度 | `length` | `yq '.items \| length' /tmp/deploy.yaml` → `3` |
| 获取所有键 | `keys` | `yq '.items[0].metadata.labels \| keys' /tmp/deploy.yaml` |
| 排序 | `sort_by()` | `yq '.items \| sort_by(.metadata.name)' /tmp/deploy.yaml` |
| 去重 | `unique` | `yq '.items[].metadata.namespace \| unique' /tmp/deploy.yaml` |

### 输出纯文本（`-r`）

yq 默认输出带格式的 YAML。在 Shell 脚本中取值时，加 `-r` 输出纯文本：

```bash
# 不加 -r
yq '.items[0].spec.replicas' /tmp/deploy.yaml
# 1

# 加 -r（对简单值效果一样，但对字符串会去掉引号）
yq -r '.items[0].metadata.name' /tmp/deploy.yaml
# calico-kube-controllers
```

## 输出格式控制

### YAML 与 JSON 互转

```bash
# YAML 转 JSON
yq -o=json '.' /tmp/deploy.yaml | head -20

# JSON 转 YAML
kubectl get pods -A -o json | yq -o=yaml '.items[0]'
```

### 美化输出

```bash
yq -P '.' /tmp/deploy.yaml | head -30
```

`-P`（pretty print）会强制缩进 2 空格，适合调试格式不规范的 YAML。

## 修改 YAML

### 修改字段（预览）

不加 `-i`，修改结果只输出到终端，不写回文件：

```bash
# 修改前
yq '.items[0].spec.replicas' /tmp/deploy.yaml
# 1

# 修改后预览
yq '.items[0].spec.replicas = 5' /tmp/deploy.yaml | yq '.items[0].spec.replicas'
# 5

# 确认文件没变
yq '.items[0].spec.replicas' /tmp/deploy.yaml
# 1
```

### 写回文件（`-i`）

加 `-i`（in-place），修改直接写回文件：

```bash
yq -i '.items[0].spec.replicas = 99' /tmp/deploy.yaml
yq '.items[0].spec.replicas' /tmp/deploy.yaml
# 99
```

!!! warning "`-i` 是原地覆盖"

    `-i` 直接修改原文件，没有备份。对生产配置操作前先 `cp file file.bak`。

恢复原始文件：

```bash
kubectl get deployment -n kube-system -o yaml > /tmp/deploy.yaml
```

### 修改嵌套字段

```bash
yq '.items[0].spec.template.spec.containers[0].image = "calico/kube-controllers:v3.29.0"' /tmp/deploy.yaml | \
    yq '.items[0].spec.template.spec.containers[0].image'
# calico/kube-controllers:v3.29.0
```

### 删除字段（`del`）

```bash
yq 'del(.items[0].metadata.annotations)' /tmp/deploy.yaml | head -20
```

输出中第一个 Deployment 的 `annotations` 字段被移除，其他内容不变。

### 新增字段

```bash
yq '.items[0].metadata.labels."test-label" = "true"' /tmp/deploy.yaml | \
    yq '.items[0].metadata.labels'
```

输出：

```yaml
k8s-app: calico-kube-controllers
pod-template-hash: 7b44d8d7c8
test-label: "true"
```

## 多文档 YAML 处理

多文档 YAML 用 `---` 分隔，常见于 Helm 模板和 `kubectl` 输出。这是 yq 相对于纯文本工具的核心优势之一。

### 什么是多文档 YAML

```bash
cat /tmp/multi.yaml | head -5
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coredns
---
apiVersion: v1
kind: Service
metadata:
  name: kube-dns
```

两个文档之间用 `---` 分隔。

### 按文档索引访问

```bash
# 取第一个文档的类型
yq 'select(documentIndex == 0) | .kind' /tmp/multi.yaml
# Deployment

# 取第二个文档的类型
yq 'select(documentIndex == 1) | .kind' /tmp/multi.yaml
# Service
```

### 遍历所有文档

yq v4 默认对每个文档执行表达式。不需要 `.[]` 遍历文档：

```bash
yq '"\(.kind)/\(.metadata.name)"' /tmp/multi.yaml
```

输出：

```
Deployment/coredns
Service/kube-dns
```

!!! warning "yq 和 jq 的 `.[]` 语义不同"

    jq 中 `.[]` 遍历数组元素。yq 中 `.[]` 遍历对象的值（不是文档）。跨文档遍历时不需要 `.[]`，直接写表达式即可。

### 文档计数

```bash
# 统计非空文档数量
yq '.kind' /tmp/multi.yaml | grep -c .
# 2
```

!!! note "kubectl 输出的尾部空文档"

    `kubectl get deployment,service -o yaml` 会在末尾产生一个空文档（`---` 后面没有内容），`yq 'length'` 会把空文档也算进去。用 `grep -c .` 只统计有内容的行更准确。

## Kubernetes 实战示例

### 提取所有 Deployment 的副本数

```bash
yq '.items[] | "\(.metadata.name): replicas=\(.spec.replicas)"' /tmp/deploy.yaml
```

输出：

```
calico-kube-controllers: replicas=1
coredns: replicas=2
headlamp: replicas=1
```

### 提取所有容器镜像

```bash
yq '.items[].spec.template.spec.containers[].image' /tmp/deploy.yaml
```

输出：

```
m.daocloud.io/docker.io/calico/kube-controllers:v3.28.2
swr.cn-east-3.myhuaweicloud.com/coredns/coredns:v1.11.4
swr.cn-east-3.myhuaweicloud.com/helm/headlamp:v0.25.1
```

### 按条件筛选容器

```bash
# 找出镜像名包含 calico 的容器
yq '.items[].spec.template.spec.containers[] | select(.image | test("calico")) | .name' /tmp/deploy.yaml
# calico-kube-controllers
```

### YAML 与 JSON 互转

```bash
# 把 YAML 输出转成 JSON（方便和其他工具配合）
kubectl get deployment coredns -n kube-system -o yaml | yq -o=json '.spec.replicas'
# 2

# 把 JSON 输出转成 YAML（方便阅读）
kubectl get pods -A -o json | yq -o=yaml '.items[0].metadata.labels'
```

## Shell 脚本实战

### 读取副本数用于判断

```bash
#!/bin/bash
# check_replicas.sh - 检查 Deployment 副本数

REPLICAS=$(yq -r '.items[0].spec.replicas' /tmp/deploy.yaml)

if [ "$REPLICAS" -lt 2 ]; then
    echo "警告: 副本数 $REPLICAS，建议至少 2 个"
else
    echo "副本数正常: $REPLICAS"
fi
```

### 批量提取镜像清单

```bash
#!/bin/bash
# list_images.sh - 提取所有容器镜像并去重排序

yq -r '.items[].spec.template.spec.containers[].image' /tmp/deploy.yaml | sort -u
```

输出：

```
m.daocloud.io/docker.io/calico/kube-controllers:v3.28.2
swr.cn-east-3.myhuaweicloud.com/coredns/coredns:v1.11.4
swr.cn-east-3.myhuaweicloud.com/helm/headlamp:v0.25.1
```

### 批量修改配置

```bash
#!/bin/bash
# batch_update.sh - 批量修改多个 YAML 文件的副本数

for file in deploy-*.yaml; do
    echo "处理 $file..."
    yq -i '.spec.replicas = 3' "$file"
done
```

## 常见踩坑

### 坑一：Python 版和 Go 版语法不兼容

| 现象 | 原因 | 解决 |
|------|------|------|
| `yq '.'` 输出 JSON | 装到了 Python 版（kislyuk/yq） | 安装 Go 版（mikefarah/yq） |
| 报错信息是 `jq: error` | Python 版底层就是 jq | 同上 |
| `yq --version` 没有 mikefarah | 不是 Go 版 | 同上 |

### 坑二：字段名含特殊字符

```bash
# 错误：yq 把 - 解析为减法
yq '.items[0].metadata.labels.k8s-app' /tmp/deploy.yaml
# Error: bad expression

# 正确写法一：引号包裹
yq '.items[0].metadata.labels."k8s-app"' /tmp/deploy.yaml

# 正确写法二：方括号语法
yq '.items[0].metadata.labels["k8s-app"]' /tmp/deploy.yaml
```

### 坑三：List 结构的路径访问

`kubectl get deployment -o yaml` 输出的是 `kind: List`，不是单个 Deployment：

```bash
# 错误：根对象没有 spec 字段
yq '.spec.replicas' /tmp/deploy.yaml
# null

# 正确：通过 items[0] 访问第一个元素
yq '.items[0].spec.replicas' /tmp/deploy.yaml
# 1
```

### 坑四：多文档 YAML 的 `.[]` 语义

```bash
# 错误：.[] 遍历的是对象 value，不是文档
yq '.[] | "\(.kind)/\(.metadata.name)"' /tmp/multi.yaml
# 输出乱码或 null

# 正确：直接写表达式，yq 自动对每个文档执行
yq '"\(.kind)/\(.metadata.name)"' /tmp/multi.yaml
# Deployment/coredns
# Service/kube-dns
```

### 坑五：`-i` 直接覆盖无备份

```bash
# 危险：直接覆盖原文件
yq -i '.spec.replicas = 99' deployment.yaml

# 安全：先备份
cp deployment.yaml deployment.yaml.bak
yq -i '.spec.replicas = 99' deployment.yaml
```

## 最佳实践

**先看结构再取字段。** 拿到 YAML 先 `yq '.'` 格式化看结构，确认层级关系后再写过滤器。比直接猜路径高效得多。

**脚本中用 `-r`。** 用变量接收 yq 输出时，不加 `-r` 可能带上引号，导致后续字符串匹配失败。

**预览后再写回。** 先不加 `-i` 跑一遍看输出，确认结果正确后再加 `-i` 写回文件。

**确认版本再查文档。** 网上教程可能是 Python 版语法。先 `yq --version` 确认版本，再对照对应文档。

## 语法速查

| 操作 | 语法 | 示例 |
|------|------|------|
| 输出整个文档 | `.` | `yq '.' file.yaml` |
| 取字段 | `.field` | `yq '.metadata.name' file.yaml` |
| 取嵌套字段 | `.a.b.c` | `yq '.spec.replicas' file.yaml` |
| 取数组元素 | `[0]` | `yq '.items[0]' file.yaml` |
| 遍历数组 | `.[]` | `yq '.items[]' file.yaml` |
| 管道 | `\|` | `yq '.items[] \| .name' file.yaml` |
| 条件筛选 | `select()` | `yq 'select(.kind == "Deployment")' file.yaml` |
| 构造对象 | `{}` | `yq '{name: .metadata.name}' file.yaml` |
| 修改字段 | `=` | `yq '.spec.replicas = 5' file.yaml` |
| 删除字段 | `del()` | `yq 'del(.metadata.annotations)' file.yaml` |
| 按文档索引 | `select(documentIndex == N)` | 取第 N 个文档 |
| 输出 JSON | `-o=json` | `yq -o=json '.' file.yaml` |
| 输出纯文本 | `-r` | `yq -r '.metadata.name' file.yaml` |
| 写回文件 | `-i` | `yq -i '.spec.replicas = 5' file.yaml` |
| 美化输出 | `-P` | `yq -P '.' file.yaml` |

## 相关阅读

- [jq 命令详解](jq-command-guide.md)：处理 JSON 的工具，与 yq 配合使用
- [文本处理三剑客](text-processing.md)：grep、sed、awk 基础
