<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { store } from '../store'
import { API_BASE_URL } from '../config.js'
import { LogOut, Star, Wallet, MapPin, Clock, Camera, Settings, X } from 'lucide-vue-next'

const router = useRouter()
const activeTab = ref('items')
const user = computed(() => store.state.currentUser)
const fileInput = ref(null)

// 偏好设置相关
const isPreferencesOpen = ref(false)
const labels = ref([])
const selectedLabels = ref([])
const loadingPreferences = ref(false)
const savingPreferences = ref(false)

const myItems = computed(() => {
  if (!user.value) return []
  return store.state.items.filter(i => i.sellerId === user.value.id)
})

const myTasks = computed(() => {
  if (!user.value) return []
  return store.state.tasks.filter(t => t.publisherId === user.value.id || t.runnerId === user.value.id)
})

const handleLogout = () => { store.logout(); router.push('/login') }

// 触发头像上传
const triggerUpload = () => {
  fileInput.value.click()
}

// 处理头像文件选择
const handleAvatarChange = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  
  // 简单的前端校验
  if (!['image/jpeg', 'image/png', 'image/gif'].includes(file.type)) {
    alert('请上传 JPG/PNG/GIF 格式的图片')
    return
  }

  const result = await store.uploadAvatar(file)
  if (result.success) {
    alert('头像更新成功')
  } else {
    alert(result.message)
  }
}

const openPreferences = async () => {
  if (!user.value) return
  isPreferencesOpen.value = true
  loadingPreferences.value = true
  
  try {
    // 1. 获取所有标签
    const labelsRes = await fetch(`${API_BASE_URL}/labels`)
    if (labelsRes.ok) {
      const allLabels = await labelsRes.json()
      // 过滤出可订阅的标签
      labels.value = allLabels.filter(l => l.can_subscribe)
    }

    // 2. 获取用户最新信息（包含偏好）
    const userRes = await fetch(`${API_BASE_URL}/user/${user.value.id}`)
    if (userRes.ok) {
      const userData = await userRes.json()
      selectedLabels.value = userData.prefer || []
    }
  } catch (e) {
    console.error('Failed to load preferences', e)
    alert('加载偏好设置失败')
  } finally {
    loadingPreferences.value = false
  }
}

const savePreferences = async () => {
  if (!user.value) return
  savingPreferences.value = true
  
  try {
    const res = await fetch(`${API_BASE_URL}/user/${user.value.id}/preferences`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ labels: selectedLabels.value })
    })
    
    const data = await res.json()
    if (res.ok) {
      alert('偏好设置已更新！')
      isPreferencesOpen.value = false
      // 更新本地 store 中的用户信息（可选）
      // store.updateUser({ ...user.value, prefer: selectedLabels.value })
    } else {
      alert(data.error || '更新失败')
    }
  } catch (e) {
    alert('网络错误')
  } finally {
    savingPreferences.value = false
  }
}

const statusColor = (status) => {
  switch(status) {
    case '待接单': return 'blue'
    case '进行中': return 'yellow'
    case '已完成': return 'green'
    default: return 'gray'
  }
}
</script>

