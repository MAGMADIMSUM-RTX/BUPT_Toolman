import './assets/main.css' 
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

const app = createApp(App)

// 配置axios，使得跨域请求能自动带上cookie
axios.defaults.withCredentials = true

app.use(router)

app.mount('#app')