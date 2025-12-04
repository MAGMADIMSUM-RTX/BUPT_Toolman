import './assets/main.css' // <--- 关键！加上这一行，所有样式才会生效！

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)

app.mount('#app')