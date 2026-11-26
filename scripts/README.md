# 脚本

用于验证非功能需求与造数的辅助脚本，不属于业务代码。

| 脚本 | 用途 | 对应需求 | 状态 |
|---|---|---|---|
| `gen_usecase_overview_svg.py` | 生成用例总览图 SVG（40 个用例） | 需求建模 | ✅ 可用 |
| `seed_notices.py` | 生成 1000 条通知，用于首屏性能测试 | NFR-1 | 待补 |
| `feed_replay.py` | 重复投喂同一批响应，验证幂等去重 | NFR-2 | 待补 |
| `latency_check.py` | 计时统计 P95 | NFR-1 | 待补 |

## 用例总览图生成

```bash
python scripts/gen_usecase_overview_svg.py
# → models/usecase/usecase-overview.svg（1560×1678 矢量图）
```

为什么不用 PlantUML：实测 40 个用例在 PlantUML 下会排成 663×3759 的细长条，
自动布局无法控制。改为脚本精确计算坐标，输出可控的 SVG。详见
[docs/03-需求分析模型/用例图.md](../docs/03-需求分析模型/用例图.md) 第 5 节。

## 约定

- 脚本必须可重复执行，不污染真实数据
- 输出结论写进 `docs/05-测试/测试报告.md`
