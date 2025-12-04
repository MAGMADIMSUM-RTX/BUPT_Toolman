import { createRouter, createWebHistory } from 'vue-router'
import { store } from '../store'
import MarketView from '../views/MarketView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'market', component: MarketView },
    { path: '/tasks', name: 'tasks', component: () => import('../views/TaskView.vue') },
    { path: '/chat', name: 'chat', component: () => import('../views/ChatView.vue') },
    { path: '/profile', name: 'profile', component: () => import('../views/ProfileView.vue') },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') }
  ]
})

// 路由守卫：检查是否登录
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!store.state.currentUser
  if (to.name !== 'login' && !isAuthenticated) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router