<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { store } from '../store'
import { Search, Plus, X, MessageCircle, Image as ImageIcon } from 'lucide-vue-next'

const router = useRouter()
const searchQuery = ref('')
const isModalOpen = ref(false)
const selectedItem = ref(null)

// 图片相关状态
const imageFiles = ref([]) // 改为数组
const previewUrls = ref([])

const form = ref({
  title: '',
  price: '',
  category: '生活用品',
  description: ''
})

onMounted(() => {
  store.fetchItems()
})

const filteredItems = computed(() => {
  return store.state.items.filter(item => 
    item.title.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 处理文件选择 (支持多选)
const handleFileChange = (event) => {
  const files = Array.from(event.target.files)
  
  // 检查数量限制
  if (imageFiles.value.length + files.length > 9) {
    alert('最多只能上传 9 张图片')
    return
  }

  files.forEach(file => {
    imageFiles.value.push(file)
    previewUrls.value.push(URL.createObjectURL(file))
  })
}

// 移除单张图片
const removeImage = (index) => {
    imageFiles.value.splice(index, 1)
    URL.revokeObjectURL(previewUrls.value[index]) // 释放内存
    previewUrls.value.splice(index, 1)
}

const handlePost = async () => {
  if (!form.value.title || !form.value.price) return
  
  const result = await store.postItem({
    title: form.value.title,
    price: Number(form.value.price),
    category: form.value.category,
    description: form.value.description,
    imageFiles: imageFiles.value // 传递文件数组
  })

  if (result.success) {
    isModalOpen.value = false
    // 重置表单
    form.value = { title: '', price: '', category: '生活用品', description: '' }
    imageFiles.value = []
    previewUrls.value = []
    if (result.message) {
      alert(result.message) 
    }
  } else {
    alert('发布失败：' + result.message)
  }
}

const openDetail = (item) => {
  selectedItem.value = item
}

const contactSeller = () => {
  if (!store.state.currentUser) {
    alert('请先登录')
    router.push('/login')
    return
  }
  if (selectedItem.value && selectedItem.value.sellerId) {
    // 存储卖家信息到 store
    store.setActiveChatUser({
      id: selectedItem.value.sellerId,
      name: `商家`,
      avatar: `https://picsum.photos/seed/${selectedItem.value.sellerId}/150/150`
    })
    router.push('/chat')
  }
}
</script>

<template>
  <div class="market-container">
    <div class="page-header">
      <h1 class="page-title">二手市场</h1>
      <div class="header-right">
        <div class="search-box">
          <Search class="search-icon" size="20" />
          <input v-model="searchQuery" type="text" placeholder="搜索好物..." class="search-input" />
        </div>
        <button @click="isModalOpen = true" class="primary-btn">
          <Plus size="20" stroke-width="2.5" /> 发布闲置
        </button>
      </div>
    </div>

    <div class="goods-grid">
      <div 
        v-for="item in filteredItems" 
        :key="item.id" 
        class="goods-card"
        @click="openDetail(item)"
      >
        <div class="img-wrapper">
          <img :src="item.images[0]" class="goods-img" />
          <div v-if="item.status === '已售'" class="sold-overlay">已售</div>
          <div v-if="item.images.length > 1" class="multi-tag">{{ item.images.length }}图</div>
        </div>
        <div class="card-body">
          <h3 class="goods-title">{{ item.title }}</h3>
          <p class="goods-desc">{{ item.description || '暂无描述' }}</p>
          <div class="card-footer">
            <span class="price">¥{{ item.price }}</span>
            <span class="category-tag">{{ item.category }}</span>
          </div>
        </div>
      </div>
    </div>

    <Transition name="modal">
      <div v-if="isModalOpen" class="modal-overlay" @click.self="isModalOpen = false">
        <div class="modal-container">
          <div class="modal-header">
            <h3>发布闲置宝贝</h3>
            <button @click="isModalOpen = false" class="close-btn"><X size="22" /></button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>商品名称 <span class="required">*</span></label>
              <input v-model="form.title" placeholder="例如：95新 iPad Air 5" />
            </div>
            
            <div class="form-group">
              <label>实拍图片 (已选 {{ imageFiles.length }}/9)</label>
              
              <div class="preview-grid" v-if="previewUrls.length > 0">
                  <div v-for="(url, index) in previewUrls" :key="index" class="preview-item">
                      <img :src="url" />
                      <button class="remove-img-btn" @click.stop="removeImage(index)">×</button>
                  </div>
                  <div v-if="previewUrls.length < 9" class="add-more-btn" @click="$refs.fileInput.click()">
                      <Plus size="20" />
                  </div>
              </div>

              <div v-else class="upload-box" @click="$refs.fileInput.click()">
                <div class="upload-placeholder">
                  <ImageIcon size="32" class="upload-icon"/>
                  <span>点击上传图片 (最多9张)</span>
                </div>
              </div>
              
              <input 
                  type="file" 
                  ref="fileInput"
                  accept="image/*" 
                  multiple 
                  @change="handleFileChange" 
                  class="hidden-input"
              />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>价格 (¥) <span class="required">*</span></label>
                <input v-model="form.price" type="number" placeholder="0.00" />
              </div>
              <div class="form-group">
                <label>分类</label>
                <select v-model="form.category">
                  <option>生活用品</option>
                  <option>数码电子</option>
                  <option>书籍教材</option>
                  <option>美妆护肤</option>
                  <option>交通工具</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <div class="label-row">
                <label>商品描述</label>
              </div>
              <textarea v-model="form.description" rows="4" placeholder="描述一下宝贝的新旧程度、入手渠道等..."></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="isModalOpen = false" class="cancel-btn">取消</button>
            <button @click="handlePost" class="primary-btn confirm-btn" :disabled="!form.title">确认发布</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="modal">
      <div v-if="selectedItem" class="modal-overlay" @click.self="selectedItem = null">
        <div class="modal-container detail-modal">
          <div class="modal-header">
            <h3>商品详情</h3>
            <button @click="selectedItem = null" class="close-btn"><X size="22" /></button>
          </div>
          
          <div class="modal-body no-padding">
            <div class="detail-gallery">
              <img v-for="(img, idx) in selectedItem.images" :key="idx" :src="img" class="detail-img" />
            </div>

            <div class="detail-content">
              <div class="detail-title-row">
                <h2 class="detail-title">{{ selectedItem.title }}</h2>
                <span class="detail-price">¥{{ selectedItem.price }}</span>
              </div>
              
              <div class="detail-tags">
                <span class="category-tag">{{ selectedItem.category }}</span>
                <span v-if="selectedItem.status === '已售'" class="status-tag sold">已售</span>
                <span v-else class="status-tag active">在售</span>
              </div>

              <div class="detail-desc-box">
                <label>商品描述</label>
                <p class="detail-text">{{ selectedItem.description || '暂无描述' }}</p>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button @click="contactSeller" class="primary-btn full-width">
              <MessageCircle size="18" /> 联系卖家
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; flex-wrap: wrap; gap: 16px; position: relative; z-index: 20; }
.page-title { font-size: 2rem; font-weight: 800; color: var(--text-main); letter-spacing: -0.5px; }
.header-right { display: flex; gap: 16px; align-items: center; }
.search-box { position: relative; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--text-secondary); }
.search-input { width: 260px; padding-left: 44px; border-radius: 24px; border: 1px solid var(--border); transition: all 0.3s; box-shadow: var(--shadow-sm); }
.search-input:focus { width: 320px; border-color: var(--primary); box-shadow: var(--shadow-blue); }
.goods-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; }
.goods-card { background: var(--bg-card); border-radius: 20px; overflow: hidden; border: 1px solid var(--border); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; box-shadow: var(--shadow-sm); cursor: pointer; }
.goods-card:hover { transform: translateY(-6px); box-shadow: var(--shadow-md), 0 0 0 1px var(--primary) inset; border-color: var(--primary); }
.img-wrapper { height: 200px; position: relative; background: #eee; }
.goods-img { width: 100%; height: 100%; object-fit: cover; }
.sold-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.6); color: white; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: bold; letter-spacing: 2px; backdrop-filter: blur(2px); }
.multi-tag { position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.6); color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; }
.card-body { padding: 20px; }
.goods-title { font-weight: 700; margin-bottom: 8px; font-size: 1.15rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-main); }
.goods-desc { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 16px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 2.8em; line-height: 1.4; }
.card-footer { display: flex; justify-content: space-between; align-items: center; }
.price { color: var(--primary); font-weight: 800; font-size: 1.3rem; }
.category-tag { background: var(--bg-body); color: var(--text-secondary); padding: 6px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; }
.modal-overlay { position: fixed; inset: 0; z-index: 9999; background: var(--bg-modal-overlay); backdrop-filter: blur(6px); display: flex; justify-content: center; align-items: center; padding: 24px; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 520px; border-radius: 24px; box-shadow: var(--shadow-lg); display: flex; flex-direction: column; border: 1px solid var(--border); overflow: hidden; max-height: 90vh; }
.modal-header { padding: 24px 28px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg-body); }
.modal-header h3 { font-size: 1.35rem; font-weight: 700; color: var(--text-main); }
.close-btn { background: transparent; color: var(--text-secondary); padding: 8px; border-radius: 50%; transition: 0.2s; }
.close-btn:hover { background: var(--border); color: var(--text-main); }
.modal-body { padding: 28px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
.modal-body.no-padding { padding: 0; gap: 0; }
.form-group label { display: block; margin-bottom: 8px; font-size: 0.95rem; font-weight: 600; color: var(--text-main); }
.required { color: #ef4444; margin-left: 4px; }
.form-row { display: flex; gap: 20px; }
.form-row .form-group { flex: 1; }
.label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.modal-footer { padding: 20px 28px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 16px; background: var(--bg-body); }
.cancel-btn { background: transparent; padding: 0.8rem 1.6rem; font-weight: 600; color: var(--text-secondary); border-radius: 12px; }
.cancel-btn:hover { color: var(--text-main); background: var(--border); }

/* 详情页图片列表 */
.detail-gallery { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: 10px; padding: 10px; background: #eee; }
.detail-img { width: 100%; height: 300px; object-fit: contain; scroll-snap-align: center; flex-shrink: 0; background: #fff; }

.detail-content { padding: 28px; display: flex; flex-direction: column; gap: 16px; }
.detail-title-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.detail-title { font-size: 1.5rem; font-weight: 800; color: var(--text-main); line-height: 1.3; }
.detail-price { font-size: 1.8rem; font-weight: 800; color: var(--primary); }
.detail-tags { display: flex; gap: 10px; margin-bottom: 8px; }
.status-tag { padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
.status-tag.sold { background: #fee2e2; color: #b91c1c; }
.status-tag.active { background: #dcfce7; color: #15803d; }
.detail-desc-box label { display: block; font-size: 0.9rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 8px; }
.detail-text { font-size: 1rem; color: var(--text-main); line-height: 1.7; white-space: pre-wrap; }
.full-width { width: 100%; }

/* --- 上传图片样式 --- */
.upload-box {
  border: 2px dashed var(--border);
  border-radius: 12px;
  min-height: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  background-color: var(--bg-input);
  transition: all 0.2s;
}
.upload-box:hover { border-color: var(--primary); background-color: var(--bg-card); }
.hidden-input { display: none; }
.upload-placeholder { display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--text-secondary); }

.preview-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 10px; margin-top: 10px; }
.preview-item { position: relative; width: 100%; aspect-ratio: 1; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
.preview-item img { width: 100%; height: 100%; object-fit: cover; }
.remove-img-btn { position: absolute; top: 2px; right: 2px; background: rgba(0,0,0,0.5); color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; justify-content: center; align-items: center; cursor: pointer; border: none; font-size: 14px; }
.add-more-btn { border: 2px dashed var(--border); border-radius: 8px; display: flex; justify-content: center; align-items: center; cursor: pointer; color: var(--text-secondary); aspect-ratio: 1; }
.add-more-btn:hover { border-color: var(--primary); color: var(--primary); }
</style>