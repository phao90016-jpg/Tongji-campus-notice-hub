# -*- coding: utf-8 -*-
"""生成用例总览图 SVG（精确控制布局）。

PlantUML 对 40 个用例的总览图布局不可用（实测排成 663x3759 细长条），
这里手工计算坐标，输出矢量 SVG，可直接放进文档或导入 draw.io 作为底图。
"""
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "models", "usecase", "usecase-overview.svg")

# ---------------- 数据 ----------------
# (模块代号, 模块名, [(用例号, 用例名)])
MODULES = [
    ("A", "认证与校内数据同步", [
        ("UC-01", "通过学校统一身份认证登录"),
        ("UC-02", "首次登录同步校内数据"),
        ("UC-03", "查看课程档案与周课表"),
        ("UC-04", "同步课表变更"),
        ("UC-05", "同步考试与补缓考安排"),
        ("UC-06", "查看考试安排"),
        ("UC-07", "同步教务通知"),
        ("UC-36", "同步毕设与实习节点"),
    ]),
    ("B", "统一通知流", [
        ("UC-08", "浏览与筛选通知流"),
        ("UC-09", "查看通知详情与原文"),
        ("UC-10", "标记通知已读或归档"),
        ("UC-35", "自动归类到课程与类型"),
    ]),
    ("C", "补充源与手动导入", [
        ("UC-11", "添加官网栏目源"),
        ("UC-12", "添加 GitHub 仓库源"),
        ("UC-13", "暂停或删除订阅源"),
        ("UC-14", "手动导入通知"),
        ("UC-15", "抓取并去重入库"),
    ]),
    ("D", "待办生成", [
        ("UC-16", "自动生成考试待办"),
        ("UC-17", "自动生成上课待办"),
        ("UC-18", "从节点记录生成待办"),
        ("UC-19", "导入一网通办待办"),
        ("UC-20", "从通知生成待办草稿"),
    ]),
    ("E", "待办管理", [
        ("UC-21", "确认与编辑待办"),
        ("UC-22", "更新待办状态"),
        ("UC-23", "删除待办"),
        ("UC-34", "登记与编辑课程作业"),
    ]),
    ("F", "提醒与日程", [
        ("UC-24", "设置提醒规则与渠道"),
        ("UC-25", "写入学校日程"),
        ("UC-26", "接收新消息与截止提醒"),
        ("UC-27", "检测改期并提示核对"),
    ]),
    ("G", "资料与检索", [
        ("UC-28", "收藏资料并添加标签"),
        ("UC-29", "关联资料到课程"),
        ("UC-30", "搜索通知与资料"),
    ]),
    ("H", "发布与后台", [
        ("UC-31", "发布班级通知并看阅读"),
        ("UC-32", "维护信息源与同步任务"),
        ("UC-33", "用户与角色管理"),
    ]),
    ("N", "非功能用例", [
        ("NFR-UC-01", "重复同步幂等去重"),
        ("NFR-UC-02", "越权访问拦截"),
        ("NFR-UC-03", "提醒准点送达"),
        ("NFR-UC-04", "首屏响应与同步时效"),
    ]),
]

# 主参与者：(id, 显示名, x, y, 侧)
MAIN_ACTORS = [
    ("STU", "学生", 96, 470, "L"),
    ("SCHED", "定时调度器", 96, 1080, "L"),
    ("PUB", "班委 / 组织干事", 1474, 470, "R"),
    ("ADM", "系统管理员", 1474, 900, "R"),
]
# 次参与者：(id, 显示名, x, y)
EXT_ACTORS = [
    ("SSO", "学校统一身份认证", 330, 116),
    ("OPEN", "开放平台数据接口", 700, 116),
    ("GH", "GitHub API", 1030, 116),
    ("WEB", "官网栏目", 1330, 116),
    ("WX", "微信服务号", 470, None),      # y 在算完边界后填
    ("MAIL", "邮件 SMTP", 800, None),
    ("CAL", "学校日程服务", 1150, None),
]

# 连接：参与者 -> 用例号
LINKS = {
    "STU": ["UC-01", "UC-03", "UC-06", "UC-08", "UC-09", "UC-10", "UC-11", "UC-12",
            "UC-13", "UC-14", "UC-21", "UC-22", "UC-23", "UC-24", "UC-26", "UC-28",
            "UC-29", "UC-30", "UC-34", "NFR-UC-02", "NFR-UC-04"],
    "PUB": ["UC-31"],
    "ADM": ["UC-32", "UC-33"],
    "SCHED": ["UC-02", "UC-04", "UC-05", "UC-07", "UC-15", "UC-16", "UC-17", "UC-18",
              "UC-19", "UC-20", "UC-25", "UC-27", "UC-35", "UC-36",
              "NFR-UC-01", "NFR-UC-03"],
    "SSO": ["UC-01"],
    "OPEN": ["UC-02", "UC-04", "UC-05", "UC-07", "UC-16", "UC-17", "UC-18", "UC-19",
             "UC-27", "UC-36"],
    "CAL": ["UC-25"],
    "WX": ["UC-26", "NFR-UC-03"],
    "MAIL": ["UC-26", "NFR-UC-03"],
    "GH": ["UC-12", "UC-15"],
    "WEB": ["UC-11", "UC-15"],
}

