<script setup>
import { ref, computed } from 'vue'
import { store } from '../store'
import { Plus, MapPin, Sparkles, X, DollarSign, Clock } from 'lucide-vue-next'
import { generateDescription } from '../services/gemini'

const isModalOpen = ref(false)
const isGenerating = ref(false)
const tasks = computed(() => store.state.tasks)
const user = computed(() => store.state.currentUser)

const form = ref({ title: '', bounty: '', location: '', notes: '' })

const handlePost = () => {
  if(!form.value.title) return
  store.postTask({
    title: form.value.title,
    bounty: Number(form.value.bounty),
    location: form.value.location,
    notes: form.value.notes
  })
  isModalOpen.value = false
  form.value = { title: '', bounty: '', location: '', notes: '' }
}

const handleGrab = (id) => {
  if(confirm('确认要接下这个跑腿任务吗？')) store.grabTask(id)
}

const handleAIHelp = async () => {
  if (!form.value.title) return
  isGenerating.value = true
  const draft = form.value.notes || `帮我做：${form.value.title}，送到${form.value.location}。`
  const polished = await generateDescription(draft, 'task')
  form.value.notes = polished
  isGenerating.value = false
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

    <div class="task-grid">
      <div v-for="task in tasks" :key="task.id" class="task-card">
        <div class="card-header">
          <span :class="['status-badge', task.status === '待接单' ? 'blue' : 'yellow']">{{ task.status }}</span>
          <div class="bounty-box">
            <DollarSign size="18" stroke-width="3" />
            <span>{{ task.bounty }}</span>
          </div>
        </div>
        
        <h3 class="task-title">{{ task.title }}</h3>
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
                <button @click="handleAIHelp" :disabled="isGenerating || !form.title" class="ai-btn">
                  <Sparkles size="14" /> AI 优化
                </button>
              </div>
              <textarea v-model="form.notes" rows="3" placeholder="写清楚具体要求，方便同学接单..."></textarea>
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
/* 修复头部点击问题的关键样式 */
.page-header { 
  display: flex; justify-content: space-between; align-items: center; 
  margin-bottom: 32px; 
  position: relative; z-index: 10; /* 确保在最上层 */
}
.page-title { font-size: 2rem; font-weight: 800; color: var(--text-main); letter-spacing: -0.5px; }
.subtitle { color: var(--text-secondary); font-size: 1rem; margin-top: 6px; }

.task-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 24px; }

/* 任务卡片新风格 */
.task-card {
  background: var(--bg-card); border-radius: 20px; padding: 28px;
  border: 1px solid var(--border); position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
  display: flex; flex-direction: column;
  box-shadow: var(--shadow-sm);
}
.task-card:hover { 
  border-color: var(--primary);
  box-shadow: var(--shadow-md), 0 0 0 1px var(--primary) inset; /* 蓝色内描边 */
  transform: translateY(-4px);
}

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.status-badge { padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.5px; }
.status-badge.blue { background: #dbeafe; color: #1e40af; }
.status-badge.yellow { background: #fef3c7; color: #92400e; }
html.dark .status-badge.blue { background: #1d4ed8; color: #eff6ff; }
html.dark .status-badge.yellow { background: #854d0e; color: #fef9c3; }

.bounty-box { display: flex; align-items: center; color: #059669; font-weight: 800; font-size: 1.35rem; gap: 2px; }

.task-title { font-size: 1.35rem; font-weight: 700; color: var(--text-main); margin-bottom: 10px; line-height: 1.3; }
.task-note { color: var(--text-secondary); font-size: 1rem; margin-bottom: 24px; line-height: 1.6; flex: 1; }

.task-meta { display: flex; gap: 20px; margin-bottom: 28px; }
.meta-item { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; color: var(--text-secondary); font-weight: 500; }

.grab-btn {
  width: 100%; 
  padding: 14px; 
  border-radius: 14px; 
  font-weight: 700; 
  font-size: 1.05rem;
  /* 修改这里：改成纯蓝色背景，确保醒目 */
  background: var(--primary); 
  color: white; 
  transition: all 0.2s ease-in-out;
  box-shadow: var(--shadow-blue);
}

.grab-btn:hover { 
  /* 鼠标放上去变亮一点，往上浮动一点 */
  filter: brightness(1.15); 
  transform: translateY(-3px); 
  box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.5); 
}

.grab-btn:active {
  /* 点击时按下去的效果 */
  transform: scale(0.98) translateY(0);
  box-shadow: none;
}

/* 弹窗样式 (复用，但风格更新) */
.modal-overlay { position: fixed; inset: 0; z-index: 9999; background: var(--bg-modal-overlay); backdrop-filter: blur(6px); display: flex; justify-content: center; align-items: center; padding: 24px; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 520px; border-radius: 24px; box-shadow: var(--shadow-lg); display: flex; flex-direction: column; border: 1px solid var(--border); overflow: hidden; }
.modal-header { padding: 24px 28px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg-body); }
.modal-header h3 { font-size: 1.35rem; font-weight: 700; color: var(--text-main); }
.close-btn { background: transparent; color: var(--text-secondary); padding: 8px; border-radius: 50%; transition: 0.2s; }
.close-btn:hover { background: var(--border); color: var(--text-main); }
.modal-body { padding: 28px; display: flex; flex-direction: column; gap: 20px; }
.form-group label { display: block; margin-bottom: 8px; font-size: 0.95rem; font-weight: 600; color: var(--text-main); }
.required { color: #ef4444; margin-left: 4px; }
.form-row { display: flex; gap: 20px; }
.form-row .form-group { flex: 1; }
.label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.ai-btn { background: none; color: var(--primary); font-size: 0.85rem; display: flex; align-items: center; gap: 6px; font-weight: 600; padding: 4px 8px; border-radius: 6px; transition: 0.2s; }
.ai-btn:hover { background: var(--bg-input); }
.modal-footer { padding: 20px 28px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 16px; background: var(--bg-body); }
.cancel-btn { background: transparent; padding: 0.8rem 1.6rem; font-weight: 600; color: var(--text-secondary); border-radius: 12px; transition: 0.2s; }
.cancel-btn:hover { color: var(--text-main); background: var(--border); }
</style>