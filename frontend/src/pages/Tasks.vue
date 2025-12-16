<script setup>
import { ref, computed, onMounted } from 'vue'
import { store } from '../store'
import { Plus, MapPin, X, DollarSign, Clock, Upload, Image as ImageIcon } from 'lucide-vue-next'

const isModalOpen = ref(false)
const activeTab = ref('available') // 'available' 或 'accepted'
const tasks = computed(() => store.state.tasks)
const user = computed(() => store.state.currentUser)
const acceptedTasks = ref([])

const form = ref({ title: '', bounty: '', location: '', notes: '' })
const imageFiles = ref([])
const imagePreviewUrls = ref([])

onMounted(async () => {
  await store.fetchTasks()
  if (user.value) {
    await loadAcceptedTasks()
  }
})

const loadAcceptedTasks = async () => {
  const result = await store.loadMyAcceptedTasks()
  if (result.success) {
    acceptedTasks.value = result.tasks
  }
}

const handleImageSelect = (event) => {
  const files = Array.from(event.target.files)
  imageFiles.value = files
  
  // 生成预览
  imagePreviewUrls.value = []
  files.forEach(file => {
    const reader = new FileReader()
    reader.onload = (e) => {
      imagePreviewUrls.value.push(e.target.result)
    }
    reader.readAsDataURL(file)
  })
}

const removeImage = (index) => {
  imageFiles.value.splice(index, 1)
  imagePreviewUrls.value.splice(index, 1)
}

const handlePost = async () => {
  if(!form.value.title) return
  
  const result = await store.postTask({
    title: form.value.title,
    bounty: Number(form.value.bounty) || 0,
    location: form.value.location,
    notes: form.value.notes,
    imageFiles: imageFiles.value
  })
  
  if (result.success) {
    isModalOpen.value = false
    form.value = { title: '', bounty: '', location: '', notes: '' }
    imageFiles.value = []
    imagePreviewUrls.value = []
  } else {
    alert(result.message || '发布失败')
  }
}

const handleGrab = async (id) => {
  if(!user.value) {
    alert('请先登录')
    return
  }
  
  if(confirm('确认要接下这个跑腿任务吗？')) {
    const result = await store.grabTask(id)
    if (result.success) {
      await loadAcceptedTasks()
      alert('抢单成功！')
    } else {
      alert(result.message || '抢单失败')
    }
  }
}

</script>

