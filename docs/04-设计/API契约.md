# API 契约

> 对应单元：4 设计建模｜检查点：第 6 次课（第 14 周）
> 负责人：架构 / 设计工程师｜状态：草稿，接口签字后方可编码

> 契约一旦签字定稿，变更须走变更流程。建议用 OpenAPI 文件维护（`openapi.yaml`），
> 本文件为摘要与决策说明。

## 1. 通用约定

| 项 | 约定 |
|---|---|
| 基础路径 | `/api/v1` |
| 认证 | Session Cookie（登录后签发），后台接口独立前缀 `/api/v1/admin` |
| 错误格式 | `{"code": "TODO", "message": "...", "detail": {}}` |
| 越权 | 统一 403，响应不体现资源是否存在 |
| 分页 | `?page=1&size=20`，响应含 `total` |

## 2. 接口清单

### 认证 auth

| 方法 | 路径 | 说明 | 角色 | 需求 |
|---|---|---|---|---|
| GET | `/auth/github/login` | 跳转 GitHub 授权 | 匿名 | REQ-F-001 |
| GET | `/auth/github/callback` | 授权回调，建立会话 | 匿名 | REQ-F-001 |
| POST | `/auth/logout` | 退出登录 | 已登录 | REQ-F-001 |
| DELETE | `/auth/github/binding` | 解绑 GitHub | 学生 | REQ-F-002 |

### 订阅源 sources

| 方法 | 路径 | 说明 | 角色 | 需求 |
|---|---|---|---|---|
| GET | `/sources` | 我的订阅源列表 | 学生 | REQ-F-003 |
| POST | `/sources` | 添加订阅源 | 学生 | REQ-F-003 |
| PATCH | `/sources/{id}` | 暂停 / 恢复 | 学生 | REQ-F-004 |
| DELETE | `/sources/{id}` | 删除订阅源 | 学生 | REQ-F-004 |

### 通知 notices

| 方法 | 路径 | 说明 | 角色 | 需求 |
|---|---|---|---|---|
| GET | `/notices` | 通知流（筛选、分页） | 学生 | REQ-F-006 |
| GET | `/notices/{id}` | 通知详情 | 学生 | REQ-F-007 |
| POST | `/notices/import` | 手动导入 | 学生 | REQ-F-005 |
| PATCH | `/notices/{id}` | 标记已读 / 归档 | 学生 | REQ-F-008 |

### 待办 todos

| 方法 | 路径 | 说明 | 角色 | 需求 |
|---|---|---|---|---|
| GET | `/todos` | 我的待办列表 | 学生 | REQ-F-012 |
| POST | `/todos/{id}/confirm` | 确认待办草稿 | 学生 | REQ-F-012 |
| PATCH | `/todos/{id}` | 编辑待办 | 学生 | REQ-F-012 |
| PATCH | `/todos/{id}/status` | 更新状态 | 学生 | REQ-F-014 |
| DELETE | `/todos/{id}` | 删除待办 | 学生 | REQ-F-013 |

### 提醒 reminders

| 方法 | 路径 | 说明 | 角色 | 需求 |
|---|---|---|---|---|
| GET | `/reminders/rules` | 我的提醒规则 | 学生 | REQ-F-015 |
| PUT | `/reminders/rules/{todo_id}` | 设置提醒规则 | 学生 | REQ-F-015 |

### 管理后台 admin

| 方法 | 路径 | 说明 | 角色 | 需求 |
|---|---|---|---|---|
| GET | `/admin/sources` | 信息源清单 | 管理员 | REQ-F-024 |
| GET | `/admin/fetch-tasks` | 抓取任务与失败告警 | 管理员 | REQ-F-025 |
| GET | `/admin/users` | 用户与角色管理 | 管理员 | REQ-F-026 |
| POST | `/admin/notices` | 发布班级通知 | 班委 | REQ-F-022 |

## 3. 契约签字

| 项 | 内容 |
|---|---|
| 定稿版本 | v1.0 |
| 签字人 | 待填 |
| 日期 | 待填 |
| 变更记录 | 见 [../02-需求规约/变更记录.md](../02-需求规约/变更记录.md) |