# ---------------- 布局参数 ----------------
COL_X = [400, 810, 1220]          # 三列用例中心
COL_MODULES = [["A", "B"], ["C", "D", "E"], ["F", "G", "H", "N"]]
ROW_H = 74
HEAD_H = 32
BAND_PAD = 10
TOP = 200                          # 系统边界上沿
RX, RY = 158, 30                   # 椭圆半径
BOUND_X0, BOUND_X1 = 196, 1400

W = 1560

# 计算每个用例的位置
pos = {}
band_rects = []
for ci, mids in enumerate(COL_MODULES):
    y = TOP + 24
    for mid in mids:
        mod = next(m for m in MODULES if m[0] == mid)
        band_top = y
        y += HEAD_H
        for code, name in mod[2]:
            pos[code] = (COL_X[ci], y + RY)
            y += ROW_H
        band_rects.append((COL_X[ci], band_top, y + BAND_PAD, mid, mod[1]))
        y += BAND_PAD

BOTTOM = max(b[2] for b in band_rects) + 20

# 底部外部参与者的 y 依赖边界高度，算完再填
for _i, (_aid, _label, _x, _y) in enumerate(EXT_ACTORS):
    if _y is None:
        EXT_ACTORS[_i] = (_aid, _label, _x, BOTTOM + 78)
H = BOTTOM + 230


def wrap(text, limit=13):
    """按字数折行，最多两行。"""
    if len(text) <= limit:
        return [text]
    cut = len(text) // 2
    # 找最近的合理断点
    for d in range(0, 4):
        for c in (cut + d, cut - d):
            if 0 < c < len(text):
                return [text[:c], text[c:]]
    return [text[:limit], text[limit:]]


def ellipse(cx, cy, code, name, is_nfr):
    fill = "#FFF6E9" if is_nfr else "#F2F8FD"
    stroke = "#B98A2E" if is_nfr else "#2C5F8A"
    out = [f'<ellipse cx="{cx}" cy="{cy}" rx="{RX}" ry="{RY}" fill="{fill}" '
           f'stroke="{stroke}" stroke-width="1.1"/>']
    lines = wrap(name)
    n = len(lines)
    # 垂直排版：代号 + 名称行
    total_h = 11 + n * 13
    y0 = cy - total_h / 2 + 9
    out.append(f'<text x="{cx}" y="{y0:.1f}" text-anchor="middle" font-size="8.5" '
               f'fill="#4C5F73">{escape(code)}</text>')
    for i, ln in enumerate(lines):
        out.append(f'<text x="{cx}" y="{y0 + 13 + i * 13:.1f}" text-anchor="middle" '
                   f'font-size="10.5" fill="#1B2A3A">{escape(ln)}</text>')
    return "".join(out)


def actor(x, y, label, stereo=None):
    """画 UML 小人 + 标签。"""
    out = [
        f'<circle cx="{x}" cy="{y - 22}" r="7" fill="none" stroke="#333" stroke-width="1.3"/>',
        f'<line x1="{x}" y1="{y - 15}" x2="{x}" y2="{y + 4}" stroke="#333" stroke-width="1.3"/>',
        f'<line x1="{x - 11}" y1="{y - 8}" x2="{x + 11}" y2="{y - 8}" stroke="#333" stroke-width="1.3"/>',
        f'<line x1="{x}" y1="{y + 4}" x2="{x - 9}" y2="{y + 20}" stroke="#333" stroke-width="1.3"/>',
        f'<line x1="{x}" y1="{y + 4}" x2="{x + 9}" y2="{y + 20}" stroke="#333" stroke-width="1.3"/>',
    ]
    ty = y + 40
    if stereo:
        out.append(f'<text x="{x}" y="{ty}" text-anchor="middle" font-size="8.5" '
                   f'fill="#7A5C1E">&#171;{escape(stereo)}&#187;</text>')
        ty += 13
    out.append(f'<text x="{x}" y="{ty}" text-anchor="middle" font-size="11" '
               f'fill="#1B2A3A">{escape(label)}</text>')
    return "".join(out)


