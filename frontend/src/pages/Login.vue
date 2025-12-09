<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { store } from '../store'
import { UserCheck } from 'lucide-vue-next'

const form = ref({ username: '', password: '' })
const errorMsg = ref('')
const loading = ref(false)
const router = useRouter()

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) return
  
  loading.value = true
  errorMsg.value = ''
  
  const result = await store.login(form.value.username, form.value.password)
  
  if (result.success) {
    router.push('/')
  } else {
    errorMsg.value = result.message
  }
  loading.value = false
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-circle"><UserCheck class="logo-icon" /></div>
        <h2>泥邮工具人</h2>
        <p>欢迎回来，请登录</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <input v-model="form.username" type="text" required placeholder="用户名 / 邮箱" class="form-input"/>
        </div>
        <div class="form-group">
          <input v-model="form.password" type="password" required placeholder="密码" class="form-input"/>
        </div>
        
        <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>

        <button type="submit" :disabled="loading" class="submit-btn">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        
        <div class="footer-link">
            <router-link to="/register">还没有账号？去注册</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-container { min-height: 100vh; display: flex; align-items: center; justify-content: center; background-color: var(--bg-body); }
.login-card { width: 100%; max-width: 400px; background-color: var(--bg-card); padding: 2.5rem; border-radius: var(--radius); box-shadow: var(--shadow-sm); border: 1px solid var(--border); }
.login-header { text-align: center; margin-bottom: 2rem; }
.logo-circle { width: 48px; height: 48px; background-color: #dbeafe; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem; }
.logo-icon { color: var(--primary); width: 24px; height: 24px; }
h2 { font-size: 1.8rem; font-weight: bold; color: var(--text-main); margin-bottom: 0.5rem; }
p { color: var(--text-secondary); font-size: 0.9rem; }
.form-group { margin-bottom: 1.2rem; }
.form-input { width: 100%; padding: 0.75rem 1rem; border: 1px solid var(--border); border-radius: var(--radius); background-color: var(--bg-input); color: var(--text-main); outline: none; transition: border-color 0.2s; }
.form-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); }
.submit-btn { width: 100%; padding: 0.75rem; background-color: var(--primary); color: white; border: none; border-radius: var(--radius); font-weight: bold; cursor: pointer; transition: 0.2s; }
.submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }
.submit-btn:hover:not(:disabled) { filter: brightness(1.1); }
.error-text { color: #ef4444; font-size: 0.9rem; text-align: center; margin-bottom: 1rem; }
.footer-link { margin-top: 15px; text-align: center; font-size: 0.9rem; }
.footer-link a { color: var(--primary); text-decoration: none; }
</style>