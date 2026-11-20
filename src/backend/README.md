# 后端（FastAPI）

## 目录

```
app/
├── main.py        # 应用入口（骨架期仅健康检查）
├── core/          # 配置、数据库、调度等基础设施
├── api/           # 路由层：参数校验、鉴权、响应
├── schemas/       # Pydantic 出入参模型
├── models/        # ORM 实体
├── services/      # 应用层：用例编排
└── adapters/      # 信息源适配器（R1 应对，见其 README）
tests/             # pytest 单元与集成测试
```

## 分层约定

- `api` 只做参数校验与鉴权，不写业务逻辑
- `services` 编排用例，事务边界在此
- `adapters` 只负责"拉取 + 归一化"，不写库（保证 NFR-2 幂等可测）
- `models` 只放 ORM 实体，状态迁移必须经 `services`

## 本地开发

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
pytest -q
uvicorn app.main:app --reload
```

## 质量门禁

- `ruff check .` 无告警
- `pytest -q` 全绿
- 核心模块覆盖率 ≥ 80%（ingest、reminders）
