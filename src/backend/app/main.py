"""应用入口（骨架）。

当前仅提供健康检查，用于验证 CI 与部署链路；
业务接口自 v0.1 起按 Issue 逐个增量加入。
"""

from fastapi import FastAPI

app = FastAPI(
    title="校园信息聚合与待办提醒系统 API",
    version="0.0.0",
    description="骨架阶段：仅健康检查。业务接口自 v0.1 起增量交付。",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """存活探针，供 CI 冒烟与部署健康检查使用。"""
    return {"status": "ok"}
