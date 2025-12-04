import { reactive } from 'vue'

// 模拟初始数据
const MOCK_USER = {
  id: 'u1',
  name: '陈同学',
  avatar: 'https://picsum.photos/seed/alex/150/150',
  studentId: '2023001',
  creditScore: 95,
  balance: 150.00
}

const MOCK_USERS = {
  'u1': MOCK_USER,
  'u2': { id: 'u2', name: '吴学姐', avatar: 'https://picsum.photos/seed/sarah/150/150', studentId: '2023002', creditScore: 88, balance: 45.00 },
  'u3': { id: 'u3', name: '李同学', avatar: 'https://picsum.photos/seed/mike/150/150', studentId: '2023003', creditScore: 92, balance: 200.00 },
}

const MOCK_ITEMS = [
  {
    id: 'i1', sellerId: 'u2', title: '微积分第九版课本', price: 25, category: '书籍',
    description: '用了一个学期，保护得很好，书内没有乱画。',
    images: ['https://image.pollinations.ai/prompt/calculus%20textbook%20book%20cover?width=400&height=300&nologo=true'], status: '在售', createdAt: Date.now() - 86400000
  },
  {
    id: 'i2', sellerId: 'u3', title: '罗技无线鼠标', price: 15, category: '数码',
    description: '几乎全新，买来没怎么用过。',
    images: ['https://image.pollinations.ai/prompt/logitech%20computer%20mouse?width=400&height=300&nologo=true'], status: '在售', createdAt: Date.now() - 172800000
  },
  // 补回这条数据，这样你的个人中心就有东西了
  {
    id: 'i3', sellerId: 'u1', title: '校园代步自行车', price: 80, category: '交通',
    description: '蓝色山地车，刹车有点松，但骑行没问题。',
    images: ['https://image.pollinations.ai/prompt/blue%20mountain%20bicycle?width=400&height=300&nologo=true'], status: '已售', createdAt: Date.now() - 604800000
  }
]

const MOCK_TASKS = [
  {
    id: 't1', publisherId: 'u2', title: '北门取快递', bounty: 5, location: '北门 -> A栋宿舍',
    notes: '快递很小，就一个文件袋。', status: '待接单', createdAt: Date.now() - 3600000
  },
  {
    id: 't2', publisherId: 'u3', title: '代买星巴克咖啡', bounty: 8, location: '图书馆3楼',
    notes: '冰拿铁，大杯。咖啡钱和跑腿费一起给。', status: '进行中', runnerId: 'u1', createdAt: Date.now() - 7200000
  }
]

const MOCK_MESSAGES = [
  { id: 'm1', senderId: 'u2', receiverId: 'u1', text: '你好，自行车还在吗？', timestamp: Date.now() - 6000000, read: true },
  { id: 'm2', senderId: 'u1', receiverId: 'u2', text: '不好意思，刚卖掉了！', timestamp: Date.now() - 5000000, read: true },
]

export const store = reactive({
  state: {
    currentUser: null, 
    items: [...MOCK_ITEMS],
    tasks: [...MOCK_TASKS],
    messages: [...MOCK_MESSAGES],
    users: MOCK_USERS
  },

  login(studentId) {
    const user = Object.values(this.state.users).find(u => u.studentId === studentId)
    if (user) {
      this.state.currentUser = user
    } else {
      const newUser = {
        id: 'u' + Date.now(),
        name: `同学 ${studentId}`,
        studentId,
        avatar: `https://picsum.photos/seed/${studentId}/150/150`,
        creditScore: 100,
        balance: 0
      }
      this.state.users[newUser.id] = newUser
      this.state.currentUser = newUser
    }
    return true
  },

  logout() {
    this.state.currentUser = null
  },

  postItem(item) {
    if (!this.state.currentUser) return
    const newItem = {
      ...item,
      id: `i${Date.now()}`,
      sellerId: this.state.currentUser.id,
      createdAt: Date.now(),
      status: '在售',
    }
    this.state.items.unshift(newItem)
  },

  postTask(task) {
    if (!this.state.currentUser) return
    const newTask = {
      ...task,
      id: `t${Date.now()}`,
      publisherId: this.state.currentUser.id,
      createdAt: Date.now(),
      status: '待接单',
    }
    this.state.tasks.unshift(newTask)
  },

  grabTask(taskId) {
    if (!this.state.currentUser) return
    const task = this.state.tasks.find(t => t.id === taskId)
    if (task) {
      task.status = '进行中'
      task.runnerId = this.state.currentUser.id
    }
  },

  sendMessage(receiverId, text) {
    if (!this.state.currentUser) return
    this.state.messages.push({
      id: `m${Date.now()}`,
      senderId: this.state.currentUser.id,
      receiverId,
      text,
      timestamp: Date.now(),
      read: false
    })
  },
  
  getUser(id) {
    return this.state.users[id]
  }
})