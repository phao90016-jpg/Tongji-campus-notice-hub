import { createRouter, createWebHistory } from "vue-router";

// 骨架期只挂根路由；v0.1 起按角色拆分学生端与 /admin 后台路由。
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("../App.vue"),
    },
  ],
});

export default router;
