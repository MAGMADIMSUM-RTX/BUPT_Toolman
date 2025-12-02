<template>
  <div>
    <h1>验证邮箱</h1>
    <p v-if="loading">正在验证...</p>
    <p v-if="message">{{ message }}</p>
    <p v-if="error">{{ error }}</p>
  </div>
</template>

<script>
import { API_BASE_URL } from '../config.js'

export default {
  name: 'Confirm',
  data() {
    return {
      loading: true,
      message: '',
      error: ''
    }
  },
  async mounted() {
    const token = this.$route.query.token
    if (!token) {
      this.error = '缺少验证令牌'
      this.loading = false
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/user/confirm?token=${token}`)
      const data = await response.json()
      if (response.ok) {
        this.message = data.message || '验证成功！'
      } else {
        this.error = data.error || '验证失败'
      }
    } catch (err) {
      this.error = '网络错误'
    } finally {
      this.loading = false
    }
  }
}
</script>