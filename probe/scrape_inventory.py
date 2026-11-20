#!/usr/bin/env python3
"""抓取同济开放平台全部接口文档页，产出机器可读的接口清单 CSV。

用法: python3 scrape_inventory.py [--out api_inventory.csv]
仅依赖标准库。
"""
import csv, json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

BASE = "https://api.tongji.edu.cn/docs/interface"
UA = {"User-Agent": "Mozilla/5.0 (compatible; tj-feasibility-probe/1.0)"}


def get(url, timeout=40, retries=2):
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception:
            if i == retries:
                return ""
            time.sleep(1.5)


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "header", "footer"):
            self.skip += 1
        if tag in ("p", "div", "li", "tr", "br", "h1", "h2", "h3", "td", "th"):
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "header", "footer") and self.skip:
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)


def text_of(html):
    # 只取 <article> 区域，去掉导航噪声
    m = re.search(r"<article[^>]*>(.*?)</article>", html, re.S)
    seg = m.group(1) if m else html
    p = Text(); p.feed(seg)
    t = "".join(p.out)
    return re.sub(r"\n{2,}", "\n", t).strip()


def parse(link):
    url = f"https://api.tongji.edu.cn{link}"
    t = text_of(get(url))
    if not t:
        return {"path": link, "error": "fetch_failed"}
    rec = {"path": link, "url": url}
    m = re.search(r"(?:描述|注意事项)\n(.+?)\n(?:支持的模式|请求方法|注意事项)", t, re.S)
    rec["desc"] = re.sub(r"\s+", " ", m.group(1))[:200] if m else ""
    m = re.search(r"支持的模式\n(.+)", t)
    rec["modes"] = m.group(1).strip() if m else ""
    m = re.search(r"请求方法\n(\w+)", t)
    rec["method"] = m.group(1) if m else ""
    m = re.search(r"请求地址\n(\S+)", t)
    rec["endpoint"] = m.group(1) if m else ""
    m = re.search(r"数据来源\n(\S+)", t)
    rec["source_sys"] = m.group(1) if m else ""
    m = re.search(r"最近更新时间[:：]\s*(\S+)", t)
    rec["doc_updated"] = m.group(1) if m else ""
    rec["anonymous"] = "无需授权" in rec["modes"]
    rec["params"] = ""
    pm = re.search(r"请求(?:体)?参数\n(.*?)(?:返回参数|请求示例)", t, re.S)
    if pm:
        names = re.findall(r"([A-Za-z][A-Za-z0-9_]{1,30})(?:string|int|ARRAY|OBJECT|number|array|object|boolean)", pm.group(1))
        seen, out = set(), []
        for n in names:
            if n not in seen:
                seen.add(n); out.append(n)
        rec["params"] = ",".join(out[:12])
    return rec


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "api_inventory.csv"
    home = get(BASE)
    links = sorted(set(re.findall(r'href="(/docs/interface/[^"#?]+)"', home)))
    print(f"接口页数: {len(links)}", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(parse, links))
    cols = ["path", "method", "endpoint", "modes", "anonymous", "source_sys", "params", "desc", "doc_updated", "error", "url"]
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    ok = [r for r in rows if not r.get("error")]
    anon = [r for r in ok if r.get("anonymous")]
    print(f"抓取成功 {len(ok)}/{len(rows)}；匿名可直连 {len(anon)} 个", file=sys.stderr)
    for r in anon:
        print("  匿名:", r["method"], r["endpoint"], "|", r["desc"][:50], file=sys.stderr)


if __name__ == "__main__":
    main()
