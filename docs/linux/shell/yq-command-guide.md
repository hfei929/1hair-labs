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

## 文章摘要

如果你已经熟悉了 jq，那么你很快就会发现：在 Linux 运维、Kubernetes 配置管理和自动化脚本中，另一个同样重要的工具就是 yq。

yq 的作用非常直观：

- 读取 YAML、JSON、TOML 等结构化数据
- 按层级提取字段
- 过滤、转换和重写配置内容
- 在 Shell 脚本和 Kubernetes 场景中批量处理配置

尤其是在 Kubernetes、Helm、Ansible、CI/CD 和配置自动化场景里，yq 可以说是“处理 YAML 的 jq”。

本文会从最基础的概念讲起，带你逐步掌握 yq 的常见语法、过滤器、修改配置的方式，以及与 kubectl、Helm、Shell 脚本结合的实战案例。

---

## 一、为什么要学 yq？

在现代运维和云原生场景中，YAML 几乎无处不在：

- Kubernetes 的 Deployment、Service、ConfigMap
- Helm 的 Chart 配置
- Ansible 的 playbook
- CI/CD 的流水线配置
- 大量基础设施和应用配置文件

很多人刚接触 YAML 时，会遇到一个典型问题：

> 我看着配置文件很清楚，但我怎么快速提取其中的某个字段？

例如，你可能想要这样做：

- 取出一个 Deployment 的副本数
- 提取所有容器镜像名
- 过滤出某个标签下的资源
- 修改一个值后再写回文件

如果你仅使用 `grep`、`sed`、`awk`，处理嵌套 YAML 往往会非常痛苦。yq 的价值就在于：

- 把 YAML 当成“数据结构”来处理
- 支持按层级访问字段
- 支持条件筛选和批量处理
- 能和 Shell 管道、kubectl、Helm 很好结合

---

## 二、yq 是什么？

yq 是一个命令行工具，用来处理 YAML、JSON、TOML 等格式的数据。它的核心思路和 jq 非常类似：

- 读取输入
- 使用过滤器选择内容
- 输出结果

最常见的用法就是：

```bash
yq '.spec.replicas' deployment.yaml
```

这条命令表示：

- 读取 deployment.yaml
- 取出其中 `spec.replicas` 的值
- 输出结果

如果你已经使用过 jq，就会非常容易理解 yq 的使用方式。

!!! warning "注意：yq 版本有两大流派"
    目前主流有两种 yq：

    - `mikefarah/yq`（Go 版，常见现代版本，本文以它为例）
    - `kislyuk/yq`（Python 版，语法和现代版略有差异）

    如果你从网上看到教程和你手上的命令不一致，先确认一下版本再继续。

---

## 三、yq 的安装

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install yq
```

### CentOS / Rocky / RHEL

```bash
sudo yum install yq
```

### macOS

```bash
brew install yq
```

### 验证安装

```bash
yq --version
```

如果看到版本号，说明安装成功。

---

## 四、yq 的基本工作方式

yq 的基本结构可以概括为：

```bash
yq '<过滤器>' <文件>
```

例如：

```bash
yq '.' deployment.yaml
```

这里的 `.` 表示“输出整个文档”。

如果你想取出某个字段：

```bash
yq '.metadata.name' deployment.yaml
```

这条命令会输出 YAML 中 `metadata.name` 的值。

---

## 五、yq 的最常见语法：从入门开始

### 5.1 输出整个 YAML

```bash
yq '.' deployment.yaml
```

这会把整个文件按标准格式输出。

### 5.2 取出单个字段

假设有如下 YAML：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
```

你可以这样取出副本数：

```bash
yq '.spec.replicas' deployment.yaml
```

输出结果：

```yaml
3
```

### 5.3 取出嵌套字段

```bash
yq '.spec.selector.matchLabels.app' deployment.yaml
```

输出：

```yaml
web
```

### 5.4 取数组中的元素

如果 YAML 中有数组：

```yaml
containers:
  - name: app
    image: nginx:1.25
  - name: sidecar
    image: busybox:1.36
```

你可以取出第一个容器：

```bash
yq '.spec.template.spec.containers[0]' deployment.yaml
```

### 5.5 遍历数组

```bash
yq '.spec.template.spec.containers[] | .name' deployment.yaml
```

这会把数组里的每个元素依次输出。

### 5.6 取对象中的所有键

```bash
yq '.metadata.labels | keys' deployment.yaml
```

这对于快速查看对象有哪些字段很有用。

---

## 六、yq 的核心过滤器：最常用的 10 个

下面这些是 yq 中最常用、最实用的语法。

### 6.1 `.`：当前输入

```bash
yq '.' deployment.yaml
```

### 6.2 `.field`：取对象字段

```bash
yq '.metadata.name' deployment.yaml
```

### 6.3 `.field1.field2`：取嵌套字段

```bash
yq '.spec.template.spec.containers[0].image' deployment.yaml
```

### 6.4 `.[]`：遍历数组或对象

```bash
yq '.items[]' file.yaml
```

### 6.5 `|`：管道

```bash
yq '.items[] | .metadata.name' file.yaml
```

这是 yq 最常见的组合之一，类似于 Shell 中的管道。

### 6.6 `select()`：条件筛选

```bash
yq '.items[] | select(.metadata.name == "web")' file.yaml
```

这会筛选出名字为 `web` 的对象。

### 6.7 `map()`：批量转换

```bash
yq '.items | map(.metadata.name)' file.yaml
```

可以用于把一组对象提取成一个名字列表。

### 6.8 `length`：求长度

```bash
yq '.items | length' file.yaml
```

### 6.9 `keys`：获取字段名

