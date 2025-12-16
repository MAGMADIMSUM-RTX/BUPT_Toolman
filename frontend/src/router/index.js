import { createRouter, createWebHashHistory } from 'vue-router'
import { store } from '../store'

// 引入 Pages
const Home = () => import('../pages/Home.vue')
const Tasks = () => import('../pages/Tasks.vue')
const Chat = () => import('../pages/Chat.vue')
const Profile = () => import('../pages/Profile.vue')
const Login = () => import('../pages/Login.vue')
const Register = () => import('../pages/Register.vue')
const Confirm = () => import('../pages/Confirm.vue')
const Preferences = () => import('../pages/Preferences.vue')
const Test = () => import('../pages/Test.vue')

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/goods/:id', name: 'GoodDetail', component: Home },
  { path: '/tasks', name: 'Tasks', component: Tasks },
  { path: '/chat', name: 'Chat', component: Chat },
  { path: '/profile', name: 'Profile', component: Profile },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { path: '/confirm', name: 'Confirm', component: Confirm },
  { path: '/preferences', name: 'Preferences', component: Preferences },
  { path: '/test', name: 'Test', component: Test },
]

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由守卫：未登录跳转到 Login
router.beforeEach((to, from, next) => {
  const publicPages = ['Login', 'Register', 'Confirm'];
  const authRequired = !publicPages.includes(to.name);
  // 从 store 中检查，或者重新从 localStorage 读取以防 store 丢失
  const loggedIn = store.state.currentUser || localStorage.getItem('user');

  if (authRequired && !loggedIn) {
    next({ name: 'Login' });
  } else {
    next();
  }
});

export default router