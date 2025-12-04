<script setup>
import { ref, computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
// --- 修复点：这里改成 ./store ---
import { store } from './store' 
import { ShoppingBag, ClipboardList, MessageSquare, User, Moon, Sun } from 'lucide-vue-next'

const route = useRoute()
const isDark = ref(false)
const user = computed(() => store.state.currentUser)

const toggleDark = () => {
  isDark.value = !isDark.value
  if (isDark.value) document.documentElement.classList.add('dark')
  else document.documentElement.classList.remove('dark')
}
</script>

<template>
  <div class="app-wrapper">
    <header v-if="route.name !== 'login'" class="navbar">
      <div class="container navbar-inner">
        <div class="nav-left">
          <span class="logo">泥邮工具人</span>
          <nav class="nav-menu">
            <RouterLink to="/" class="nav-link"><ShoppingBag size="18"/> 二手市场</RouterLink>
            <RouterLink to="/tasks" class="nav-link"><ClipboardList size="18"/> 跑腿大厅</RouterLink>
            <RouterLink to="/chat" class="nav-link"><MessageSquare size="18"/> 消息</RouterLink>
            <RouterLink to="/profile" class="nav-link"><User size="18"/> 我的</RouterLink>
          </nav>
        </div>
        
        <div class="nav-right">
          <button @click="toggleDark" class="icon-btn">
            <Moon v-if="!isDark" size="20" />
            <Sun v-else size="20" />
          </button>
          <div v-if="user" class="user-profile">
            <img :src="user.avatar" class="avatar" />
            <span class="username">{{ user.name }}</span>
          </div>
        </div>
      </div>
    </header>

    <main class="main-body">
      <div class="container">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-wrapper { min-height: 100vh; display: flex; flex-direction: column; }

.navbar {
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border);
  height: 64px;
  position: sticky;
  top: 0;
  z-index: 50;
  transition: background-color 0.3s, border-color 0.3s;
}

.navbar-inner { height: 100%; display: flex; justify-content: space-between; align-items: center; }

.nav-left { display: flex; align-items: center; gap: 3rem; }
.logo { font-size: 1.25rem; font-weight: 800; color: var(--primary); letter-spacing: -0.5px; }

.nav-menu { display: flex; gap: 8px; }

/* --- 导航链接样式：去下划线 + 胶囊背景 --- */
.nav-link { 
  display: flex; align-items: center; gap: 6px; 
  color: var(--text-secondary); 
  font-size: 0.95rem; font-weight: 500;
  padding: 8px 16px; 
  border-radius: 20px; /* 胶囊圆角 */
  text-decoration: none; /* 核心：去掉下划线 */
  transition: all 0.2s ease;
  border: none; /* 确保无边框 */
}

.nav-link:hover { 
  color: var(--primary); 
  background-color: var(--bg-input); 
}

/* 选中状态：淡蓝色背景胶囊 */
.nav-link.router-link-active { 
  color: var(--primary); 
  background-color: rgba(59, 130, 246, 0.1); 
  font-weight: 600;
}

.nav-right { display: flex; align-items: center; gap: 1.5rem; }

.icon-btn { background: none; border: none; color: var(--text-secondary); padding: 8px; border-radius: 50%; transition: 0.2s; }
.icon-btn:hover { background-color: var(--bg-input); color: var(--text-main); }

.user-profile { display: flex; align-items: center; gap: 10px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 1px solid var(--border); }
.username { font-size: 0.9rem; font-weight: 600; color: var(--text-main); }

.main-body { flex: 1; padding: 2rem 0; }
</style>