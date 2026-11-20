# 校园待办中心 · Tongji Campus Notice Hub

[![CI](https://github.com/phao90016-jpg/Tongji-campus-notice-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/phao90016-jpg/Tongji-campus-notice-hub/actions/workflows/ci.yml)
![stage](https://img.shields.io/badge/stage-proposal-blue)
![version](https://img.shields.io/badge/version-v0.0.0-lightgrey)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![vue](https://img.shields.io/badge/vue-3-42b883)

> 把学校教务系统里本来就有的课表、考试、毕设节点和通知，连同官网公告、GitHub 仓库和手动导入的内容，汇成一个入口，直接生成可核对的待办，并按你设定的提前量提醒。

软件工程课程设计（CST3619 / 420146）项目仓库。

---

## 这个项目解决什么

学生漏事，通常不是因为"没有聚合"，而是因为**关键时间点散在教务系统的不同页面里，且没有任何一处会主动找你**。

| 现象 | 现在怎么做 | 代价 |
|---|---|---|
| 考试时间地点只在排考页面 | 截图、记在备忘录 | 考场临时调整，按旧信息跑错楼 |
| 每学期课表要手工敲进日历 | 对着教务系统一条条录 | 8–12 门课，换教室后日历就废了 |
| 毕设选题/中期/预答辩三个节点 | 等群里通知、问同学 | 错过中期考核只能延毕设 |
| 一网通办申请卡在某个节点 | 反复登录看 | 不知道在等谁，也不知道还剩几天 |
| 班委发通知 | 群里刷屏 + 手动数谁没回 | 阅读率靠猜 |

**这个项目做的事**：把这些"已经在系统里、但没人提醒你"的时间点，变成手机上会响的待办。

### 三个设计判断

1. **主源是校内结构化接口，不是网页抓取。** 考试接口直接给 `examDate` + `examStartTime` + `roomName`，比从通知正文里猜时间可靠一个数量级。
2. **结构化数据不强迫用户确认。** 考试、课表、毕设节点生成的待办直接可用；只有从通知正文抽取的才走"草稿 → 用户确认"。
3. **提醒由服务端直接投递到微信，不依赖学校渠道，也不依赖客户端常驻。** 学生在页面上绑定一次微信服务号，之后到点由服务端发一条 HTTPS 请求，手机在微信「服务通知」里响；服务号失败自动降级到邮件。

---

## 功能

### 1. 校内数据接入

| 能力 | 用户看到什么 | 数据来源 |
|---|---|---|
| 学校统一身份认证登录 | 用学校账号登录，不用另设密码 | OAuth2 授权码 + `kc_idp_hint=tjiam` |
| 首次登录自动同步 | 登录后 10 秒内看到本周课表、考试、通知 | 课表 / 考试 / 教务通知 / 毕设节点 / 一网通办待办 |
| 课表同步 | "周三 3–4 节 数据结构 · 嘉定 A301" | `weekday`/`startUnit`/`endUnit`/`week`/`classroomName` |
| 考试同步 | "12-30 13:30 材料科学基础2 · 博楼 B110" | `examDate`/`examStartTime`/`roomName` |
| 毕设节点同步 | 选题、中期考核、预答辩各一条待办 | `topicTime`/`assessTime`/`defenseDate` |
| 一网通办待办导入 | 已有申请直接进待办列表 | `taskId`/`nodeName`/`formUrl` |

### 2. 补充源

| 能力 | 说明 |
|---|---|
| 官网栏目订阅 | HTML 适配器（**同济站点没有 RSS**），每源一份配置：列表页、条目选择器、正文选择器 |
| GitHub 仓库订阅 | 公开 REST API + ETag 条件请求，无更新时返回 304、不产生新通知 |
| 手动导入 | 粘贴文本 / 粘贴链接 / 上传截图，生成 `origin=manual` 的通知 |

### 3. 通知流与归类

- 四类来源合并为一条时间线，按来源、类型、课程、未读筛选，游标分页
- 按课程名 / 课程号 / 教师名把通知归到课程，匹配不中归"未分类"
- 同一业务主键的内容哈希变化 → 生成"原文已变更，请核对"，**不覆盖你改过的待办**

### 4. 待办

| 类型 | 生成方式 | 是否需要确认 |
|---|---|---|
| 考试、补缓考、上课、毕设、实习、一网通办、图书催还 | 结构化数据直接生成，`auto_confirmed=true` | 否 |
| 通知里提到的截止事项 | 规则 + 抽取生成草稿，保留原文高亮 | **是**，用户确认后才进列表 |
| 手动新建 | 用户自己写 | — |

状态机：`草稿 → 已确认 → 进行中 → 已完成`，可转`已过期`/`已取消`；每次迁移写状态日志，非法迁移返回 409。

### 5. 提醒

提醒由服务端投递：不依赖学校接口是否真的发消息，也不依赖网页开着。

| 环节 | 做法 |
|---|---|
| 绑定 | 学生扫码关注微信服务号（Server酱 / PushPlus），把 SendKey 粘进「我的 → 通知渠道」，系统立即发一条测试消息验证 |
| 投递 | 到点按「主通道 → 兜底」顺序发送：微信服务号 → 邮件 → 站内，任一成功即止 |
| 失败 | 凭据失效、网络错误、服务商业务错误分别归类；网络错误重试 2 次，仍失败 3s 内降级，投递记录标红 |
| 记录 | 每次尝试写一条（通道、耗时、结果码），后台可查每条待办实际走了哪条通道 |
| 日程 | 已确认待办可同步到校园号日程，方便在日历里看到（可选，不承诺提醒） |

准点率验收的是**服务端发出请求的时间**（计划时间 ±60s）；到达时间由服务商决定，不计入验收。

### 6. 资料与后台

- 收藏文本/链接/截图，加标签、关联课程，全文检索（SQLite FTS5 / PG `tsvector`）
- 班委发布班级通知 + 阅读率统计
- 管理员：源与同步任务健康度、手动触发、失败告警；用户与角色；审计日志

---

## 数据来源

功能点全部锚定在已存在的接口上。字段取自接口文档的返回参数表，不是推测。

| 数据 | 接口 | 授权 | 关键字段 |
|---|---|---|---|
| 课表 | `GET /v2/dc/teaching_info/student_timetable` | 客户端 / 授权码 | `weekday`、`startUnit`、`endUnit`、`week`、`classroomName`、`delInd` |
| 期末考试 | `GET /v1/rt/teaching_info/absent_examinfo` | 客户端 | `examDate`、`examStartTime`、`roomName`、`examStatus` |
| 补缓考 | `GET /v1/rt/teaching_info/deferred_examinfo` | 客户端 | 同上，`examType=2` |
| 教务通知 | `GET /v1/rt/onetongji/msg_list` · `msg_detail` | 客户端 | `title`、`content`、`publishTime`、`faceUserName` |
| 学年学期 | `GET /v1/rt/teaching_info/semester` | **匿名** | `beginDay`、`endDay`、`examWeekStart/End` |
| 毕设节点 | `thesis_topic` · `midterm_assessment` · `pre_defense` | 客户端 / 授权码 | `topicTime`、`assessTime`、`defenseDate` + 地点 |
| 一网通办待办 | `GET /v1/infra/task_center/task_list` | 客户端 / 授权码 | `taskId`、`nodeName`、`formUrl` |
| 提醒投递 | Server酱 / PushPlus HTTPS 接口 | 用户 SendKey / Token | `title`、`desp`、`token` |
| 个人日程（可选） | `POST /v1/infra/calendar/person/create` | 客户端 / 授权码 | `eventRepeatType`、`remindTimes`、`linkUrl` |
| GitHub | `GET /repos/{owner}/{repo}/commits` | 公开 REST | `sha`、`commit.message`、`commit.author.date` |
| 官网栏目 | 本科生院 `/30359/list.htm` 等 | 公开页面 | 列表条目、`div.wp_articlecontent` |

> 学校消息服务（邮件 / 企业微信 / 模板消息）与个人日程只作为可选增强：写进去的日程不一定会触发提醒，模板消息需要用户关注并授权，因此提醒主链路不依赖它们。通道设计见 [通知通道](docs/04-设计/通知通道.md)。

**三条硬事实**（详见 [可行性探测报告](docs/00-立项/可行性探测报告.md)）：

1. 教务通知接口**没有任何参数**（目录中 `parameters=null`），返回全校通知，需按 `faceUserName` 过滤；`startTime/endTime` 是展示有效期，不是办理截止时间。
2. 校历接口不可用（`A07500`），但学期接口匿名可用（66 个学期），周次换算没问题。
3. 考试与课表接口要求先取 `calendarId`（当前学期编号），"查考试"实际是两步。

---

## 角色与权限

| 角色 | 职责 | 数据边界 |
|---|---|---|
| 学生 `student` | 看通知与待办、管自己的提醒与收藏 | 仅本人 |
| 班委 `publisher` | 向所属班级发布通知、看阅读率 | 仅本班 / 本组织 |
| 管理员 `admin` | 维护源与同步任务、管理用户与角色 | 全局配置；审计只记元数据，不读待办正文 |
| 教师（可选，v0.3） | 发布课程通知、看课程待办完成率 | 仅本课程聚合，不读个人明细 |

**校内接口的调用约束**（重要）：

- 支持授权码模式的接口 → 一律用当前登录用户的 token，`userId` 从 token 取，不接受前端传入
- 仅客户端模式的接口（考试、教务通知）→ 后端以应用身份调用，但入参 `userId` 必须等于当前登录用户，代码层断言 + 审计
- 越权访问统一返回 `403`，且不泄露资源是否存在

---

## 架构

```mermaid
flowchart LR
    subgraph ext["外部来源"]
        A1["学校开放平台<br/>课表 · 考试 · 通知 · 毕设 · 待办"]
        A2["官网栏目<br/>HTML 适配器"]
        A3["GitHub 仓库<br/>ETag"]
        A4["手动导入<br/>文本 · 链接 · 截图"]
    end

    subgraph be["后端 FastAPI"]
        B0["auth<br/>学校 OAuth2 授权码"]
        B1["adapters<br/>源适配器（拉取 + 归一化）"]
        B2["services<br/>去重 · 归类 · 待办 · 编排"]
        B3[("PostgreSQL<br/>开发用 SQLite")]
        B4["scheduler<br/>同步 · 提醒兜底"]
    end

    subgraph out["提醒投递（服务端发起）"]
        D0["notify<br/>Notifier 适配器"]
        D1["微信服务号<br/>Server酱 / PushPlus"]
        D2["邮件 SMTP<br/>兜底"]
    end

    subgraph fe["前端 Vue 3"]
        C1[学生端]
        C2[管理后台]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    B0 --> B2
    B1 --> B2
    B2 --> B3
    B2 --> B4
    B4 --> D0
    D0 --> D1
    D0 --> D2
    C1 --> B2
    C2 --> B2
    B1 -. 连续失败 3 次 .-> A4
```

**关键约束**

- 适配器不直接写库（去重幂等可单测）；状态迁移只能经 `services` 层
- 幂等用**业务主键**（`UNIQUE(source, external_id)`），不用内容哈希；哈希只用于检测改期
- 不预拉全校数据：只对已授权用户按需同步 + 本地缓存，避免把他人明细落库

---

## 增量与里程碑

| 增量 | 目标 | 交付内容 | 演示重点 |
|---|---|---|---|
| **v0.1** | 校内数据 → 一条流 | 学校 OAuth 登录、课表/考试/通知/毕设同步、官网 1 个适配器、GitHub 订阅、手动导入、通知流与去重 | 新账号登录后 10 秒看到"本周课表 + 考试 + 通知" |
| **v0.2** | 结构化待办 → 提醒 | 七类结构化待办、文本草稿与确认、状态机、提醒规则、服务号绑定与投递、邮件兜底、投递记录、改期提示 | 确认一条待办，关掉网页，手机微信收到提醒；把 SendKey 改错再触发，自动降级到邮件 |
| **v0.3** | 资料复用 + 管理面 | 收藏/标签/搜索、班委发布与阅读统计、源与同步任务监控、RBAC、审计、越权 403 | 双账号越权演示 + 后台源健康度与降级 |

**并行任务**：第 1 周完成开放平台应用登记与 scope 申请、OAuth 回调地址备案。审批未到位时，v0.1 用"手动导入 + 官网 + GitHub"三条零依赖路径演示，校内接口以 mock 响应驱动开发。

---

## 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 前端 | Vue 3 + TypeScript + Vite | 学生端与管理后台同仓 |
| 后端 | FastAPI（Python 3.11+） | 分层：`api` / `services` / `adapters` / `notify` / `models` |
| 数据库 | 开发 SQLite / 部署 PostgreSQL | 全文检索分别用 FTS5 / `tsvector` |
| 调度 | 进程内调度 + 任务落库 | 同步任务与提醒投递，启动补扫 |
| 测试 | pytest + pytest-cov / Vitest | 适配器、通道与状态机必须有单测 |
| CI | GitHub Actions | ruff + pytest，红灯禁合并 |

---

## 快速开始

```bash
# 后端
cd src/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # 填写 client_id / secret；.env 不提交
                                   # 通知通道：SMTP 填在 .env；服务号凭据由用户在页面绑定，无需配置
pytest -q                          # 应全绿
uvicorn app.main:app --reload      # http://localhost:8000/health

# 前端
cd src/frontend
npm install
npm run dev
```

### 可行性探测（可复跑）

立项阶段对全部数据源做了实测，脚本与结果在 [`probe/`](probe/)：

```bash
cd probe
python3 probe_feasibility.py --json     # 9 项实测：token / 匿名接口 / scope / GitHub ETag / RSS / 官网解析
python3 scrape_inventory.py             # 抓取 235 个接口文档页，产出 api_inventory.csv
```

结论：235 个接口中 22 个匿名、80 个仅客户端、124 个支持授权码；官网无 RSS；校历接口故障；GitHub ETag 返回 304。详见 [可行性探测报告](docs/00-立项/可行性探测报告.md)。

---

## 仓库结构

```
campus-notice-hub/
├── .github/
│   ├── ISSUE_TEMPLATE/      # 用户故事 / 缺陷 / 任务
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/ci.yml     # ruff + pytest，红灯禁合并
├── docs/                    # 课程交付物（文档即代码）
│   ├── 00-立项/             # 选题文稿 v3（md + docx）、可行性探测报告、项目章程
│   ├── 01-需求调研/         # 调研计划、访谈纪要、竞品分析、调研报告
│   ├── 02-需求规约/         # SRS、用户故事清单、变更记录、追溯矩阵
│   ├── 03-需求分析模型/     # 用例图、类图与 CRC、状态图与顺序图
│   ├── 04-设计/             # 概要/详细设计、数据库、API 契约、ADR
│   ├── 05-测试/             # 测试计划、用例库、验收用例、测试报告
│   ├── 06-迭代/             # 迭代计划与回顾
│   ├── 07-部署/             # 部署说明、演示脚本
│   ├── 08-AI使用/           # AI 使用报告与台账
│   ├── 09-评审/             # 评审单模板
│   └── 10-课堂讲解/         # 课堂讲解排期与讲稿
├── models/                  # 图源文件（Mermaid/PlantUML），一图一 PR
├── probe/                   # 可行性探测：脚本 + 接口清单 + 结果
├── scripts/                 # 造数与压测；md2docx.py 由 Markdown 生成 docx
├── src/
│   ├── backend/             # FastAPI 后端（分层骨架）
│   └── frontend/            # Vue 3 前端（骨架）
└── README.md
```

---

## 文档导航

| 交付物 | 位置 | 检查点 |
|---|---|---|
| 选题文稿 v3 | [md](docs/00-立项/选题文稿.md) · [docx](docs/00-立项/选题文稿-v3.docx) | 第 1 次课 |
| 可行性探测报告 | [可行性探测报告](docs/00-立项/可行性探测报告.md) | 第 1 次课 |
| 选题变更说明 | [变更说明-选题v3](docs/00-立项/变更说明-选题v3.md) | 第 1 次课 |
| 项目章程 | [项目章程](docs/00-立项/项目章程.md) | 第 1 次课 |
| 调研计划表 | [调研计划表](docs/01-需求调研/调研计划表.md) | 第 1 次课 |
| 调研报告 | [调研报告](docs/01-需求调研/调研报告.md) | 第 2 次课 |
| 用户故事清单 | [用户故事清单](docs/02-需求规约/用户故事清单.md) | 第 2 次课 |
| 需求规约 SRS | [SRS-v1.0](docs/02-需求规约/SRS-v1.0.md) | 第 3 次课 |
| 需求追溯矩阵 | [需求追溯矩阵](docs/02-需求规约/需求追溯矩阵.md) | 第 3 / 5 次课 |
| 分析模型 | [用例图](docs/03-需求分析模型/用例图.md) · [类图](docs/03-需求分析模型/类图与CRC.md) · [状态图](docs/03-需求分析模型/状态图与顺序图.md) | 第 4 / 5 次课 |
| 概要 / 详细设计 | [概要设计](docs/04-设计/概要设计.md) · [详细设计](docs/04-设计/详细设计.md) | 第 6 / 7 次课 |
| 通知通道设计 | [通知通道](docs/04-设计/通知通道.md) | 第 6 次课 |
| 测试计划与报告 | [05-测试/](docs/05-测试/) | 第 7 次课起 |
| 演示脚本 | [演示脚本](docs/07-部署/演示脚本.md) | 期末 |
| AI 使用报告 | [AI使用报告](docs/08-AI使用/AI使用报告.md) | 期末 |

完整索引与"十项交付物"对照见 **[docs/README.md](docs/README.md)**。

---

## 工程约定

完整工作流见 **[CONTRIBUTING.md](CONTRIBUTING.md)**，要点：

- `main` 受保护，**禁止直推**，一律走 Pull Request
- 每个 PR 至少 1 人 Review + CI 绿灯方可合并
- 需求、缺陷、任务一律先建 Issue；变更走"申请 → 评审 → 批准 → 关闭"
- AI 产出必须登记到 [AI 使用台账](docs/08-AI使用/AI使用台账.md)；密钥、token、学工号严禁进入代码仓库与提示词
- 文档改动同时更新 Markdown 与 docx（`python3 scripts/md2docx.py docs/00-立项/选题文稿.md docs/00-立项/选题文稿-v3.docx --template docs/00-立项/选题文稿-v2.docx`）
- 禁止"最后一晚打包上传"式提交，提交分布计入过程成绩

---

## 团队

| 成员 | 课程角色 | 兼任 |
|---|---|---|
| 待填 | 项目经理 | |
| 待填 | 需求分析师 | |
| 待填 | 架构 / 设计工程师 | |
| 待填 | 开发工程师 | |
| 待填 | 测试 / 质量工程师 | |
| 待填 | — | AI 使用负责人 |
| 待填 | — | DevOps 负责人 |

> 每人至少主讲 1 次课堂讲解、至少 10 个被合并的 PR。排期见
> [课堂讲解排期](docs/10-课堂讲解/讲解排期.md)。
