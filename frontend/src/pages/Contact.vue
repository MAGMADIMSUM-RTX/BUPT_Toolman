<script setup>
import { ref } from 'vue'
import { API_BASE_URL } from '../config.js'

const name = ref('')
const reply = ref(null)

async function submit() {
  const payload = { name: name.value }
  const r = await fetch(`${API_BASE_URL}/api/echo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  reply.value = await r.json()
}
</script>

<template>
  <div>
    <h2>Contact</h2>
    <p>Type your name and press submit — the backend will echo it back.</p>
    <input v-model="name" placeholder="Your name" />
    <button @click="submit">Submit</button>
    <pre v-if="reply">{{ reply }}</pre>
  </div>
</template>
