<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { store } from '../store'
import { Send, MessageSquare } from 'lucide-vue-next'

const currentUser = computed(() => store.state.currentUser)
const text = ref('')
const activeChatUser = ref(null)
const scrollRef = ref(null)
const loading = ref(true)
let pollInterval = null

const chatUsers = computed(() => {
  if (!currentUser.value) return []
  // 返回所有有过消息的用户，如果没有则返回当前激活用户
  const users = Object.values(store.state.users).filter(Boolean)
  if (users.length === 0 && activeChatUser.value) {
    return [activeChatUser.value]
  }
  return users
})

const scrollToBottom = async () => {
  await nextTick()
  if (scrollRef.value) {
    scrollRef.value.scrollTop = scrollRef.value.scrollHeight
  }
}

// 启动消息轮询
const startPolling = async () => {
  if (pollInterval) clearInterval(pollInterval)
  
  // 首次立即加载
  if (activeChatUser.value && currentUser.value) {
    await store.loadMessagesWithUser(activeChatUser.value.id)
  }
  
  // 每 0.5 秒检查一次新消息
  pollInterval = setInterval(async () => {
    if (activeChatUser.value && currentUser.value) {
      await store.loadMessagesWithUser(activeChatUser.value.id)
    }
  }, 500)
}

// 停止消息轮询
const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onMounted(async () => {
  if (!currentUser.value) return
  
  // 检查是否有预设的对话用户（从商品详情页面跳转过来）
  const presetUser = Object.values(store.state.users).find(u => u && u.id)
  
  if (presetUser) {
    // 直接使用预设的用户
    activeChatUser.value = presetUser
    loading.value = false
  } else {
    // 加载对话列表
    const result = await store.loadChatUsers()
    if (result.success && result.users.length > 0) {
      activeChatUser.value = result.users[0]
    }
    loading.value = false
  }
  
  // 启动轮询
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

const activeMessages = computed(() => {
  if (!currentUser.value || !activeChatUser.value) return []
  return store.state.messages.filter(m => 
    (m.senderId === currentUser.value.id && m.receiverId === activeChatUser.value.id) ||
    (m.senderId === activeChatUser.value.id && m.receiverId === currentUser.value.id)
  )
})

watch(activeMessages, scrollToBottom, { deep: true })

watch(activeChatUser, async (newUser) => {
  if (newUser && currentUser.value) {
    scrollToBottom()
    // 重启轮询以加载新对话的消息
    startPolling()
  }
})

const handleSend = async () => {
  if (!text.value.trim() || !activeChatUser.value) return
  
  const messageText = text.value.trim()
  text.value = ''
  
  const result = await store.sendMessage(activeChatUser.value.id, messageText)
  if (!result.success) {
    alert('发送失败：' + result.message)
    text.value = messageText // 恢复文本
  } else {
    // 确保该用户在对话列表中
    if (!store.state.users[activeChatUser.value.id]) {
      store.setActiveChatUser(activeChatUser.value)
    }
  }
}
</script>

<template>
  <div class="chat-layout">
    <div class="sidebar">
      <div class="sidebar-header">消息列表</div>
      <div class="user-list">
        <div v-if="loading" class="empty-list">加载中...</div>
        <div v-else-if="chatUsers.length === 0" class="empty-list">暂无消息</div>
        <div 
          v-for="u in chatUsers" 
          :key="u.id"
          @click="activeChatUser = u"
          :class="['user-item', activeChatUser?.id === u.id ? 'active' : '']"
        >
          <img :src="u.avatar" class="avatar" />
          <div class="user-info">
            <div class="name">{{ u.name }}</div>
            <div class="sub-text">点击查看消息</div>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-window">
      <div v-if="activeChatUser" class="chat-content">
        <div class="chat-header">
          <span class="chat-title">{{ activeChatUser.name }}</span>
        </div>
        
        <div class="messages-area" ref="scrollRef">
          <div v-for="m in activeMessages" :key="m.id" :class="['msg-row', m.senderId === currentUser?.id ? 'msg-right' : 'msg-left']">
            <img v-if="m.senderId !== currentUser?.id" :src="activeChatUser.avatar" class="msg-avatar" />
            <div class="bubble">
              {{ m.text }}
            </div>
            <img v-if="m.senderId === currentUser?.id" :src="currentUser.avatar" class="msg-avatar" />
          </div>
        </div>

        <form @submit.prevent="handleSend" class="input-area">
          <input v-model="text" placeholder="输入消息..." class="chat-input" />
          <button type="submit" :disabled="!text.trim()" class="send-btn">
            <Send size="18" />
          </button>
        </form>
      </div>

      <div v-else class="empty-chat">
        <div class="empty-icon-circle">
          <MessageSquare size="40" stroke-width="1.5" />
        </div>
        <p v-if="!loading">选择一个联系人开始聊天</p>
        <p v-else>加载中...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-layout { display: flex; height: calc(100vh - 120px); background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-sm); }
.sidebar { width: 280px; border-right: 1px solid var(--border); display: flex; flex-direction: column; background: var(--bg-body); }
.sidebar-header { padding: 20px; font-weight: 700; color: var(--text-main); border-bottom: 1px solid var(--border); background: var(--bg-card); }
.user-list { flex: 1; overflow-y: auto; }
.user-item { display: flex; align-items: center; gap: 12px; padding: 16px 20px; cursor: pointer; transition: background 0.2s; border-bottom: 1px solid transparent; }
.user-item:hover { background: var(--bg-input); }
.user-item.active { background: var(--bg-card); border-left: 4px solid var(--primary); }
.avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.name { font-weight: 600; font-size: 0.95rem; color: var(--text-main); }
.sub-text { font-size: 0.8rem; color: var(--text-secondary); }
.empty-list { padding: 20px; text-align: center; color: var(--text-secondary); font-size: 0.9rem; }
.chat-window { flex: 1; display: flex; flex-direction: column; background: var(--bg-card); }
.chat-content { display: flex; flex-direction: column; height: 100%; }
.chat-header { padding: 16px 24px; border-bottom: 1px solid var(--border); font-weight: 700; font-size: 1.1rem; color: var(--text-main); }
.messages-area { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; background: var(--bg-body); }
.msg-row { display: flex; gap: 12px; align-items: center; max-width: 80%; }
.msg-left { align-self: flex-start; }
.msg-right { align-self: flex-end; justify-content: flex-end; }
.msg-avatar { width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0; }
.bubble { padding: 10px 16px; border-radius: 18px; font-size: 0.95rem; line-height: 1.5; position: relative; word-wrap: break-word; box-shadow: var(--shadow-sm); }
.msg-left .bubble { background: var(--bg-card); border: 1px solid var(--border); color: var(--text-main); border-bottom-left-radius: 4px; }
.msg-right .bubble { background: var(--primary-gradient); color: white; border: none; border-bottom-right-radius: 4px; box-shadow: var(--shadow-blue); }
.input-area { padding: 16px 24px; border-top: 1px solid var(--border); display: flex; gap: 12px; background: var(--bg-card); }
.chat-input { flex: 1; border-radius: 24px; padding-left: 20px; }
.send-btn { background: var(--primary-gradient); color: white; width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: 0.2s; box-shadow: var(--shadow-blue); }
.send-btn:hover { transform: scale(1.05); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }
.empty-chat { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-secondary); }
.empty-icon-circle { width: 80px; height: 80px; background: var(--bg-body); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; color: var(--primary); }
</style>