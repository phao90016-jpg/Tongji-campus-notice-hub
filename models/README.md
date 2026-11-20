# 模型源文件

所有图的源文件放这里，**一图一 PR**。文档中引用图，不贴截图。

## 目录

| 目录 | 内容 | 格式 |
|---|---|---|
| `usecase/` | 用例图 | Mermaid / PlantUML |
| `class/` | 类图、ER 图 | Mermaid / PlantUML |
| `state/` | 状态图 | Mermaid `stateDiagram-v2` |
| `sequence/` | 顺序图、活动图 | Mermaid / PlantUML |

## 命名约定

```
<类型>-<编号>-<简述>.<扩展名>
例：uc-usecase-overview.mmd
    sd01-fetch.puml
```

## 为什么用源文件

- 可版本化、可 diff、可评审
- 改一个状态不用重画整张图
- 与"文档即代码"一致：图也是代码

## 自查

- [ ] 语法能渲染
- [ ] 与 SRS 编号一致（UC-、AC-、REQ-）
- [ ] 与追溯矩阵对应
