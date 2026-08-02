---
title: jq 命令详解：从语法到脚本实战的 JSON 处理指南
description: 深入介绍 jq 的核心语法、过滤器、管道、函数、脚本使用和最佳实践，帮助你在 Linux、Kubernetes、运维和自动化场景中高效处理 JSON 数据。
authors:
  - hfei
date: 2026-08-02
categories:
  - Linux
  - Shell
  - Kubernetes
tags:
  - jq
  - JSON
  - Shell
  - Linux
  - Kubernetes
  - 运维
---

# jq 命令详解：从语法到脚本实战的 JSON 处理指南

## 文章摘要

在现代 Linux 运维、Kubernetes 管理和自动化脚本中，JSON 已经变成了最常见的数据格式之一。

很多人第一次接触 jq，都会有同样的疑问：

- jq 到底是什么？
- 它和 `grep`、`awk`、`sed` 有什么区别？
- 为什么在 Kubernetes 场景里，`kubectl` 输出 JSON 时，jq 会特别常用？
- 我应该怎样从一堆复杂 JSON 中提取出我真正关心的数据？

本文从最基础的概念讲起，逐步带你掌握 jq 的核心语法、常见过滤器、管道用法、脚本编写方式和最佳实践。最后再结合 Kubernetes 场景，展示几个非常实用的使用案例。

---

## 一、为什么要学 jq？

JSON（JavaScript Object Notation）是现代系统最常见的数据交换格式之一。

你在以下场景中都会遇到它：

- `kubectl get pods -o json`
- `curl` 请求接口返回的 JSON 数据
- 配置文件、日志中出现的 JSON 结构
- CI/CD 流水线中处理 API 返回结果

如果你只会 `grep` 或 `awk`，处理 JSON 往往会变得很痛苦，因为 JSON 本质上是“层级结构化数据”，而不是简单的文本行。

jq 的核心价值在于：

- 把 JSON 当作“数据结构”来处理，而不是普通字符串
- 支持按层级提取字段
- 支持筛选、转换、格式化和聚合
- 能与 Shell 管道无缝结合

这也是为什么它在 Kubernetes 运维里非常常见。

---

## 二、jq 是什么？

jq 是一个命令行 JSON 处理器，最常见的用途是：

- 从 JSON 中筛选字段
- 过滤特定对象
- 输出成更适合阅读的格式
- 把 JSON 转成另一种结构

它的基本使用方式非常简单：

```bash
jq '.foo' data.json
```

这条命令的意思是：

- 从 `data.json` 读取 JSON
- 取出其中名为 `foo` 的字段
- 输出结果

如果你熟悉 Linux 管道，你会发现 jq 非常适合接在其他命令后面：

```bash
cat data.json | jq '.foo'
```

---