```bash
yq '.metadata.labels | keys' file.yaml
```

### 6.10 `-r`：输出纯文本

```bash
yq -r '.metadata.name' deployment.yaml
```

如果你想把结果直接用于 Shell 脚本，`-r` 非常实用。

---

## 七、yq 与 JSON 的关系

yq 不仅可以处理 YAML，还可以处理 JSON。事实上，很多时候你会发现：

- Kubernetes 的 `kubectl get ... -o json` 输出是 JSON
- 某些 API 返回值是 JSON
- 你在脚本里想统一处理配置和接口数据

这时 yq 也能派上用场。

例如：

```bash
kubectl get pods -o json | yq '.items[0].metadata.name'
```

或：

```bash
curl -s https://example.com/api | yq '.data[0].id'
```

从这个角度看，yq 就像是 YAML 世界里的 jq。

---

## 八、yq 的常见输出格式

### 8.1 默认输出

```bash
yq '.' file.yaml
```

### 8.2 输出为 JSON

```bash
yq -o=json '.' file.yaml
```

有些时候你需要把 YAML 转成 JSON，方便进一步交给脚本或其他工具处理。

### 8.3 输出为 YAML

```bash
yq -o=yaml '.' file.json
```

### 8.4 美化输出

```bash
yq -P '.' file.yaml
```

`-P` 会让输出更适合阅读，特别适合调试配置。

---

## 九、修改 YAML：yq 的写回能力

yq 的一个非常实用的能力是“修改并写回文件”。

### 9.1 修改单个字段

```bash
yq -i '.spec.replicas = 5' deployment.yaml
```

这会把 `replicas` 的值改成 `5`，并直接写回文件。

### 9.2 修改嵌套字段

```bash
yq -i '.spec.template.spec.containers[0].image = "nginx:1.27"' deployment.yaml
```

### 9.3 增加字段

```bash
yq -i '.metadata.labels.test = "true"' deployment.yaml
```

这类操作在批量调整配置时很实用。

!!! tip "谨慎修改配置文件"
    `-i` 是直接写回文件，适合你明确知道自己在做什么的场景。对于生产环境配置，建议先备份文件或者先用输出预览结果，确认无误后再写回。

---

## 十、结合 Kubernetes 的实战示例

### 10.1 提取 Deployment 的副本数

```bash
kubectl get deployment web -o yaml | yq '.spec.replicas'
```

### 10.2 提取所有容器镜像

```bash
kubectl get deployment web -o yaml | yq '.spec.template.spec.containers[].image'
```

### 10.3 提取所有 Pod 名称

```bash
kubectl get pods -o json | yq '.items[].metadata.name'
```

### 10.4 过滤出特定命名空间下的资源

```bash
kubectl get pods -A -o yaml | yq '.items[] | select(.metadata.namespace == "kube-system") | .metadata.name'
```

这类用法在日常运维中非常常见，尤其是你想快速从大量资源中定位某一类对象时。

---

## 十一、结合 Shell 脚本的实战示例

### 11.1 批量提取 Deployment 名称

```bash
kubectl get deploy -A -o yaml | yq '.items[].metadata.name'
```

### 11.2 统计资源数量

```bash
kubectl get pods -A -o yaml | yq '.items | length'
```

### 11.3 读取一个字段并用于脚本判断

```bash
replicas=$(kubectl get deployment web -o yaml | yq -r '.spec.replicas')
echo "当前副本数: $replicas"
```

### 11.4 自动筛选异常资源

```bash
kubectl get pods -A -o yaml | \
  yq '.items[] | select(.status.phase != "Running") | .metadata.namespace + "/" + .metadata.name'
```

这类脚本很适合用于巡检、告警和自动化运维。

---

## 十二、yq 的常见最佳实践

### 12.1 先看再改

在修改配置前，先用查询命令确认路径是否正确：

```bash
yq '.spec.template.spec.containers[0].image' deployment.yaml
```

### 12.2 对生产配置先备份

如果你准备用 `-i` 改写文件，建议先备份：

```bash
cp deployment.yaml deployment.yaml.bak
```

### 12.3 使用 `-r` 处理 Shell 脚本

当你希望把结果作为字符串传给脚本时，用 `-r`：

```bash
yq -r '.metadata.name' deployment.yaml
```

### 12.4 处理复杂 YAML 时，先用 `.` 看结构

```bash
yq '.' config.yaml
```

尤其在你不知道字段层级时，这一步非常重要。

### 12.5 版本差异要注意

如果你在网上看到某些写法和你本机不一致，优先确认 yq 的版本，避免踩坑。

---

## 十三、yq 的学习路线建议

如果你是第一次接触 yq，可以按下面顺序学习：

1. 先学会读取字段：`.field`、`.field1.field2`
2. 学会遍历数组：`.[]`、`[] |`
3. 学会条件筛选：`select()`
4. 学会修改配置：`-i` 和赋值语法
5. 再结合 kubectl、Helm 和 Shell 脚本实战

只要你掌握这几个步骤，就已经足够应付大多数运维工作了。

---

## 十四、总结

yq 是处理 YAML、JSON 和配置文件的利器。它的核心价值不是“看起来很高级”，而是：

- 在命令行里把结构化配置当作数据来处理
- 更高效地提取和修改字段
- 在 Kubernetes、Shell 脚本和自动化运维里大幅降低操作复杂度

如果你已经掌握了 jq，那么 yq 的学习曲线会非常顺滑。你只需要把“JSON 的思维方式”迁移到“YAML 的场景”，就能很快上手。

对于 Kubernetes 运维工程师来说，yq 不是“可有可无”的工具，而是非常值得长期掌握的命令行技能。
