<script setup>
import { ref, onMounted } from 'vue'
import { API_BASE_URL } from '../config.js'

const message = ref('loading...')
const items = ref([])
const echoResponse = ref(null)

async function load() {
  try {
    const r = await fetch(`${API_BASE_URL}/api/hello`)
    const j = await r.json()
    message.value = j.message

    const r2 = await fetch(`${API_BASE_URL}/api/items`)
    const j2 = await r2.json()
    items.value = j2.items || []
  } catch (e) {
    message.value = 'Failed to fetch from backend'
  }
}

async function doEcho() {
  const payload = { time: Date.now(), note: 'hello from frontend' }
  const r = await fetch(`${API_BASE_URL}/api/echo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  echoResponse.value = await r.json()
}

onMounted(load)
</script>

<template>
  <div>
    <h1>Marketplace Admin (HTML Only)</h1>

    <section>
      <h2>Create User</h2>
      <p>
        <router-link to="/register">Go to Register Page</router-link> | 
        <router-link to="/preferences">Set Preferences</router-link>
      </p>
      <!-- <form :action="`${API_BASE_URL}/user/register`" method="POST">
        <div>
          <label>Name: <input type="text" name="name" required /></label>
        </div>
        <div>
          <label>Email: <input type="email" name="email" /></label>
        </div>
        <div>
          <label>Password: <input type="text" name="pswd" /></label>
        </div>
        <button type="submit">Create User</button>
      </form> -->
    </section>

    <hr />

    <section>
      <h2>Create Good</h2>
      <form :action="`${API_BASE_URL}/goods`" method="POST">
        <div>
          <label>Name: <input type="text" name="name" required /></label>
        </div>
        <div>
          <label>Seller ID: <input type="number" name="seller_id" required /></label>
        </div>
        <!-- <div>
          <label>Original Num: <input type="number" name="ori_num" required /></label>
        </div> -->
        <div>
          <label>Current Num: <input type="number" name="num" required /></label>
        </div>
        <div>
          <label>Value: <input type="number" step="0.01" name="value" required /></label>
        </div>
        <div>
          <label>Description: <textarea name="description"></textarea></label>
        </div>
        <div>
          <label>Labels (comma separated IDs): <input type="text" name="labels" placeholder="1, 4" /></label>
        </div>
        <button type="submit">Create Good</button>
      </form>
    </section>

    <hr />

    <section>
      <h2>Create Order</h2>
      <form :action="`${API_BASE_URL}/orders`" method="POST">
        <div>
          <label>Buyer ID: <input type="number" name="buyer_id" required /></label>
        </div>
        <div>
          <label>Goods ID: <input type="number" name="goods_id" required /></label>
        </div>
        <div>
          <label>Quantity: <input type="number" name="num" required /></label>
        </div>
        <button type="submit">Create Order</button>
      </form>
    </section>

    <hr />

    <section>
      <h2>Quick Links</h2>
      <ul>
        <li><a :href="`${API_BASE_URL}/labels`" target="_blank">View All Labels</a></li>
        <li><a :href="`${API_BASE_URL}/goods/random?num=5`" target="_blank">Get 5 Random Goods</a></li>
      </ul>
    </section>
  </div>
</template>
