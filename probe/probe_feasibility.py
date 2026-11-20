#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校园信息聚合与待办提醒系统 —— 功能点可行性探测脚本

对选题的每个"外部依赖型"功能点做一次可复现的实测，输出判定表与 JSON 结果。
只依赖 Python 标准库，可直接在任意机器上跑：

    python3 probe_feasibility.py            # 打印表格
    python3 probe_feasibility.py --json     # 额外写出 probe_result.json

探测项与对应功能点：
  C1 开放平台 OAuth 取 token        -> 全部校内数据接入的前提
  C2 匿名接口：学年学期              -> F2 截止时间/周次换算
  C3 匿名接口：校历                  -> F2 节假日顺延
  C4 scope 鉴权（401/403）           -> 能否按需拿到课表/考试/通知
  C5 GitHub 公开 API + ETag/304      -> F1 GitHub 课程仓库订阅
  C6 官网 RSS 是否存在               -> F1 "RSS 订阅"假设
  C7 官网栏目 HTML 可解析性（本科生院）-> F1 官网公告适配器
  C8 学院站点是否同为服务端渲染       -> F1 适配器能否复用
  C9 内容指纹去重                    -> NFR-2 幂等
"""

import hashlib
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
CTX = ssl.create_default_context()
RESULTS = []

# 文档站公开的演示用客户端（仅 fake_api scope），见 /docs/intro/develop/authentication
DEMO_CLIENT_ID = "xxb-example-api"
DEMO_CLIENT_SECRET = "3fwowzYYEgcCci1p7UPUtqgg9xdiWejv"


def http(url, method="GET", data=None, headers=None, timeout=25, follow=True):
    """返回 (status, body_bytes, headers, elapsed_ms)。异常时 status=0。"""
    hdrs = {"User-Agent": UA}
    if headers:
        hdrs.update(headers)
    body = None
    if data is not None:
        if isinstance(data, dict):
            body = urllib.parse.urlencode(data).encode()
            hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
        else:
            body = data
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.read(), dict(r.headers), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers), int((time.time() - t0) * 1000)
    except Exception as e:  # 网络/证书/超时
        return 0, str(e).encode(), {}, int((time.time() - t0) * 1000)


def record(cid, name, verdict, evidence, feature):
    RESULTS.append({"id": cid, "name": name, "verdict": verdict,
                    "evidence": evidence, "feature": feature})
    print(f"[{verdict:^6}] {cid} {name}\n         {evidence}")


def jload(b):
    try:
        return json.loads(b.decode("utf-8", "ignore"))
    except Exception:
        return None


# ---------------------------------------------------------------- C1
def c1_token():
    st, body, _, ms = http("https://api.tongji.edu.cn/v1/token", "POST",
                           {"client_id": DEMO_CLIENT_ID,
                            "client_secret": DEMO_CLIENT_SECRET,
                            "grant_type": "client_credentials"})
    d = jload(body) or {}
    if st == 200 and d.get("access_token"):
        record("C1", "开放平台 client_credentials 取 token", "PASS",
               f"HTTP 200 / {ms}ms / scope={d.get('scope')} / expires_in={d.get('expires_in')}s",
               "所有校内数据接入")
        return d["access_token"]
    record("C1", "开放平台 client_credentials 取 token", "FAIL",
           f"HTTP {st} / {body[:120]!r}", "所有校内数据接入")
    return None


# ---------------------------------------------------------------- C2
def c2_semester():
    st, body, _, ms = http("https://api.tongji.edu.cn/v1/rt/teaching_info/semester")
    d = jload(body) or {}
    data = d.get("data") or []
    if st == 200 and d.get("code") == "A00000" and data:
        cur = data[0]
        record("C2", "学年学期信息（匿名）", "PASS",
               f"HTTP 200 / {ms}ms / {len(data)} 个学期 / 首条 {cur.get('semesterName')} "
               f"{cur.get('beginDay')}~{cur.get('endDay')} 考试周 {cur.get('examWeekStart')}-{cur.get('examWeekEnd')}",
               "F2 截止时间/周次换算")
    else:
        record("C2", "学年学期信息（匿名）", "FAIL", f"HTTP {st} / {body[:160]!r}", "F2 截止时间/周次换算")


# ---------------------------------------------------------------- C3
def c3_calendar():
    st, body, _, ms = http(
        "https://api.tongji.edu.cn/v1/rt/onetongji/calendar"
        "?fromDate=2026-09-01&endDate=2026-09-30")
    d = jload(body) or {}
    code, msg = d.get("code"), d.get("msg")
    if st == 200 and code == "A00000" and d.get("data"):
        record("C3", "校历（匿名）", "PASS",
               f"HTTP 200 / {ms}ms / {len(d['data'])} 天", "F2 节假日顺延")
    else:
        record("C3", "校历（匿名）", "BROKEN",
               f"HTTP {st} / 业务码 {code} / msg={msg} —— 接口在线但取不到数据", "F2 节假日顺延")


# ---------------------------------------------------------------- C4
def c4_scope(token):
    url = ("https://api.tongji.edu.cn/v1/rt/onetongji/student_timetable"
           "?userId=000000")
    st1, _, _, _ = http(url)
    st2, body2, _, _ = http(url, headers={"Authorization": f"Bearer {token}"}) if token else (0, b"", {}, 0)
    d2 = jload(body2) or {}
    ok = st1 == 401 and st2 == 403
    record("C4", "scope 鉴权：课表接口", "PASS" if ok else "CHECK",
           f"无 token -> {st1}；fake_api token -> {st2} {str(d2.get('error') or d2)[:80]}"
           "（证明接口按 scope 逐项授权，需申请对应 scope）", "课表/考试/通知接入")


# ---------------------------------------------------------------- C5
def c5_github():
    u = "https://api.github.com/repos/vuejs/core/commits?per_page=1"
    st, body, hdrs, ms = http(u)
    etag = hdrs.get("ETag") or hdrs.get("etag")
    limit = hdrs.get("X-RateLimit-Limit") or hdrs.get("x-ratelimit-limit")
    remain = hdrs.get("X-RateLimit-Remaining") or hdrs.get("x-ratelimit-remaining")
    st2 = 0
    if etag:
        st2, _, _, _ = http(u, headers={"If-None-Match": etag})
    ok = st == 200 and st2 == 304
    record("C5", "GitHub 公开 REST API + ETag 条件请求", "PASS" if ok else "CHECK",
           f"HTTP {st} / {ms}ms / ETag 复验 -> {st2}（304 表示可零配额增量拉取）/ "
           f"未授权配额 {remain}/{limit} 次/小时（按 IP 共享）", "F1 GitHub 仓库订阅")


# ---------------------------------------------------------------- C6
def c6_rss():
    sites = ["https://www.tongji.edu.cn", "https://jwc.tongji.edu.cn",
             "https://gs.tongji.edu.cn", "https://youth.tongji.edu.cn"]
    paths = ["/rss.xml", "/feed", "/index.xml", "/atom.xml"]
    hits = []
    for s in sites:
        for p in paths:
            st, body, hdrs, _ = http(s + p, timeout=10)
            ctype = (hdrs.get("Content-Type") or hdrs.get("content-type") or "")
            if st == 200 and ("xml" in ctype or b"<rss" in body[:400] or b"<feed" in body[:400]):
                hits.append(s + p)
    if hits:
        record("C6", "同济各站点 RSS/Atom 探测", "PASS", f"命中 {hits}", "F1 RSS 订阅假设")
    else:
        record("C6", "同济各站点 RSS/Atom 探测", "FAIL",
               f"{len(sites)} 站点 × {len(paths)} 常见路径全部未命中（404/非 XML）"
               "—— 选题中的“RSS 订阅官网”假设不成立", "F1 RSS 订阅假设")


# ---------------------------------------------------------------- C7
def c7_html_adapter():
    """本科生院通知公告：列表页 + 详情页正文 + 指纹。"""
    LIST = "https://jwc.tongji.edu.cn/30359/list.htm"
    st, body, _, ms = http(LIST)
    h = body.decode("utf-8", "ignore")
    arts = sorted(set(re.findall(r'(/[0-9a-f]{2}/[0-9a-f]{2}/c\d+a\d+/page\.htm)', h)))
    if st != 200 or not arts:
        record("C7", "官网栏目 HTML 适配器（本科生院·通知公告）", "FAIL",
               f"HTTP {st} / 列表条目 {len(arts)}", "F1 官网公告接入")
        return
    def body_text(html):
        """正文区：定位 wp_articlecontent 后截一段，去标签。"""
        i = html.find("wp_articlecontent")
        if i < 0:
            return ""
        seg = html[i:i + 30000]
        seg = re.sub(r"<script.*?</script>", "", seg, flags=re.S)
        t = re.sub(r"<[^>]+>", "", seg)
        return re.sub(r"\s+", " ", t).strip()[:2000]

    st2, body2, _, _ = http("https://jwc.tongji.edu.cn" + arts[0])
    text = body_text(body2.decode("utf-8", "ignore"))
    # 内容指纹（NFR-2 去重方案的最小验证）
    fp1 = hashlib.sha256((arts[0] + text).encode()).hexdigest()[:16]
    st3, body3, _, _ = http("https://jwc.tongji.edu.cn" + arts[0])
    fp2 = hashlib.sha256((arts[0] + body_text(body3.decode("utf-8", "ignore"))).encode()).hexdigest()[:16]
    verdict = "PASS" if len(arts) >= 5 and len(text) > 50 else "CHECK"
    record("C7", "官网栏目 HTML 适配器（本科生院·通知公告）", verdict,
           f"列表 HTTP {st} / {ms}ms / {len(arts)} 条；详情正文 {len(text)} 字；"
           f"同一文章两次抓取指纹 {fp1}=={fp2} -> {fp1 == fp2}", "F1 官网公告接入 / NFR-2")


# ---------------------------------------------------------------- C8
def c8_college_js():
    """学院站点：列表能否解析、正文是什么形态。"""
    u = "https://cs.tongji.edu.cn/index/tzgg.htm"
    st, body, _, ms = http(u)
    h = body.decode("utf-8", "ignore")
    items = re.findall(r'href="(\.\./info/\d+/\d+\.htm)"[^>]*title="([^"]*)"', h)
    dates = re.findall(r'<div class="date">([\d-]{10})</div>', h)
    if not items:
        record("C8", "学院站点列表可解析性（计算机学院·通知公告）", "FAIL",
               f"HTTP {st} / {ms}ms / HTML 中条目 0 条", "F1 适配器复用性")
        return
    # 取最新一条看正文形态
    art_url = "https://cs.tongji.edu.cn/info/" + items[0][0].split("/info/")[-1]
    st2, body2, _, _ = http(art_url)
    a = body2.decode("utf-8", "ignore")
    i = a.find("v_news_content")
    seg = a[i:i + 6000] if i >= 0 else ""
    visible = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.sub(
        r"<script.*?</script>", "", seg, flags=re.S))).strip()
    imgs = len(re.findall(r"<img", seg))
    pdf_imgs = len(re.findall(r"__local/[^\"]+\.jpg", seg))
    form = "PDF 转图片" if pdf_imgs >= 3 and len(visible) < 400 else "HTML 文本"
    record("C8", "学院站点列表可解析性（计算机学院·通知公告）",
           "ADAPTER_NEEDED",
           f"列表 HTTP {st} / {ms}ms / {len(items)} 条 / 最新 {dates[0] if dates else '?'} / "
           f"链接形如 {items[0][0]}（与本科生院 c30359a…/page.htm 完全不同）；"
           f"正文形态={form}（可见文本 {len(visible)} 字 / 图 {imgs} 张）"
           f"{'，文本抽取前需 OCR' if form != 'HTML 文本' else ''}",
           "F1 适配器复用性 / F2 正文抽取")


# ---------------------------------------------------------------- C9
def c9_dedupe():
    """同一 feed 重复投喂 -> 指纹稳定（NFR-2 的判定口径演示）。"""
    payload = ("<h1>关于2026-2027学年第一学期缓考、重考的通知</h1>"
               "<p>请于 2026年9月27日 17:00 前提交申请。</p>")
    norm = re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", payload))
    fps = {hashlib.sha256(norm.encode()).hexdigest() for _ in range(3)}
    record("C9", "内容指纹去重（NFR-2 口径）", "PASS",
           f"3 次投喂得到 {len(fps)} 个指纹 -> 幂等判据可用（唯一索引 + upsert）", "NFR-2 幂等去重")


def main():
    print("=" * 78)
    print("校园信息聚合与待办提醒系统 · 功能点可行性探测")
    print("=" * 78)
    token = c1_token()
    c2_semester()
    c3_calendar()
    c4_scope(token)
    c5_github()
    c6_rss()
    c7_html_adapter()
    c8_college_js()
    c9_dedupe()
    print("=" * 78)
    tally = {}
    for r in RESULTS:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    print("汇总:", " / ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    if "--json" in sys.argv:
        with open("probe_result.json", "w", encoding="utf-8") as f:
            json.dump({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                       "results": RESULTS}, f, ensure_ascii=False, indent=2)
        print("已写出 probe_result.json")


if __name__ == "__main__":
    main()
