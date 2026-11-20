<script setup lang="ts">
// 骨架占位页：v0.1 起替换为真实布局与路由视图。
const project = "校园信息聚合与待办提醒系统";
</script>

<template>
  <main class="placeholder">
    <h1>{{ project }}</h1>
    <p>骨架阶段：前端尚未开工，业务页面自 v0.1 起交付。</p>
    <p class="hint">接口文档见 <code>docs/04-设计/API契约.md</code></p>
  </main>
</template>

<style scoped>
.placeholder {
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  max-width: 720px;
  margin: 12vh auto;
  padding: 0 24px;
  line-height: 1.8;
  color: #242424;
}
h1 {
  font-size: 1.6rem;
}
.hint {
  color: #4c5f73;
  font-size: 0.9rem;
}
</style>