<template>
  <div v-if="user">
    <div class="profile-header">
      <div class="user-info">
        <div class="avatar-wrapper" @click="triggerUpload">
            <img :src="user.avatar" class="profile-avatar" />
            <div class="avatar-overlay">
                <Camera size="24" color="white"/>
            </div>
            <input 
                type="file" 
                ref="fileInput" 
                hidden 
                accept="image/*" 
                @change="handleAvatarChange"
            />
        </div>

        <div>
          <h1 class="profile-name">{{ user.name }}</h1>
          <p class="profile-id">Email: {{ user.email }}</p>
          <div class="badges">
            <span class="stat-badge yellow"><Star size="14" fill="currentColor"/> 信用分: {{ user.creditScore }}</span>
            <span class="stat-badge green"><Wallet size="14"/> 余额: ¥{{ user.balance.toFixed(2) }}</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <button @click="openPreferences" class="outline-btn"><Settings size="16" /> 偏好设置</button>
        <button @click="handleLogout" class="outline-btn"><LogOut size="16" /> 退出登录</button>
      </div>
    </div>

    <div class="tabs">
      <button @click="activeTab='items'" :class="['tab-item', activeTab==='items'?'active':'']">我发布的商品 ({{ myItems.length }})</button>
      <button @click="activeTab='tasks'" :class="['tab-item', activeTab==='tasks'?'active':'']">我的任务 ({{ myTasks.length }})</button>
    </div>

    <div class="tab-content">
      
      <div v-if="activeTab === 'items'">
        <div v-if="myItems.length === 0" class="empty-state">暂无发布商品。</div>
        <div class="goods-grid">
          <div v-for="item in myItems" :key="item.id" class="goods-card">
            <div class="img-box">
              <img :src="item.images[0]" class="goods-img" />
              <div v-if="item.status === '已售'" class="sold-mask">已售</div>
            </div>
            <div class="info-box">
              <h3 class="goods-title">{{ item.title }}</h3>
              <div class="goods-footer">
                <span class="price">¥{{ item.price }}</span>
                <span class="tag">{{ item.status }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'tasks'">
        <div v-if="myTasks.length === 0" class="empty-state">暂无相关任务。</div>
        <div class="task-list">
          <div v-for="task in myTasks" :key="task.id" class="task-row">
            <div class="task-main">
              <div class="task-top">
                <span :class="['status-dot', statusColor(task.status)]"></span>
                <span class="task-status-text">{{ task.status }}</span>
                <span class="task-title">{{ task.title }}</span>
              </div>
              <div class="task-meta">
                <span v-if="task.location"><MapPin size="12"/> {{ task.location }}</span>
                <span><Clock size="12"/> {{ new Date(task.createdAt).toLocaleDateString() }}</span>
              </div>
            </div>
            <div class="task-right">
              <span class="bounty">+ {{ task.bounty }}</span>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- 偏好设置弹窗 -->
    <Transition name="modal">
      <div v-if="isPreferencesOpen" class="modal-overlay" @click.self="isPreferencesOpen = false">
        <div class="modal-container">
          <div class="modal-header">
            <h3>偏好设置</h3>
            <button @click="isPreferencesOpen = false" class="close-btn"><X size="22" /></button>
          </div>
          <div class="modal-body">
            <p class="hint-text">选择你感兴趣的分类，当有新品上架时我们会通知你。</p>
            
            <div v-if="loadingPreferences" class="loading-text">加载中...</div>
            
            <div v-else class="tags-grid">
              <label 
                v-for="label in labels" 
                :key="label.id" 
                class="tag-item"
                :class="{ active: selectedLabels.includes(label.id) }"
              >
                <input 
                  type="checkbox" 
                  :value="label.id" 
                  v-model="selectedLabels"
                  hidden
                />
                {{ label.name }}
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="isPreferencesOpen = false" class="cancel-btn">取消</button>
            <button @click="savePreferences" class="primary-btn" :disabled="savingPreferences">
              {{ savingPreferences ? '保存中...' : '保存设置' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.profile-header { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 30px; display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; }
.user-info { display: flex; gap: 24px; align-items: center; }
.header-actions { display: flex; gap: 12px; }

/* 头像交互样式 */
.avatar-wrapper { position: relative; cursor: pointer; width: 80px; height: 80px; border-radius: 50%; overflow: hidden; border: 4px solid var(--bg-body); }
.profile-avatar { width: 100%; height: 100%; object-fit: cover; }
.avatar-overlay {
    position: absolute; inset: 0;
    background: rgba(0,0,0,0.4);
    display: flex; justify-content: center; align-items: center;
    opacity: 0; transition: opacity 0.2s;
}
.avatar-wrapper:hover .avatar-overlay { opacity: 1; }

.profile-name { font-size: 1.5rem; font-weight: 800; color: var(--text-main); margin-bottom: 4px; }
.profile-id { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 12px; }
.badges { display: flex; gap: 10px; }
.stat-badge { display: flex; align-items: center; gap: 4px; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; }
.stat-badge.yellow { background: #fffbeb; color: #b45309; }
.stat-badge.green { background: #ecfdf5; color: #047857; }
html.dark .stat-badge.yellow { background: #451a03; color: #fcd34d; }
html.dark .stat-badge.green { background: #064e3b; color: #6ee7b7; }
.outline-btn { background: transparent; border: 1px solid var(--border); color: var(--text-secondary); padding: 8px 16px; border-radius: 6px; display: flex; align-items: center; gap: 6px; font-size: 0.9rem; transition: 0.2s; }
.outline-btn:hover { background: var(--bg-body); color: var(--text-main); }
.tabs { display: flex; gap: 30px; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
.tab-item { background: none; border: none; padding-bottom: 12px; font-size: 1rem; color: var(--text-secondary); border-bottom: 2px solid transparent; transition: 0.2s; }
.tab-item.active { color: var(--primary); border-bottom-color: var(--primary); font-weight: 600; }
.empty-state { text-align: center; color: var(--text-secondary); padding: 50px 0; }
.goods-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }
.goods-card { background: var(--bg-card); border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }
.img-box { height: 140px; position: relative; background: #eee; }
.goods-img { width: 100%; height: 100%; object-fit: cover; }
.sold-mask { position: absolute; inset: 0; background: rgba(0,0,0,0.6); color: white; display: flex; justify-content: center; align-items: center; font-weight: bold; }
.info-box { padding: 12px; }
.goods-title { font-size: 1rem; font-weight: 600; color: var(--text-main); margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.goods-footer { display: flex; justify-content: space-between; align-items: center; }
.price { color: var(--primary); font-weight: 700; }
.tag { font-size: 0.75rem; color: var(--text-secondary); background: var(--bg-body); padding: 2px 6px; border-radius: 4px; }
.task-list { display: flex; flex-direction: column; gap: 12px; }
.task-row { background: var(--bg-card); padding: 16px; border-radius: 12px; border: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.task-top { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.task-title { font-weight: 600; color: var(--text-main); }
.task-status-text { font-size: 0.8rem; color: var(--text-secondary); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.blue { background: #3b82f6; }
.status-dot.yellow { background: #eab308; }
.status-dot.green { background: #22c55e; }
.status-dot.gray { background: #9ca3af; }
.task-meta { display: flex; gap: 12px; font-size: 0.8rem; color: var(--text-secondary); }
.task-meta span { display: flex; align-items: center; gap: 4px; }
.bounty { font-weight: 700; color: #10b981; font-size: 1.1rem; }

/* Modal Styles */
.modal-overlay { position: fixed; inset: 0; z-index: 9999; background: var(--bg-modal-overlay); backdrop-filter: blur(6px); display: flex; justify-content: center; align-items: center; padding: 24px; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 520px; border-radius: 24px; box-shadow: var(--shadow-lg); display: flex; flex-direction: column; border: 1px solid var(--border); overflow: hidden; max-height: 90vh; }
.modal-header { padding: 24px 28px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg-body); }
.modal-header h3 { font-size: 1.35rem; font-weight: 700; color: var(--text-main); }
.close-btn { background: transparent; color: var(--text-secondary); padding: 8px; border-radius: 50%; transition: 0.2s; border: none; cursor: pointer; }
.close-btn:hover { background: var(--border); color: var(--text-main); }
.modal-body { padding: 28px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
.modal-footer { padding: 20px 28px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 16px; background: var(--bg-body); }
.hint-text { color: var(--text-secondary); font-size: 0.95rem; }
.loading-text { text-align: center; color: var(--text-secondary); padding: 20px; }

.tags-grid { display: flex; flex-wrap: wrap; gap: 12px; }
.tag-item { 
  padding: 8px 16px; 
  background: var(--bg-input); 
  border-radius: 20px; 
  cursor: pointer; 
  font-size: 0.9rem; 
  color: var(--text-secondary);
  border: 1px solid transparent;
  transition: all 0.2s;
}
.tag-item:hover { background: var(--border); }
.tag-item.active { 
  background: #eff6ff; 
  color: var(--primary); 
  border-color: var(--primary); 
  font-weight: 600;
}
html.dark .tag-item.active { background: rgba(59, 130, 246, 0.2); }

.primary-btn { background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s; }
.primary-btn:hover { opacity: 0.9; }
.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.cancel-btn { background: transparent; padding: 10px 20px; font-weight: 600; color: var(--text-secondary); border-radius: 8px; border: none; cursor: pointer; }
.cancel-btn:hover { color: var(--text-main); background: var(--border); }
</style>