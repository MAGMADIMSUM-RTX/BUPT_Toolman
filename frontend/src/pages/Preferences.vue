<template>
  <div>
    <h1>偏好设置</h1>
    
    <div class="section">
      <label>用户 ID:</label>
      <input v-model.number="userId" type="number" placeholder="输入你的用户ID" />
      <button @click="loadPreferences" :disabled="!userId">加载当前偏好</button>
    </div>

    <div v-if="loading">加载中...</div>
    
    <div v-else-if="labels.length > 0" class="section">
      <h3>选择你感兴趣的标签：</h3>
      <div class="tags">
        <label v-for="label in labels" :key="label.id" class="tag-item">
          <input 
            type="checkbox" 
            :value="label.id" 
            v-model="selectedLabels"
          />
          {{ label.name }}
        </label>
      </div>
      
      <div class="actions">
        <button @click="savePreferences" :disabled="saving">
          {{ saving ? '保存中...' : '保存偏好' }}
        </button>
      </div>
    </div>

    <p v-if="message" :class="{ error: isError }">{{ message }}</p>
  </div>
</template>

<script>
import { API_BASE_URL } from '../config.js'

export default {
  name: 'Preferences',
  data() {
    return {
      userId: '',
      labels: [],
      selectedLabels: [],
      loading: false,
      saving: false,
      message: '',
      isError: false
    }
  },
  async mounted() {
    await this.fetchLabels()
  },
  methods: {
    async fetchLabels() {
      try {
        const res = await fetch(`${API_BASE_URL}/labels`)
        if (res.ok) {
          const allLabels = await res.json()
          // Only show labels that are marked as prefered
          this.labels = allLabels.filter(l => l.prefered)
        }
      } catch (e) {
        console.error('Failed to fetch labels', e)
      }
    },
    async loadPreferences() {
      if (!this.userId) return
      
      // Since we don't have a direct GET /user/:id/preferences endpoint yet,
      // we might need to rely on user knowing what they want, 
      // OR we could add a GET endpoint. 
      // For now, let's just allow setting them.
      // If we want to show current, we need to fetch user info.
      // Let's try to fetch user info if endpoint exists, otherwise just clear selection.
      
      // Assuming we don't have GET preferences, we just start fresh or keep selection.
      this.message = '请选择新的偏好并保存'
      this.isError = false
    },
    async savePreferences() {
      if (!this.userId) {
        this.message = '请输入用户ID'
        this.isError = true
        return
      }
      
      this.saving = true
      this.message = ''
      this.isError = false
      
      try {
        const res = await fetch(`${API_BASE_URL}/user/${this.userId}/preferences`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ labels: this.selectedLabels })
        })
        
        const data = await res.json()
        if (res.ok) {
          this.message = '偏好设置已更新！'
        } else {
          this.message = data.error || '更新失败'
          this.isError = true
        }
      } catch (e) {
        this.message = '网络错误'
        this.isError = true
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.section {
  margin-bottom: 20px;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 10px 0;
}
.tag-item {
  padding: 5px 10px;
  background: #f0f0f0;
  border-radius: 4px;
  cursor: pointer;
}
.tag-item:hover {
  background: #e0e0e0;
}
.actions {
  margin-top: 20px;
}
.error {
  color: red;
}
</style>