## 三、jq 的安装

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install jq
```

### CentOS / Rocky / RHEL

```bash
sudo yum install jq
```

### macOS

```bash
brew install jq
```

### 验证安装

```bash
jq --version
```

如果输出版本号，说明安装成功。

---

## 四、jq 的基本工作方式

jq 的核心思路可以概括为一句话：

> jq 读取 JSON，然后用“过滤器”去选择、转换、处理数据。

它的基本结构如下：

```bash
jq '<过滤器>' <输入文件>
```

例如：

```bash
jq '.name' user.json
```

这里的 `.name` 就是一个过滤器，表示取出 `name` 字段。

### 4.1 过滤器是什么？

过滤器是 jq 的核心语法。它类似于 SQL 的查询语句，或者 Python 中的对象访问语法。

例如：

- `.name`：取出对象中的 `name`
- `.items[]`：取出数组中的每一个元素
- `.items[] | .name`：遍历数组并取出每个元素的 `name`

---

## 五、jq 的最常见语法：从入门开始

### 5.1 直接输出整个 JSON

```bash
jq '.' data.json
```

这里的 `.` 表示“整个输入对象”。它的作用相当于“输出原始 JSON”。

### 5.2 取出字段

假设 JSON 长这样：

```json
{
  "name": "alice",
  "age": 28,
  "city": "Shanghai"
}
```

你可以这样取字段：

```bash
jq '.name' data.json
```

输出：

```json
"alice"
```

### 5.3 取出嵌套字段

```json
{
  "user": {
    "name": "alice",
    "age": 28
  }
}
```

```bash
jq '.user.name' data.json
```

输出：

```json
"alice"
```

### 5.4 取数组中的元素

```json
{
  "items": ["a", "b", "c"]
}
```

```bash
jq '.items[0]' data.json
```

输出：

```json
"a"
```

### 5.5 取数组的全部内容

```bash
jq '.items' data.json
```

### 5.6 遍历数组

```bash
jq '.items[]' data.json
```

它会逐个输出数组里的元素。

---

## 六、jq 的核心过滤器：最常用的 10 个

下面这些是 jq 里最常见、最实用的语法。

### 6.1 `.`：当前输入

```bash
jq '.' data.json
```

### 6.2 `.field`：取对象字段

```bash
jq '.name' data.json
```

### 6.3 `.field1.field2`：取嵌套字段

```bash
jq '.user.name' data.json
```

### 6.4 `.[index]`：取数组下标

```bash
jq '.[1]' data.json
```

### 6.5 `.[ ]` 或 `.[]`：遍历数组

```bash
jq '.[]' data.json
```

### 6.6 `|`：管道

```bash
jq '.items[] | .name' data.json
```

这条命令的意思是：

- 先取出 `items`
- 再对数组中的每个元素取 `.name`

### 6.7 `select()`：条件筛选

```bash
jq '.items[] | select(.active == true)' data.json
```

它会筛选出满足条件的元素。

### 6.8 `map()`：映射

```bash
jq '.items | map(.name)' data.json
```

作用是把每个元素都映射成它的 `name`。

### 6.9 `length`：统计长度

```bash
jq '.items | length' data.json
```

### 6.10 `keys`：取字段名

```bash
jq '. | keys' data.json
```

---

## 七、管道：jq 的真正威力所在

jq 最强的地方之一，就是它天生适合和 Shell 管道一起工作。

### 7.1 先取字段，再继续处理

```bash
jq '.items[] | .name' data.json
```

### 7.2 先筛选，再输出

```bash
jq '.items[] | select(.status == "Running") | .name' data.json
```

### 7.3 输出成更容易阅读的格式

```bash
jq '.items[] | {name, status}' data.json
```

这会输出一个更简洁的对象结构。

---

## 八、jq 的输出格式：默认、紧凑、漂亮

jq 默认输出格式是“格式化后的 JSON”，这对阅读很友好。

### 8.1 默认输出

```bash
jq '.name' data.json
```

### 8.2 紧凑输出

```bash
jq -c '.name' data.json
```

`-c` 表示 compact，输出一行，适合脚本和后续传输。

### 8.3 美化输出

```bash
jq '.name' data.json
```

默认输出本身已经比较易读。你也可以显式地用：

```bash
jq '.name' data.json
```

### 8.4 不带引号输出字符串

默认情况下，字符串会被输出为 JSON 字符串，例如：

```json
"alice"
```

如果你想输出纯文本，可以：

```bash
jq -r '.name' data.json
```

`-r` 表示 raw output，这样会输出：

```text
alice
```

这个选项在脚本中非常常用。

---

## 九、jq 的常用选项

### 9.1 `-r`：输出原始字符串

```bash
jq -r '.name' data.json
```

### 9.2 `-c`：紧凑一行输出

```bash
jq -c '.items' data.json
```

### 9.3 `-n`：不从文件读取，直接构造输入

```bash
jq -n '{name:"alice"}'
```

### 9.4 `-f`：从文件读取过滤器

```bash
jq -f filter.jq data.json
```

### 9.5 `-M`：禁用颜色输出

```bash
jq -M '.name' data.json
```

---

## 十、从简单例子理解 jq 的“对象”和“数组”

### 10.1 对象

```json
{
  "name": "alice",
  "age": 28
}
```

```bash
jq '.name' data.json
```

### 10.2 数组

```json
[
  {"name": "alice"},
  {"name": "bob"}
]
```

```bash
jq '.[0].name' data.json
```

### 10.3 复杂嵌套结构

```json
{
  "users": [
    {"name": "alice", "age": 28},
    {"name": "bob", "age": 32}
  ]
}
```

```bash
jq '.users[] | .name' data.json
```

这条命令会输出：

```text
alice
bob
```

---

## 十一、jq 的条件筛选：select() 的使用

`select()` 是 jq 中非常重要的“条件过滤”语法。

### 11.1 基础筛选

```json
{
  "items": [
    {"name": "a", "active": true},
    {"name": "b", "active": false}
  ]
}
```

```bash
jq '.items[] | select(.active == true)' data.json
```

输出：

```json
{"name":"a","active":true}
```

### 11.2 多条件筛选

```bash
jq '.items[] | select(.active == true and .age > 18)' data.json
```

### 11.3 取反筛选

```bash
jq '.items[] | select(.active != true)' data.json
```

---

## 十二、jq 的映射和转换：map()、foreach、reduce

### 12.1 map()

```bash
jq '.items | map(.name)' data.json
```

将数组中的每个元素都转换成其中的 `name`。

### 12.2 reduce()

```bash
jq '.items | map(.age) | add' data.json
```

这里的 `add` 会把数组内容加起来，适合做汇总。

### 12.3 组合使用

```bash
jq '.items | map(select(.active == true) | .name)' data.json
```

这类写法在脚本中非常有用。

---

## 十三、jq 的对象构造：生成新的 JSON

jq 不只是“读取”，它也可以“生成”新的 JSON。

### 13.1 生成一个简单对象

```bash
jq -n '{name:"alice", age:28}'
```

### 13.2 从旧对象构造新对象

```bash
jq '{name: .name, city: .city}' data.json
```

### 13.3 构造一个数组

```bash
jq '[.items[] | .name]' data.json
```

这在脚本中特别有用：

- 把复杂结果整理成更易读的结构
- 给后续脚本传递数据

---

## 十四、jq 在 Kubernetes 场景中的典型用法

Kubernetes 管理中，`kubectl` 的输出通常是 JSON。jq 在这里非常有用。

### 14.1 查看 Pod 列表并提取名称

```bash
kubectl get pods -o json | jq '.items[].metadata.name'
```

### 14.2 查看 Running 状态的 Pod

```bash
kubectl get pods -o json | jq '.items[] | select(.status.phase == "Running") | .metadata.name'
```

### 14.3 提取 Pod 的镜像

```bash
kubectl get pods -o json | jq '.items[] | {name: .metadata.name, image: .spec.containers[0].image}'
```

### 14.4 查找异常 Pod

```bash
kubectl get pods -o json | jq '.items[] | select(.status.phase != "Running") | {name: .metadata.name, phase: .status.phase}'
```

### 14.5 查看 Deployment 的副本数

```bash
kubectl get deployment nginx -o json | jq '{name: .metadata.name, replicas: .spec.replicas}'
```

这些示例是 jq 在实际生产环境里最常见的用法。

---

## 十五、jq 脚本实战：把它写进 Shell 脚本中

### 15.1 示例 1：统计 Pod 数量

```bash
#!/bin/bash
kubectl get pods -o json | jq '.items | length'
```

### 15.2 示例 2：列出所有异常 Pod

```bash
#!/bin/bash
kubectl get pods -o json | jq -r '.items[] | select(.status.phase != "Running") | .metadata.name'
```

### 15.3 示例 3：提取容器镜像并输出成表格

```bash
#!/bin/bash
kubectl get pods -o json | jq -r '.items[] | "\(.metadata.name) \(.spec.containers[0].image)"'
```

### 15.4 示例 4：筛选某个 Namespace

```bash
#!/bin/bash
kubectl get pods -n kube-system -o json | jq -r '.items[] | select(.status.phase == "Running") | .metadata.name'
```

---

## 十六、jq 的最佳实践

### 16.1 先想清楚你要什么数据

在处理 JSON 前，先问自己：

- 我需要的字段是什么？
- 我需要过滤哪些对象？
- 我是想输出文本、还是输出 JSON？

### 16.2 优先使用 `-r` 做脚本输出

如果要给后续 Shell 脚本使用，优先使用：

```bash
jq -r '.name' data.json
```

### 16.3 复杂语句尽量拆分

如果过滤条件太复杂，可以分成多步：

```bash
kubectl get pods -o json | jq '.items[] | select(.status.phase == "Running")' | jq '.metadata.name'
```

### 16.4 让输出结构更清晰

不要总是输出整个大对象。把它提炼成更小、更有用的结构：

```bash
jq '{name: .metadata.name, phase: .status.phase}'
```

### 16.5 对 JSON 先做格式化再看

```bash
jq '.' data.json
```

这经常比直接盯着一整段原始 JSON 更容易理解。

---

## 十七、jq 常见误区

### 误区 1：把 JSON 当成普通文本处理

这会导致看起来能“搜到”，但实际上很难正确提取字段。

### 误区 2：没搞清楚对象和数组的区别

对象用 `.field`，数组用 `.[]` 或 `[index]`。

### 误区 3：把 `jq` 当成“字符串替换工具”

jq 的本质不是替换文本，而是处理结构化 JSON。

### 误区 4：忽略了 `-r` 的重要性

如果你在脚本里需要纯文本内容，忘记 `-r` 会得到带引号的 JSON 字符串。

---

## 十八、总结：jq 的本质是什么？

jq 的本质可以概括为一句话：

> jq 是一个专门用于处理 JSON 的命令行过滤器和转换器。

它最适合以下场景：

- 从复杂 JSON 中提取字段
- 对数组和对象进行筛选
- 为脚本提供简洁、结构化的数据
- 在 Kubernetes、云原生、CI/CD 中高效处理 API 输出

如果你把它学会，你会发现：

- 处理 `kubectl` 输出会轻松很多
- 调试 API 返回结果会轻松很多
- 自动化脚本中处理 JSON 不再是噩梦

---

## 十九、相关阅读

| 文章 | 说明 |
| --- | --- |
| [Shell 基础入门](index.md) | 了解 Shell 与命令行基础 |
| [Linux 常用命令](../../base-system/common-commands.md) | 了解 Linux 中常见文本处理命令 |
| [Kubernetes CRI gRPC 调用详解](../../kubernetes/architecture/cri-grpc-deep.md) | 了解 Kubernetes 中常见的 JSON/接口调用场景 |

---

## 二十、后续建议

如果你想继续深入，下一步可以继续补以下内容：

- jq 中的 `if/then/else` 逻辑
- jq 中的函数定义与模块化写法
- 在脚本中通过 jq 生成更复杂的报告
- jq 与 `kubectl`、`curl`、`yq` 的组合使用

这类内容非常适合继续扩展成“jq 进阶篇”。
