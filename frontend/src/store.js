import { reactive } from 'vue'
import { API_BASE_URL } from './config.js'

// 仅保留 任务(Tasks) 的 Mock 数据
// 消息数据从后端实时加载
const MOCK_TASKS = [
  { id: 't1', title: '北门取快递', status: '待接单', bounty: 5, location: '北门 -> A栋', notes: '文件袋', createdAt: Date.now() },
]

export const store = reactive({
  state: {
    currentUser: JSON.parse(localStorage.getItem('user')) || null,
    items: [],
    tasks: [...MOCK_TASKS],
    messages: [],
    users: {} // 缓存用户信息
  },

  // --- 真实登录逻辑 ---
  async login(username, password) {
    try {
      const res = await fetch(`${API_BASE_URL}/user/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      const data = await res.json()
      
      if (res.ok) {
        this.state.currentUser = data.user
        localStorage.setItem('user', JSON.stringify(data.user))
        return { success: true }
      } else {
        return { success: false, message: data.error || '登录失败' }
      }
    } catch (e) {
      return { success: false, message: '无法连接到服务器' }
    }
  },

  logout() {
    this.state.currentUser = null
    this.state.messages = []
    this.state.users = {}
    localStorage.removeItem('user')
  },

  // --- 获取商品 (真实 API) ---
  async fetchItems() {
    try {
      const res = await fetch(`${API_BASE_URL}/goods/random?num=20`)
      if (res.ok) {
        const data = await res.json()
        this.state.items = data.map(item => ({
          id: item.id,
          title: item.name,
          price: item.value,
          description: item.description,
          sellerId: item.seller_id,
          status: item.status === 'available' ? '在售' : '已售',
          images: [`https://image.pollinations.ai/prompt/${encodeURIComponent(item.name)}?width=400&height=300&nologo=true`],
          category: '闲置'
        }))
      }
    } catch (e) {
      console.error(e)
    }
  },

  // --- 发布商品 (真实 API) ---
  async postItem(itemData) {
    // 1. 检查是否登录
    if (!this.state.currentUser) {
      return { success: false, message: '请先登录' }
    }

    // 2. 构造数据
    const payload = {
      name: itemData.title,
      seller_id: this.state.currentUser.id,
      num: 1,
      value: parseFloat(itemData.price),
      description: itemData.description,
      labels: [] // 暂时传空列表，防止后端解析报错
    }

    try {
      const res = await fetch(`${API_BASE_URL}/goods`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      const data = await res.json()

      if (res.ok) {
        await this.fetchItems() // 刷新列表
        return { success: true }
      } else {
        // 返回后端给出的具体错误 (data.error)
        return { success: false, message: data.error || '服务器处理失败' }
      }
    } catch (error) {
      console.error('发布商品失败:', error)
      return { success: false, message: '网络连接失败，请检查后端是否启动' }
    }
  },

  // --- 消息相关功能 (真实 API) ---
  async sendMessage(receiverId, text) {
    if (!this.state.currentUser) {
      return { success: false, message: '请先登录' }
    }

    if (!text || !text.trim()) {
      return { success: false, message: '消息不能为空' }
    }

    try {
      const res = await fetch(`${API_BASE_URL}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': this.state.currentUser.id
        },
        body: JSON.stringify({ receiver_id: receiverId, text: text.trim() })
      })

      const data = await res.json()

      if (res.ok) {
        // 将消息添加到本地状态
        this.state.messages.push(data)
        return { success: true, message: data }
      } else {
        return { success: false, message: data.error || '发送失败' }
      }
    } catch (e) {
      console.error('发送消息失败:', e)
      return { success: false, message: '网络连接失败' }
    }
  },

  async loadMessagesWithUser(userId) {
    if (!this.state.currentUser) {
      return { success: false, message: '请先登录' }
    }

    try {
      const res = await fetch(`${API_BASE_URL}/messages/${userId}`, {
        method: 'GET',
        headers: {
          'X-User-ID': this.state.currentUser.id
        }
      })

      if (res.ok) {
        const messages = await res.json()
        // 更新状态中的消息 (只保留与当前用户的对话)
        this.state.messages = messages
        return { success: true }
      } else {
        console.error('加载消息失败')
        return { success: false, message: '加载消息失败' }
      }
    } catch (e) {
      console.error('加载消息出错:', e)
      return { success: false, message: '网络连接失败' }
    }
  },

  async loadChatUsers() {
    if (!this.state.currentUser) {
      return { success: false, message: '请先登录' }
    }

    try {
      const res = await fetch(`${API_BASE_URL}/messages/list`, {
        method: 'GET',
        headers: {
          'X-User-ID': this.state.currentUser.id
        }
      })

      if (res.ok) {
        const users = await res.json()
        // 缓存这些用户信息
        users.forEach(u => {
          this.state.users[u.id] = u
        })
        return { success: true, users }
      } else {
        return { success: false, message: '加载对话列表失败' }
      }
    } catch (e) {
      console.error('加载对话列表出错:', e)
      return { success: false, message: '网络连接失败' }
    }
  },

  getUser(userId) {
    // 优先从缓存中获取，否则返回基本信息（通常由 loadChatUsers 填充）
    return this.state.users[userId] || null
  },

  setActiveChatUser(user) {
    // 设置激活的聊天用户（从商品详情页面跳转过来时使用）
    this.state.users[user.id] = user
    return user
  },
})
