<template>
  <div>
    <h1>注册</h1>
    <form @submit.prevent="register">
      <div>
        <label for="name">姓名:</label>
        <input id="name" v-model="form.name" required />
      </div>
      <div>
        <label for="email">邮箱:</label>
        <input id="email" type="email" v-model="form.email" required />
      </div>
      <div>
        <label for="pswd">密码:</label>
        <input id="pswd" type="password" v-model="form.pswd" required />
      </div>
      <button type="submit" :disabled="loading">注册</button>
    </form>
    <p v-if="message">{{ message }}</p>
    <p v-if="error">{{ error }}</p>
  </div>
</template>

<script>
import { API_BASE_URL } from '../config.js'

export default {
  name: 'Register',
  data() {
    return {
      form: {
        name: '',
        email: '',
        pswd: ''
      },
      loading: false,
      message: '',
      error: ''
    }
  },
  methods: {
    async register() {
      this.loading = true
      this.message = ''
      this.error = ''
      try {
        const response = await fetch(`${API_BASE_URL}/user/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.form)
        })
        const data = await response.json()
        if (response.ok) {
          this.message = '注册成功！请检查邮箱完成验证。'
        } else {
          this.error = data.error || '注册失败'
        }
      } catch (err) {
        this.error = '网络错误'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>