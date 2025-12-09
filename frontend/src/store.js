import { reactive } from 'vue'
import { API_BASE_URL } from './config.js'

// 仅保留 任务(Tasks) 和 消息(Chat) 的 Mock 数据
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

  // --- 登录逻辑 ---
  async login(username, password) {
    try {
      const res = await fetch(`${API_BASE_URL}/user/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      const data = await res.json()
      
      if (res.ok) {
        this.updateUser(data.user)
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

  // 辅助：更新本地用户状态并持久化
  updateUser(userData) {
    // 强制刷新头像缓存 (后端覆盖文件，浏览器可能缓存)
    if (userData.avatar) {
        // 如果包含 media 路径但不包含 host，拼接一下 (视后端返回情况而定)
        if (userData.avatar.startsWith('/media')) {
            userData.avatar = `${API_BASE_URL}${userData.avatar}`
        }
        userData.avatar = `${userData.avatar}?t=${new Date().getTime()}`
    }
    this.state.currentUser = userData
    localStorage.setItem('user', JSON.stringify(userData))
  },

  // --- 获取商品 (适配后端，额外获取图片) ---
  async fetchItems() {
    try {
      const res = await fetch(`${API_BASE_URL}/goods/random?num=20`)
      if (res.ok) {
        const rawData = await res.json()
        
        // 并行请求所有商品的图片
        const itemsWithImages = await Promise.all(rawData.map(async (item) => {
          let imageUrls = []
          try {
            // 调用后端获取该商品的图片链接
            const imgRes = await fetch(`${API_BASE_URL}/good/${item.id}/images`)
            if (imgRes.ok) {
              const imgData = await imgRes.json()
              // 后端返回 { image_urls: [...] }
              if (imgData.image_urls && imgData.image_urls.length > 0) {
                // 补全 URL 前缀
                imageUrls = imgData.image_urls.map(url => `${API_BASE_URL}${url}`)
              }
            }
          } catch (err) {
            console.warn(`Failed to fetch images for good ${item.id}`)
          }

          // 如果没有图片，给一个默认占位图
          if (imageUrls.length === 0) {
            imageUrls = ['https://via.placeholder.com/400x300?text=No+Image']
          }

          return {
            id: item.id,
            title: item.name,
            price: item.value,
            description: item.description,
            sellerId: item.seller_id,
            status: item.status === 'available' ? '在售' : '已售',
            images: imageUrls,
            category: '闲置'
          }
        }))

        this.state.items = itemsWithImages
      }
    } catch (e) {
      console.error(e)
    }
  },

  // --- 发布商品 (分两步：先创建商品，后上传图片) ---
  async postItem(itemData) {
    if (!this.state.currentUser) {
      return { success: false, message: '请先登录' }
    }

    // 1. 创建商品信息
    const payload = {
      name: itemData.title,
      seller_id: this.state.currentUser.id,
      num: 1,
      value: parseFloat(itemData.price),
      description: itemData.description,
      labels: [] 
    }

    try {
      const res = await fetch(`${API_BASE_URL}/goods`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      const newGood = await res.json()

      if (!res.ok) {
        return { success: false, message: newGood.error || '创建商品失败' }
      }

      // 2. 上传图片 (如果有)
      if (itemData.imageFiles && itemData.imageFiles.length > 0) {
        const formData = new FormData()
        formData.append('type', 'good')
        formData.append('id', newGood.id) // 使用新创建的商品ID
        
        // 遍历添加文件
        for (let i = 0; i < itemData.imageFiles.length; i++) {
          formData.append('files', itemData.imageFiles[i])
        }

        const uploadRes = await fetch(`${API_BASE_URL}/upload`, {
          method: 'POST',
          body: formData
        })
        
        if (!uploadRes.ok) {
          const errData = await uploadRes.json()
          return { success: true, message: `商品发布成功，但图片上传失败: ${errData.error}` }
        }
      }

      await this.fetchItems() // 刷新列表
      return { success: true }

    } catch (error) {
      console.error('发布流程错误:', error)
      return { success: false, message: '网络连接失败' }
    }
  },

  // --- 上传头像 ---
  async uploadAvatar(file) {
    if (!this.state.currentUser) return { success: false, message: '未登录' }

    const formData = new FormData()
    formData.append('type', 'avatar')
    formData.append('id', this.state.currentUser.id)
    formData.append('files', file)

    try {
      const res = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
      })
      
      const data = await res.json()
      if (res.ok) {
        // 上传成功后，重新获取用户信息以得到最新的头像URL
        await this.refreshUserProfile()
        return { success: true }
      } else {
        return { success: false, message: data.error || '上传失败' }
      }
    } catch (e) {
      return { success: false, message: '网络错误' }
    }
  },

  // 刷新用户信息
  async refreshUserProfile() {
    if (!this.state.currentUser) return
    try {
        const res = await fetch(`${API_BASE_URL}/user/${this.state.currentUser.id}`)
        if (res.ok) {
            const userData = await res.json()
            // 补充头像逻辑：如果是相对路径，且后端get_user_info返回的avatar是接口生成的
            // 后端 app.py 的 get_user_info 现在返回的是picsum默认图。
            // 我们需要手动请求一下 /user/<id>/avatar 接口确认是否有真实头像
            
            const avatarRes = await fetch(`${API_BASE_URL}/user/${userData.id}/avatar`)
            if (avatarRes.ok) {
                const avatarData = await avatarRes.json()
                if (avatarData.avatar_url) {
                    userData.avatar = avatarData.avatar_url
                }
            }
            this.updateUser(userData)
        }
    } catch(e) { console.error(e) }
  }
})