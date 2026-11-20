# 前端（Vue 3 + TypeScript + Vite）

## 目录

```
src/
├── main.ts        # 入口
├── App.vue        # 根组件（骨架期仅占位）
├── router/        # 路由
├── api/           # 接口封装
├── stores/        # Pinia 状态
├── components/    # 可复用组件
└── views/         # 页面
```

## 本地开发

```bash
npm install
npm run dev
```

## 约定

- 接口统一走 `src/api/`，组件不直接发请求
- 页面按角色分区：学生端 `/`、管理后台 `/admin`
- 越权提示统一处理 403，不区分"不存在"与"无权限"

> 骨架期仅含占位页面，业务页面自 v0.1 起按 Issue 交付。
