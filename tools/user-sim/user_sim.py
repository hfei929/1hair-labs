#!/usr/bin/env python3
"""user-sim: 影子站常驻流量模拟器（CI 链第二位顾客）

常驻行为:
  - 读路径: 每 20s GET 影子站首页一次 (0.05 QPS)
  - 写路径: 每 360s POST 一条 waline 评论 (约 0.003 QPS), 固定昵称 user-sim
  - burst:  环境变量 BURST=1 时以 1 QPS 跑 BURST_SECONDS 秒后回到常驻节奏
四指标:
  - usersim_requests_total{kind, code}    累计请求计数 (kind=read/write)
  - usersim_request_duration_seconds      请求延迟直方图 (kind 标签)
  - usersim_last_cycle_ok                 最近一轮读路径是否全通 (1/0)
  - usersim_write_fail_total              写路径累计失败数 (waline 面板直读)
"""

import json
import os
import time
import urllib.error
import urllib.request

from prometheus_client import Counter, Gauge, Histogram, start_http_server

READ_URL = os.environ.get("USER_SIM_READ_URL", "http://site.hairlabs-site.svc.cluster.local/")
WRITE_URL = os.environ.get("USER_SIM_WRITE_URL", "http://waline.hairlabs-site.svc.cluster.local:8360/api/comment")
WRITE_PAGE = os.environ.get("USER_SIM_WRITE_PAGE", "/delivery/ci-lightup/")
METRICS_PORT = int(os.environ.get("USER_SIM_METRICS_PORT", "8000"))
READ_INTERVAL = float(os.environ.get("USER_SIM_READ_INTERVAL", "20"))   # 常驻 0.05 QPS
WRITE_INTERVAL = float(os.environ.get("USER_SIM_WRITE_INTERVAL", "360"))
BURST = os.environ.get("BURST", "0") == "1"
BURST_SECONDS = float(os.environ.get("BURST_SECONDS", "60"))
BURST_QPS = float(os.environ.get("BURST_QPS", "1"))
TIMEOUT = 5

requests_total = Counter(
    "usersim_requests_total", "user-sim requests", ["kind", "code"]
)
duration = Histogram(
    "usersim_request_duration_seconds", "request latency", ["kind"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
last_cycle_ok = Gauge("usersim_last_cycle_ok", "last read cycle fully ok (1/0)")
write_fail = Counter("usersim_write_fail_total", "waline write path failures")


def http_get(url):
    start = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            code = str(resp.status)
            resp.read()
    except urllib.error.HTTPError as e:
        code = str(e.code)
    except Exception:
        code = "error"
    duration.labels(kind="read").observe(time.monotonic() - start)
    requests_total.labels(kind="read", code=code).inc()
    return code


def http_post_comment(seq):
    body = json.dumps({
        "comment": "user-sim 流量探测 #%d @%d" % (seq, int(time.time())),
        "nick": "user-sim",
        "mail": "user-sim@1hairlabs.cn",
        "url": WRITE_PAGE,
        "path": WRITE_PAGE,
        "pid": "",
        "rid": "",
    }).encode()
    req = urllib.request.Request(
        WRITE_URL, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = str(resp.status)
            resp.read()
    except urllib.error.HTTPError as e:
        code = str(e.code)
    except Exception:
        code = "error"
    duration.labels(kind="write").observe(time.monotonic() - start)
    requests_total.labels(kind="write", code=code).inc()
    if code != "200":
        write_fail.inc()
    return code


def main():
    start_http_server(METRICS_PORT)
    print("user-sim up, metrics on :%d" % METRICS_PORT, flush=True)
    print("read=%s write=%s page=%s" % (READ_URL, WRITE_URL, WRITE_PAGE), flush=True)

    seq = 0
    last_write = 0.0
    if BURST:
        print("burst mode: %s qps for %ss" % (BURST_QPS, BURST_SECONDS), flush=True)
        deadline = time.monotonic() + BURST_SECONDS
        while time.monotonic() < deadline:
            code = http_get(READ_URL)
            last_cycle_ok.set(1 if code == "200" else 0)
            time.sleep(1.0 / BURST_QPS)
        print("burst done, back to steady", flush=True)

    while True:
        seq += 1
        code = http_get(READ_URL)
        last_cycle_ok.set(1 if code == "200" else 0)
        now = time.monotonic()
        if now - last_write >= WRITE_INTERVAL:
            last_write = now
            wcode = http_post_comment(seq)
            print("write #%d -> %s" % (seq, wcode), flush=True)
        time.sleep(READ_INTERVAL)


if __name__ == "__main__":
    main()
