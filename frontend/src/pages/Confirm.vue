<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { API_BASE_URL } from '../config.js'
import { CheckCircle, XCircle, Loader } from 'lucide-vue-next'

const route = useRoute()
const status = ref('loading') // loading, success, error
const message = ref('正在验证您的邮箱...')

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    status.value = 'error'
    message.value = '无效的验证链接'
    return
  }

  try {
    const res = await fetch(`${API_BASE_URL}/user/confirm?token=${token}`)
    const data = await res.json()
    if (res.ok) {
      status.value = 'success'
      message.value = '邮箱验证成功！'
    } else {
      status.value = 'error'
      message.value = data.error || '验证失败，链接可能已过期'
    }
  } catch (e) {
    status.value = 'error'
    message.value = '无法连接到服务器'
  }
})
</script>

<template>
  <div class="login-container">
    <div class="login-card center-content">
      <div v-if="status === 'loading'">
        <Loader class="icon spin" />
        <p>{{ message }}</p>
      </div>

      <div v-else-if="status === 'success'">
        <CheckCircle class="icon success" size="48" />
        <h2>验证成功</h2>
        <p class="desc">{{ message }}</p>
        <router-link to="/login" class="submit-btn">立即登录</router-link>
      </div>

      <div v-else>
        <XCircle class="icon error" size="48" />
        <h2>验证失败</h2>
        <p class="desc">{{ message }}</p>
        <router-link to="/register" class="link">重新注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 继承 Login 的基础布局 */
.login-container { min-height: 100vh; display: flex; align-items: center; justify-content: center; background-color: var(--bg-body); }
.login-card { width: 100%; max-width: 400px; background-color: var(--bg-card); padding: 3rem 2rem; border-radius: var(--radius); box-shadow: var(--shadow-sm); border: 1px solid var(--border); }
.center-content { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 15px; }

.icon { margin-bottom: 10px; }
.icon.spin { animation: spin 1s linear infinite; color: var(--primary); }
.icon.success { color: #10b981; }
.icon.error { color: #ef4444; }

h2 { font-weight: bold; color: var(--text-main); }
.desc { color: var(--text-secondary); margin-bottom: 10px; }

.submit-btn { display: inline-block; width: 100%; padding: 0.75rem; background-color: var(--primary); color: white; border-radius: var(--radius); font-weight: bold; text-decoration: none; margin-top: 10px; }
.link { color: var(--primary); text-decoration: none; }

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>