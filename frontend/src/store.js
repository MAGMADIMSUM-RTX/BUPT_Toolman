import { reactive } from 'vue'
import { API_BASE_URL } from './config.js'

// 仅保留 任务(Tasks) 和 消息(Chat) 的 Mock 数据
// 因为后端暂时还没有这两个模块的接口
const MOCK_TASKS = [
  { id: 't1', title: '北门取快递', status: '待接单', bounty: 5, location: '北门 -> A栋', notes: '文件袋', createdAt: Date.now() },
]
const MOCK_MESSAGES = []

export const store = reactive({
  state: {
    currentUser: JSON.parse(localStorage.getItem('user')) || null,
    items: [],
    tasks: [...MOCK_TASKS],
    messages: [...MOCK_MESSAGES]
  },

  // --- 真实登录逻辑 ---
  async login(studentId, password) {
    try {
      const res = await fetch(`${API_BASE_URL}/user/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ studentId, password })
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
})