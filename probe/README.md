# 可行性探测（probe）

立项阶段对"选题里每个功能点到底有没有数据支撑"做的实测，不是读文档后的推测。

## 为什么在这里

选题文稿 v2 假设"官网有 RSS""作业平台能抓"，实测发现两个都不成立。与其在需求阶段返工，不如把探测脚本和结果一起入库：结论可复跑、可复核，评审时能当场跑一遍。

## 文件

| 文件 | 内容 |
|---|---|
| `probe_feasibility.py` | 9 项实测：取 token、匿名学期接口、校历接口、scope 鉴权（401/403）、GitHub ETag、RSS 探测、本科生院 HTML 解析、学院站解析、内容指纹去重 |
| `scrape_inventory.py` | 抓取开放平台 235 个接口文档页，产出接口清单 |
| `api_inventory.csv` | 接口清单：方法、地址、授权模式、参数、是否匿名 |
| `api_catalog.json` | 官方目录接口（237 条），含 scope 与参数结构 |
| `key_endpoints.csv` | 与本项目相关的 18 个接口及需申请的 scope |
| `probe_result.json` | 最近一次实测结果（时间戳 + 逐项判定） |

## 怎么跑

```bash
cd probe
python3 probe_feasibility.py --json     # 只依赖标准库
python3 scrape_inventory.py             # 约 20s，产出 api_inventory.csv
```

## 最近一次结论（2026-11-20）

| 项 | 结果 |
|---|---|
| OAuth client_credentials 取 token | ✅ 200 / 53ms / scope 仅 `fake_api` |
| 课表接口鉴权 | ✅ 无 token → 401，错误 scope → 403（逐接口授权） |
| 学年学期（匿名） | ✅ 200 / 66 个学期 / 含考试周起止 |
| 校历（匿名） | ❌ HTTP 200 但业务码 `A07500`，取不到数据 |
| GitHub 公开 API + ETag | ✅ 200 / 304 / 未授权配额 60 次/小时/IP |
| 同济站点 RSS | ❌ 4 站点 × 4 路径全部未命中 |
| 本科生院通知列表 | ✅ 9 条 / 正文 412 字 / 两次抓取指纹一致 |
| 计算机学院通知 | ⚠️ 可解析（另一套 CMS），正文是 PDF 转图片，需 OCR |

完整分析见 [可行性探测报告](../docs/00-立项/可行性探测报告.md)。

## 注意

- 脚本里用的是文档公开的**演示用客户端**（仅 `fake_api` scope），不是项目凭证
- 探测会真实请求学校接口，请勿高频重跑；`scrape_inventory.py` 默认 8 并发，已足够温和
- 校内网络与公网出口的延迟不同，报告中标注了探测环境
