<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { store } from '../store'
import { UserCheck } from 'lucide-vue-next'

const studentId = ref('')
const router = useRouter()

const handleLogin = () => {
  if (studentId.value.trim()) {
    store.login(studentId.value)
    router.push('/')
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-circle">
          <UserCheck class="logo-icon" />
        </div>
        <h2>泥邮工具人</h2>
        <p>校园二手交易 & 跑腿互助平台</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <input 
            id="sid" 
            v-model="studentId" 
            type="text" 
            required 
            placeholder="请输入学号或邮箱 (演示模式任意输入)"
            class="form-input"
          />
        </div>
        <button type="submit" class="submit-btn">
          登录 / 注册
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-color);
}

.login-card {
  width: 100%;
  max-width: 400px;
  background-color: var(--card-bg);
  padding: 2.5rem;
  border-radius: var(--radius);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-color);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-circle {
  width: 48px;
  height: 48px;
  background-color: #dbeafe; /* 浅蓝背景 */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
}

.logo-icon {
  color: var(--primary-color);
  width: 24px;
  height: 24px;
}

h2 {
  font-size: 1.8rem;
  font-weight: bold;
  color: var(--text-main);
  margin-bottom: 0.5rem;
}

p {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background-color: var(--input-bg);
  color: var(--text-main);
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.submit-btn {
  width: 100%;
  padding: 0.75rem;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-btn:hover {
  background-color: var(--primary-hover);
}
</style>