<template>
  <div class="task-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">跑腿大厅</h1>
        <p class="subtitle">互助互利，赚取零花钱</p>
      </div>
      <button @click="isModalOpen = true" class="primary-btn">
        <Plus size="20" stroke-width="2.5" /> 发布任务
      </button>
    </div>

    <!-- 标签页切换 -->
    <div class="tabs">
      <button 
        :class="['tab-btn', { active: activeTab === 'available' }]"
        @click="activeTab = 'available'"
      >
        可接任务
      </button>
      <button 
        :class="['tab-btn', { active: activeTab === 'accepted' }]"
        @click="activeTab = 'accepted'"
      >
        我的接单
      </button>
    </div>

    <!-- 可接任务列表 -->
    <div v-show="activeTab === 'available'" class="task-grid">
      <div v-for="task in tasks" :key="task.id" class="task-card">
        <div class="card-header">
          <span :class="['status-badge', task.status === '待接单' ? 'blue' : 'yellow']">{{ task.status }}</span>
          <div class="bounty-box">
            <DollarSign size="18" stroke-width="3" />
            <span>{{ task.bounty }}</span>
          </div>
        </div>
        
        <h3 class="task-title">{{ task.title }}</h3>
        
        <!-- 任务图片展示 -->
        <div v-if="task.images && task.images.length > 0" class="task-images">
          <img :src="task.images[0]" :alt="task.title" class="task-image" />
        </div>
        
        <p class="task-note">{{ task.notes }}</p>
        
        <div class="task-meta">
          <div class="meta-item"><MapPin size="14"/> {{ task.location || '无位置' }}</div>
          <div class="meta-item"><Clock size="14"/> {{ new Date(task.createdAt).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}</div>
        </div>

        <button 
          v-if="user && task.publisherId !== user.id && task.status === '待接单'"
          @click="handleGrab(task.id)" 
          class="grab-btn"
        >
          立即抢单
        </button>
      </div>
    </div>

    <!-- 已接单任务列表 -->
    <div v-show="activeTab === 'accepted'" class="task-grid">
      <div v-for="task in acceptedTasks" :key="task.id" class="task-card accepted">
        <div class="card-header">
          <span class="status-badge green">{{ task.status === 'completed' ? '已完成' : '进行中' }}</span>
          <div class="bounty-box">
            <DollarSign size="18" stroke-width="3" />
            <span>{{ task.bounty }}</span>
          </div>
        </div>
        
        <h3 class="task-title">{{ task.title }}</h3>
        
        <!-- 任务图片展示 -->
        <div v-if="task.images && task.images.length > 0" class="task-images">
          <img :src="task.images[0]" :alt="task.title" class="task-image" />
        </div>
        
        <p class="task-note">{{ task.notes }}</p>
        
        <div class="task-meta">
          <div class="meta-item"><MapPin size="14"/> {{ task.location || '无位置' }}</div>
          <div class="meta-item"><Clock size="14"/> 接单于 {{ new Date(task.acceptedAt).toLocaleDateString() }}</div>
        </div>
      </div>
      
      <div v-if="acceptedTasks.length === 0" class="empty-state">
        <p>暂无已接单的任务</p>
      </div>
    </div>

    <Transition name="modal">
      <div v-if="isModalOpen" class="modal-overlay" @click.self="isModalOpen = false">
        <div class="modal-container">
          <div class="modal-header">
            <h3>发布求助任务</h3>
            <button @click="isModalOpen = false" class="close-btn"><X size="22" /></button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>任务简述 <span class="required">*</span></label>
              <input v-model="form.title" placeholder="例如：代拿快递（中通）" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>赏金 (¥)</label>
                <input v-model="form.bounty" type="number" placeholder="5.00" />
              </div>
              <div class="form-group">
                <label>地点</label>
                <input v-model="form.location" placeholder="例如：北门 -> 宿舍A栋" />
              </div>
            </div>
            <div class="form-group">
              <div class="label-row">
                <label>备注要求</label>
              </div>
              <textarea v-model="form.notes" rows="3" placeholder="写清楚具体要求，方便同学接单..."></textarea>
            </div>
            
            <!-- 图片上传 -->
            <div class="form-group">
              <label>上传图片</label>
              <div class="upload-area">
                <input 
                  type="file" 
                  id="taskImages" 
                  multiple 
                  accept="image/*"
                  @change="handleImageSelect"
                  style="display: none"
                />
                <label for="taskImages" class="upload-btn">
                  <Upload size="20" />
                  <span>选择图片</span>
                </label>
              </div>
              
              <!-- 图片预览 -->
              <div v-if="imagePreviewUrls.length > 0" class="image-preview-grid">
                <div v-for="(url, index) in imagePreviewUrls" :key="index" class="preview-item">
                  <img :src="url" alt="预览" />
                  <button @click="removeImage(index)" class="remove-btn">
                    <X size="16" />
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="isModalOpen = false" class="cancel-btn">取消</button>
            <button @click="handlePost" class="primary-btn" :disabled="!form.title">立即发布</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; position: relative; z-index: 10; }
.page-title { font-size: 2rem; font-weight: 800; color: var(--text-main); letter-spacing: -0.5px; }
.subtitle { color: var(--text-secondary); font-size: 1rem; margin-top: 6px; }

/* 标签页 */
.tabs { display: flex; gap: 12px; margin-bottom: 24px; border-bottom: 2px solid var(--border); }
.tab-btn { padding: 12px 24px; background: transparent; border: none; color: var(--text-secondary); font-weight: 600; cursor: pointer; transition: all 0.2s; position: relative; }
.tab-btn:hover { color: var(--text-main); }
.tab-btn.active { color: var(--primary); }
.tab-btn.active::after { content: ''; position: absolute; bottom: -2px; left: 0; right: 0; height: 2px; background: var(--primary); }