def edge(x1, y1, x2, y2, color="#8A9AA8", dash=False):
    d = ' stroke-dasharray="4,3"' if dash else ""
    return (f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{color}" stroke-width="0.8" opacity="0.55"{d}/>')


parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" font-family="Microsoft YaHei, PingFang SC, sans-serif">')
parts.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
parts.append(f'<text x="{W/2}" y="34" text-anchor="middle" font-size="17" font-weight="bold" '
             f'fill="#172C44">面向大学生的校园待办中心 · 用例总览</text>')
parts.append(f'<text x="{W/2}" y="54" text-anchor="middle" font-size="10.5" fill="#4C5F73">'
             f'36 功能用例 + 4 非功能用例　主参与者 4 类　次参与者 7 类</text>')

# 系统边界
parts.append(f'<rect x="{BOUND_X0}" y="{TOP}" width="{BOUND_X1 - BOUND_X0}" '
             f'height="{BOTTOM - TOP}" fill="#FCFDFE" stroke="#2C5F8A" stroke-width="1.4" rx="6"/>')
parts.append(f'<text x="{(BOUND_X0 + BOUND_X1) / 2}" y="{TOP + 18}" text-anchor="middle" '
             f'font-size="12" fill="#2C5F8A" font-weight="bold">校园待办中心</text>')

# 模块带
for cx, top, bottom, mid, mname in band_rects:
    x0 = cx - RX - 12
    w = (RX + 12) * 2
    parts.append(f'<rect x="{x0}" y="{top}" width="{w}" height="{bottom - top}" '
                 f'fill="none" stroke="#B7C9D8" stroke-width="0.9" rx="4" stroke-dasharray="3,3"/>')
    parts.append(f'<text x="{cx}" y="{top + 15}" text-anchor="middle" font-size="9.5" '
                 f'fill="#4C5F73" font-weight="bold">{escape(mid)}  {escape(mname)}</text>')

# 连线（先画线，后画椭圆，避免线压字）
for aid, uses in LINKS.items():
    if aid in ("STU", "SCHED", "PUB", "ADM"):
        ax = next(a[2] for a in MAIN_ACTORS if a[0] == aid)
        ay = next(a[3] for a in MAIN_ACTORS if a[0] == aid)
    else:
        ax = next(a[2] for a in EXT_ACTORS if a[0] == aid)
        ay = next(a[3] for a in EXT_ACTORS if a[0] == aid)
    for u in uses:
        if u not in pos:
            continue
        ux, uy = pos[u]
        # 连到椭圆边缘
        dx, dy = ux - ax, uy - ay
        dist = max((dx * dx + dy * dy) ** 0.5, 1)
        ex = ux - dx / dist * RX
        ey = uy - dy / dist * RY
        color = "#B98A2E" if u.startswith("NFR") else "#8A9AA8"
        parts.append(edge(ax, ay, ex, ey, color))

# 用例椭圆
for mid, mname, items in MODULES:
    for code, name in items:
        cx, cy = pos[code]
        parts.append(ellipse(cx, cy, code, name, code.startswith("NFR")))

# 参与者
for aid, label, x, y, side in MAIN_ACTORS:
    stereo = "系统角色" if aid == "SCHED" else None
    parts.append(actor(x, y, label, stereo))
for aid, label, x, y in EXT_ACTORS:
    parts.append(actor(x, y, label, "外部系统"))

# 图例
lx, ly = 28, BOTTOM + 22
parts.append(f'<rect x="{lx}" y="{ly}" width="250" height="72" fill="#FCFDFE" '
             f'stroke="#B7C9D8" stroke-width="0.9" rx="4"/>')
parts.append(f'<text x="{lx + 10}" y="{ly + 18}" font-size="9.5" fill="#4C5F73" font-weight="bold">图例</text>')
parts.append(f'<ellipse cx="{lx + 30}" cy="{ly + 34}" rx="16" ry="9" fill="#F2F8FD" stroke="#2C5F8A" stroke-width="1"/>')
parts.append(f'<text x="{lx + 52}" y="{ly + 38}" font-size="9" fill="#1B2A3A">功能用例</text>')
parts.append(f'<ellipse cx="{lx + 30}" cy="{ly + 56}" rx="16" ry="9" fill="#FFF6E9" stroke="#B98A2E" stroke-width="1"/>')
parts.append(f'<text x="{lx + 52}" y="{ly + 60}" font-size="9" fill="#1B2A3A">非功能用例</text>')

parts.append("</svg>")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(parts))
print("已生成:", OUT)
print("尺寸:", W, "x", H, "| 用例数:", len(pos))
