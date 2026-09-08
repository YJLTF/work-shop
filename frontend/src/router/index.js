import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/tool/:id',
    name: 'tool',
    component: () => import('../views/ToolView.vue'),
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

/** hash 路由：打包成单文件 exe 后由 file 服务托管，无 history 回退负担 */
export const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})
