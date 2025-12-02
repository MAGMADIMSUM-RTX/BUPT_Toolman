import { createRouter, createWebHistory } from 'vue-router'

const Home = () => import('../pages/Home.vue')
const About = () => import('../pages/About.vue')
const Contact = () => import('../pages/Contact.vue')
const Register = () => import('../pages/Register.vue')
const Confirm = () => import('../pages/Confirm.vue')
const Preferences = () => import('../pages/Preferences.vue')

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/about', name: 'About', component: About },
  { path: '/contact', name: 'Contact', component: Contact },
  { path: '/register', name: 'Register', component: Register },
  { path: '/confirm', name: 'Confirm', component: Confirm },
  { path: '/preferences', name: 'Preferences', component: Preferences },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
