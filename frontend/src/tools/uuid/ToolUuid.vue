<script setup>
import { computed, ref } from 'vue'
import CopyButton from '../../components/CopyButton.vue'

const count = ref(5)
const upper = ref(false)
const noDash = ref(false)
const braces = ref(false)
const list = ref([])

function newUuid() {
  if (crypto.randomUUID) return crypto.randomUUID()
  // 兜底实现（旧内核）
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

function generate() {
  const n = Math.min(Math.max(count.value || 1, 1), 500)
  count.value = n
  list.value = Array.from({ length: n }, () => {
    let id = newUuid()
    if (noDash.value) id = id.replaceAll('-', '')
    if (upper.value) id = id.toUpperCase()
    if (braces.value) id = `{${id}}`
    return id
  })
}
generate()

const joined = computed(() => list.value.join('\n'))

async function copyOne(id) {
  try {
    await navigator.clipboard.writeText(id)
  } catch {
    /* 忽略剪贴板权限错误 */
  }
}
</script>

<template>
  <div class="layout">
    <section class="panel options">
      <span class="label">生成选项</span>

      <label class="opt">
        数量
        <input v-model.number="count" type="number" min="1" max="500" class="field" />
      </label>

      <label class="opt check">
        <input v-model="upper" type="checkbox" />
        大写字母
      </label>
      <label class="opt check">
        <input v-model="noDash" type="checkbox" />
        去除连字符
      </label>
      <label class="opt check">
        <input v-model="braces" type="checkbox" />
        花括号包裹
      </label>

      <button class="btn primary generate" @click="generate">生成 {{ Math.min(Math.max(count || 1, 1), 500) }} 个</button>
      <p class="note">基于浏览器加密安全随机数（UUID v4）。</p>
    </section>

    <section class="panel">
      <div class="pane-head">
        <span class="label">结果（{{ list.length }}）</span>
        <CopyButton :text="joined" :disabled="!list.length" label="复制全部" />
      </div>
      <ul class="uuid-list mono">
        <li v-for="id in list" :key="id" :title="`点击复制 ${id}`" @click="copyOne(id)">
          {{ id }}
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 16px;
  align-items: start;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 13px;
}

.opt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13.5px;
  color: var(--ink-dim);
}

.opt .field {
  width: 96px;
  padding: 7px 10px;
}

.opt.check {
  cursor: pointer;
  justify-content: flex-start;
}

.opt.check input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}

.generate {
  margin-top: 4px;
  justify-content: center;
}

.note {
  margin: 0;
  font-size: 12px;
  color: var(--ink-faint);
}

.pane-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.uuid-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 430px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.uuid-list li {
  padding: 7px 11px;
  border-radius: 7px;
  cursor: copy;
  transition: background 0.12s ease;
}

.uuid-list li:hover {
  background: var(--accent-soft);
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
