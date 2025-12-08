<script setup>
import { ref } from 'vue'
import { API_BASE_URL } from '../config.js'

const form = ref({ name: '', email: '', pswd: '' })
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const handleRegister = async () => {
  loading.value = true
  errorMsg.value = ''
  successMsg.value = ''

  try {
    const res = await fetch(`${API_BASE_URL}/user/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    const data = await res.json()

    if (res.ok) {
      successMsg.value = `注册成功！验证邮件已发送至 ${form.value.email}，请点击邮件中的链接激活账号。`
      form.value = { name: '', email: '', pswd: '' } // 清空表单
    } else {
      errorMsg.value = data.error || '注册失败'
    }
  } catch (e) {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
         <h2>注册账号</h2>
         <p>加入校园互助社区</p>
      </div>

      <form v-if="!successMsg" @submit.prevent="handleRegister">
        <div class="form-group">
          <input v-model="form.name" required placeholder="昵称 / 用户名" class="form-input" />
        </div>
        <div class="form-group">
          <input type="email" v-model="form.email" required placeholder="电子邮箱 (用于接收验证码)" class="form-input" />
        </div>
        <div class="form-group">
          <input type="password" v-model="form.pswd" required placeholder="设置密码" class="form-input" />
        </div>
        
        <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>

        <button type="submit" :disabled="loading" class="submit-btn">
          {{ loading ? '注册中...' : '立即注册' }}
        </button>
      </form>

      <div v-else class="success-box">
        <div class="success-icon">📧</div>
        <h3>请验证您的邮箱</h3>
        <p class="success-msg">{{ successMsg }}</p>
        <p class="sub-tip">验证完成后，请点击下方按钮登录。</p>
        <router-link to="/login" class="submit-btn">去登录</router-link>
      </div>

      <div v-if="!successMsg" class="footer-link">
         <router-link to="/login">已有账号？去登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 复用 Login 的样式，保持一致性 */
.login-container { min-height: 100vh; display: flex; align-items: center; justify-content: center; background-color: var(--bg-body); }
.login-card { width: 100%; max-width: 400px; background-color: var(--bg-card); padding: 2.5rem; border-radius: var(--radius); box-shadow: var(--shadow-sm); border: 1px solid var(--border); }
.login-header { text-align: center; margin-bottom: 2rem; }
.login-header h2 { font-size: 1.8rem; font-weight: bold; color: var(--text-main); margin-bottom: 0.5rem; }
.login-header p { color: var(--text-secondary); font-size: 0.9rem; }
.form-group { margin-bottom: 1.2rem; }
.form-input { width: 100%; padding: 0.75rem 1rem; border: 1px solid var(--border); border-radius: var(--radius); background-color: var(--bg-input); color: var(--text-main); outline: none; transition: border-color 0.2s; }
.form-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); }
.submit-btn { display:block; width: 100%; padding: 0.75rem; background-color: var(--primary); color: white; border: none; border-radius: var(--radius); font-weight: bold; cursor: pointer; text-align: center; text-decoration: none; transition: 0.2s; }
.submit-btn:hover { filter: brightness(1.1); }
.submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }
.error-text { color: #ef4444; font-size: 0.9rem; text-align: center; margin-bottom: 1rem; }
.footer-link { margin-top: 15px; text-align: center; font-size: 0.9rem; }
.footer-link a { color: var(--primary); text-decoration: none; }

/* 成功状态样式 */
.success-box { text-align: center; padding: 10px 0; }
.success-icon { font-size: 3rem; margin-bottom: 10px; }
.success-box h3 { color: var(--text-main); font-weight: bold; margin-bottom: 10px; }
.success-msg { color: #10b981; margin-bottom: 10px; line-height: 1.5; }
.sub-tip { color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 20px; }
</style>