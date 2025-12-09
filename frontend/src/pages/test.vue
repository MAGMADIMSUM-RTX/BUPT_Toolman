<template>
  <div>
    <h2>Test Avatar</h2>
    <input v-model="userId" placeholder="User ID" type="number">
    <input type="file" ref="avatarFile" accept="image/*">
    <button @click="uploadAvatar">Upload Avatar</button>
    <button @click="getAvatar">Get Avatar</button>
    <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar">

    <h2>Test Good Images</h2>
    <input v-model="goodId" placeholder="Good ID" type="number">
    <input type="file" ref="goodFiles" multiple accept="image/*,video/*">
    <button @click="uploadGoodImages">Upload Good Images</button>
    <button @click="getFirstImage">Get First Image</button>
    <button @click="getAllImages">Get All Images</button>
    <div v-if="images.length">
      <img v-for="img in images" :key="img" :src="img" alt="Good Image">
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  setup() {
    const userId = ref('')
    const goodId = ref('')
    const avatarUrl = ref('')
    const images = ref([])
    const avatarFile = ref(null)
    const goodFiles = ref(null)

    const uploadAvatar = async () => {
      if (!userId.value || !avatarFile.value.files[0]) return
      const formData = new FormData()
      formData.append('type', 'avatar')
      formData.append('id', userId.value)
      formData.append('files', avatarFile.value.files[0])
      try {
        const res = await fetch('http://localhost:5000/upload', {
          method: 'POST',
          body: formData
        })
        const data = await res.json()
        if (res.ok) {
          alert('Upload successful')
          getAvatar() // 上传后显示
        } else {
          alert(data.error || 'Upload failed')
        }
      } catch (e) {
        console.error(e)
      }
    }

    const uploadGoodImages = async () => {
      if (!goodId.value || !goodFiles.value.files.length) return
      const formData = new FormData()
      formData.append('type', 'good')
      formData.append('id', goodId.value)
      for (let file of goodFiles.value.files) {
        formData.append('files', file)
      }
      try {
        const res = await fetch('http://localhost:5000/upload', {
          method: 'POST',
          body: formData
        })
        const data = await res.json()
        if (res.ok) {
          alert('Upload successful')
          getAllImages() // 上传后显示全部
        } else {
          alert(data.error || 'Upload failed')
        }
      } catch (e) {
        console.error(e)
      }
    }

    const getAvatar = async () => {
      if (!userId.value) return
      try {
        const res = await fetch(`http://localhost:5000/user/${userId.value}/avatar`)
        const data = await res.json()
        if (data.avatar_url) {
          avatarUrl.value = `http://localhost:5000${data.avatar_url}`
        } else {
          alert('Avatar not found')
        }
      } catch (e) {
        console.error(e)
      }
    }

    const getFirstImage = async () => {
      if (!goodId.value) return
      try {
        const res = await fetch(`http://localhost:5000/good/${goodId.value}/images?first=true`)
        const data = await res.json()
        if (data.image_url) {
          images.value = [`http://localhost:5000${data.image_url}`]
        } else {
          alert('No images found')
        }
      } catch (e) {
        console.error(e)
      }
    }

    const getAllImages = async () => {
      if (!goodId.value) return
      try {
        const res = await fetch(`http://localhost:5000/good/${goodId.value}/images`)
        const data = await res.json()
        if (data.image_urls) {
          images.value = data.image_urls.map(url => `http://localhost:5000${url}`)
        } else {
          alert('No images found')
        }
      } catch (e) {
        console.error(e)
      }
    }

    return {
      userId,
      goodId,
      avatarUrl,
      images,
      avatarFile,
      goodFiles,
      uploadAvatar,
      uploadGoodImages,
      getAvatar,
      getFirstImage,
      getAllImages
    }
  }
}
</script>

<style>
/* 空 */
</style>
