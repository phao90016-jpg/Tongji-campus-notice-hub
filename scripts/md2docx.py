#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown → docx（课程交付物排版）

用途：把 docs/ 下的 Markdown 源文件生成同款 .docx，避免"两份内容各改各的"。
模板：传入一份已有 docx 作为样式模板（保留 Title / Heading 1 / Normal / Table Grid 等样式）。

支持子集：# ## ### 标题、段落、**加粗**、`代码`、- 无序列表、1. 有序列表、
| 管道表格 |、> 引用（映射为 Source Note 样式）、--- 分隔线（忽略）。

用法：
    python3 scripts/md2docx.py 选题文稿-v3.md 选题文稿-v3.docx --template 选题文稿-v2.docx
"""
import argparse
import re

import docx
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

EA_FONT = "宋体"          # 与既有交付物一致
INK = RGBColor(0x17, 0x2C, 0x44)


def set_ea(run):
    """统一东亚字体，避免主题字体在无 Noto 的机器上回退成别的字形。"""
    run.font.name = EA_FONT
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), EA_FONT)
    rfonts.set(qn("w:hint"), "eastAsia")


def clear_body(doc):
    body = doc.element.body
    for child in list(body):
        if child.tag.endswith("}sectPr"):
            continue
        body.remove(child)


TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")


def add_runs(paragraph, text):
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.font.size = Pt(9.5)
        else:
            run = paragraph.add_run(part)
        set_ea(run)


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # 支持 \| 转义
    cells, buf, i = [], "", 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            buf += "|"
            i += 2
            continue
        if line[i] == "|":
            cells.append(buf.strip())
            buf = ""
        else:
            buf += line[i]
        i += 1
    cells.append(buf.strip())
    return cells


def is_sep(line):
    s = line.strip()
    if not s.startswith("|"):
        return False
    return bool(re.fullmatch(r"\|?[\s:|-]+\|?", s)) and "-" in s


def visual_len(text):
    """中文按 2 个宽度计，用于估算列宽。"""
    n = 0
    for ch in text:
        n += 2 if ord(ch) > 0x2E7F else 1
    return n


def add_table(doc, rows):
    header, body = rows[0], rows[1:]
    ncol = len(header)
    table = doc.add_table(rows=1 + len(body), cols=ncol)
    table.style = "Table Grid"
    table.autofit = False

    # 表头重复（跨页时可读）
    trpr = table.rows[0]._tr.get_or_add_trPr()
    trpr.append(trpr.makeelement(qn("w:tblHeader"), {qn("w:val"): "true"}))

    for j, cell_text in enumerate(header):
        cell = table.rows[0].cells[j]
        p = cell.paragraphs[0]
        p.text = ""
        run = p.add_run(cell_text)
        run.bold = True
        set_ea(run)
    for i, row in enumerate(body, start=1):
        tr = table.rows[i]._tr
        tr.get_or_add_trPr().append(tr.get_or_add_trPr().makeelement(qn("w:cantSplit"), {}))
        for j in range(ncol):
            cell = table.rows[i].cells[j]
            p = cell.paragraphs[0]
            p.text = ""
            add_runs(p, row[j] if j < len(row) else "")

    # 按内容长度分配列宽（限制单列占比，避免一格吃掉半页）
    weights = []
    for j in range(ncol):
        lens = [visual_len(header[j])] + [visual_len(r[j]) if j < len(r) else 0 for r in body]
        w = max(10, min(sorted(lens)[int(len(lens) * 0.9)] if lens else 10, 46))
        if "接口" in header[j] or "页面" in header[j]:
            w = int(w * 1.25)
        if j == 0:
            w = max(w, 15)
        weights.append(w)
    total = sum(weights)
    sec = doc.sections[0]
    usable = sec.page_width - sec.left_margin - sec.right_margin
    widths = [int(usable * w / total) for w in weights]
    for j, w in enumerate(widths):
        table.columns[j].width = w
        for cell in table.columns[j].cells:
            cell.width = w
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                for r in p.runs:
                    if ncol >= 3:
                        r.font.size = Pt(9.5)


def convert(md_path, out_path, template=None):
    lines = open(md_path, encoding="utf-8").read().splitlines()
    doc = docx.Document(template) if template else docx.Document()
    clear_body(doc)

    i, n = 0, len(lines)
    first_h1 = True
    while i < n:
        line = lines[i]
        s = line.strip()

        if not s or s == "---":
            i += 1
            continue

        # 表格
        if s.startswith("|") and i + 1 < n and is_sep(lines[i + 1]):
            rows = [split_row(s)]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            add_table(doc, rows)
            continue

        # 标题
        if s.startswith("# "):
            text = s[2:].strip()
            if first_h1:
                p = doc.add_paragraph(text, style="Title")
                p.alignment = 1  # 居中，与 v2 一致
                for r in p.runs:
                    set_ea(r)
                first_h1 = False
            else:
                doc.add_paragraph(text, style="Heading 1")
            i += 1
            continue
        if s.startswith("## "):
            p = doc.add_paragraph(s[3:].strip(), style="Heading 1")
            for r in p.runs:
                set_ea(r)
            i += 1
            continue
        if s.startswith("### "):
            p = doc.add_paragraph(s[4:].strip(), style="Heading 2")
            for r in p.runs:
                set_ea(r)
                r.font.color.rgb = INK
                r.font.size = Pt(12)
            i += 1
            continue

        # 引用
        if s.startswith(">"):
            text = s.lstrip(">").strip()
            p = doc.add_paragraph(style="Source Note" if "数据来源" in text or "接入参考" in text else None)
            add_runs(p, text)
            i += 1
            continue

        # 列表
        if re.match(r"^[-*] ", s):
            p = doc.add_paragraph(style="List Bullet")
            add_runs(p, s[2:].strip())
            i += 1
            continue
        if re.match(r"^\d+\. ", s):
            num = re.match(r"^(\d+)\.", s).group(1)
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent = Pt(21)
            pf.first_line_indent = Pt(-21)
            pf.space_after = Pt(0)
            p.add_run(f"{num}. ")
            add_runs(p, re.sub(r"^\d+\.\s*", "", s))
            i += 1
            continue

        # 普通段落（合并紧随的非空、非特殊行）
        buf = [s]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith(("#", "|", ">", "- ", "* ")) or re.match(r"^\d+\. ", nxt)
                    or nxt == "---"):
                break
            buf.append(nxt)
            i += 1
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Pt(21)   # 首行缩进 2 字符
        add_runs(p, " ".join(buf))

    doc.save(out_path)
    print(f"已生成 {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--template", default=None)
    a = ap.parse_args()
    convert(a.src, a.out, a.template)
