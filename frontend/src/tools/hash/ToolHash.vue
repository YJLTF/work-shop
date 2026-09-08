<script setup>
import { ref, watch } from 'vue'
import { api } from '../../api'
import CopyButton from '../../components/CopyButton.vue'

const mode = ref('text')
const text = ref('hello workshop')
const textResult = ref(null)
const fileResult = ref(null)
const busy = ref(false)
const error = ref('')
const fileInput = ref(null)

const ALGOS = [
  { id: 'md5', label: 'MD5' },
  { id: 'sha1', label: 'SHA-1' },
  { id: 'sha256', label: 'SHA-256' },
  { id: 'sha512', label: 'SHA-512' },
]

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

async function hashText() {
  if (!text.value) {
    textResult.value = null
    return
  }
  busy.value = true
  error.value = ''
  try {
    textResult.value = await api.post('/tools/hash/text', { text: text.value })
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

async function hashFile(file) {
  if (!file) return
  busy.value = true
  error.value = ''
  fileResult.value = null
  try {
    const form = new FormData()
    form.append('file', file)
    fileResult.value = await api.postForm('/tools/hash/file', form)
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

function pickFile() {
  fileInput.value?.click()
}

function onDrop(event) {
  hashFile(event.dataTransfer.files?.[0])
}

watch(text, () => {
  clearTimeout(hashText._t)
  hashText._t = setTimeout(hashText, 250)
})
hashText()
</script>

<template>
  <div class="stack">
    <div class="tabs" role="tablist">
      <button class="tab" :class="{ active: mode === 'text' }" role="tab" :aria-selected="mode === 'text'" @click="mode = 'text'">文本</button>
      <button class="tab" :class="{ active: mode === 'file' }" role="tab" :aria-selected="mode === 'file'" @click="mode = 'file'">文件</button>
    </div>

    <p v-if="error" class="error-text">{{ error }}</p>

    <section v-show="mode === 'text'" class="panel">
      <span class="label">输入文本</span>
      <textarea v-model="text" class="field" rows="6" placeholder="输入要计算摘要的文本" spellcheck="false"></textarea>
    </section>

    <section
      v-show="mode === 'file'"
      class="panel dropzone"
      :class="{ busy }"
      role="button"
      tabindex="0"
      @click="pickFile"
      @keydown.enter="pickFile"
      @dragover.prevent
      @drop.prevent="onDrop"
    >
      <input ref="fileInput" type="file" hidden @change="hashFile($event.target.files[0])" />
      <p class="dz-title">{{ busy ? '正在计算…' : '拖入文件，或点击选择' }}</p>
      <p class="dz-hint">文件分块流式读取，不会完整载入内存</p>
    </section>

    <section v-if="mode === 'text' && textResult" class="panel">
      <div class="pane-head">
        <span class="label">摘要（{{ textResult.length }} 字节）</span>
      </div>
      <ul class="digest-list">
        <li v-for="algo in ALGOS" :key="algo.id" class="digest">
          <span class="algo">{{ algo.label }}</span>
          <code class="mono value">{{ textResult.digests[algo.id] }}</code>
          <CopyButton :text="textResult.digests[algo.id]" />
        </li>
      </ul>
    </section>

    <section v-if="mode === 'file' && fileResult" class="panel">
      <div class="pane-head">
        <span class="label">{{ fileResult.filename }}（{{ formatSize(fileResult.size) }}）</span>
      </div>
      <ul class="digest-list">
        <li v-for="algo in ALGOS" :key="algo.id" class="digest">
          <span class="algo">{{ algo.label }}</span>
          <code class="mono value">{{ fileResult.digests[algo.id] }}</code>
          <CopyButton :text="fileResult.digests[algo.id]" />
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tabs {
  display: inline-flex;
  gap: 4px;
  align-self: flex-start;
  padding: 4px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 11px;
}

.tab {
  padding: 7px 22px;
  border-radius: 8px;
  font-size: 13.5px;
  font-weight: 550;
  color: var(--ink-dim);
  transition: all 0.15s ease;
}

.tab:hover {
  color: var(--ink);
}

.tab.active {
  background: var(--accent);
  color: var(--on-accent);
}

.dropzone {
  border-style: dashed;
  border-width: 1.5px;
  border-color: var(--line-strong);
  text-align: center;
  padding: 44px 20px;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.dropzone:hover,
.dropzone:focus-visible {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.dz-title {
  margin: 0;
  font-weight: 600;
  font-size: 15px;
}

.dz-hint {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--ink-faint);
}

.pane-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.digest-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.digest {
  display: grid;
  grid-template-columns: 76px 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 9px 12px;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
}

.algo {
  font-size: 12.5px;
  font-weight: 650;
  color: var(--ink-dim);
}

.value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