.task-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 24px; }
.task-card { background: var(--bg-card); border-radius: 20px; padding: 28px; border: 1px solid var(--border); position: relative; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); display: flex; flex-direction: column; box-shadow: var(--shadow-sm); }
.task-card:hover { border-color: var(--primary); box-shadow: var(--shadow-md), 0 0 0 1px var(--primary) inset; transform: translateY(-4px); }
.task-card.accepted { border-color: #10b981; }
.task-card.accepted:hover { border-color: #059669; box-shadow: var(--shadow-md), 0 0 0 1px #059669 inset; }

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.status-badge { padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.5px; }
.status-badge.blue { background: #dbeafe; color: #1e40af; }
.status-badge.yellow { background: #fef3c7; color: #92400e; }
.status-badge.green { background: #d1fae5; color: #065f46; }
html.dark .status-badge.blue { background: #1d4ed8; color: #eff6ff; }
html.dark .status-badge.yellow { background: #854d0e; color: #fef9c3; }
html.dark .status-badge.green { background: #065f46; color: #d1fae5; }

.bounty-box { display: flex; align-items: center; color: #059669; font-weight: 800; font-size: 1.35rem; gap: 2px; }
.task-title { font-size: 1.35rem; font-weight: 700; color: var(--text-main); margin-bottom: 10px; line-height: 1.3; }

/* 任务图片 */
.task-images { margin-bottom: 16px; }
.task-image { width: 100%; height: 180px; object-fit: cover; border-radius: 12px; }

.task-note { color: var(--text-secondary); font-size: 1rem; margin-bottom: 24px; line-height: 1.6; flex: 1; }
.task-meta { display: flex; gap: 20px; margin-bottom: 28px; }
.meta-item { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; color: var(--text-secondary); font-weight: 500; }
.grab-btn { width: 100%; padding: 14px; border-radius: 14px; font-weight: 700; font-size: 1.05rem; background: var(--primary); color: white; transition: all 0.2s ease-in-out; box-shadow: var(--shadow-blue); }
.grab-btn:hover { filter: brightness(1.15); transform: translateY(-3px); box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.5); }
.grab-btn:active { transform: scale(0.98) translateY(0); box-shadow: none; }

/* 空状态 */
.empty-state { grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-secondary); }

.modal-overlay { position: fixed; inset: 0; z-index: 9999; background: var(--bg-modal-overlay); backdrop-filter: blur(6px); display: flex; justify-content: center; align-items: center; padding: 24px; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 520px; border-radius: 24px; box-shadow: var(--shadow-lg); display: flex; flex-direction: column; border: 1px solid var(--border); overflow: hidden; max-height: 90vh; }
.modal-header { padding: 24px 28px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg-body); }
.modal-header h3 { font-size: 1.35rem; font-weight: 700; color: var(--text-main); }
.close-btn { background: transparent; color: var(--text-secondary); padding: 8px; border-radius: 50%; transition: 0.2s; }
.close-btn:hover { background: var(--border); color: var(--text-main); }
.modal-body { padding: 28px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
.form-group label { display: block; margin-bottom: 8px; font-size: 0.95rem; font-weight: 600; color: var(--text-main); }
.required { color: #ef4444; margin-left: 4px; }
.form-row { display: flex; gap: 20px; }
.form-row .form-group { flex: 1; }
.label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }

/* 图片上传 */
.upload-area { margin-bottom: 16px; }
.upload-btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; background: var(--primary); color: white; border-radius: 12px; cursor: pointer; font-weight: 600; transition: all 0.2s; }
.upload-btn:hover { filter: brightness(1.1); }
.image-preview-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 12px; }
.preview-item { position: relative; aspect-ratio: 1; border-radius: 12px; overflow: hidden; border: 2px solid var(--border); }
.preview-item img { width: 100%; height: 100%; object-fit: cover; }
.remove-btn { position: absolute; top: 4px; right: 4px; background: rgba(0, 0, 0, 0.6); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; }
.remove-btn:hover { background: rgba(220, 38, 38, 0.9); }

.modal-footer { padding: 20px 28px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 16px; background: var(--bg-body); }
.cancel-btn { background: transparent; padding: 0.8rem 1.6rem; font-weight: 600; color: var(--text-secondary); border-radius: 12px; transition: 0.2s; }
.cancel-btn:hover { color: var(--text-main); background: var(--border); }
</style>