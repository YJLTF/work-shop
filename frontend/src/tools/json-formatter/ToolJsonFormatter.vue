<script setup>
import { computed, ref } from 'vue'
import CopyButton from '../../components/CopyButton.vue'

const input = ref(
  `{"name":"WorkShop","type":"toolbox","tools":6,"tags":["本地","高效"],"owner":{"role":"个人使用","offline":true}}`,
)
const indent = ref(2)
const output = ref('')
const error = ref('')

const stats = computed(() => ({
  chars: input.value.length,
  lines: input.value ? input.value.split('\n').length : 0,
}))

function locate(message) {
  const match = /position (\d+)/.exec(message)
  if (!match) return null
  const pos = Number(match[1])
  const before = input.value.slice(0, pos)
  const line = before.split('\n').length
  const col = pos - before.lastIndexOf('\n')
  return `第 ${line} 行，第 ${col} 列`
}

function transform(mode) {
  error.value = ''
  output.value = ''
  if (!input.value.trim()) {
    error.value = '请先输入 JSON 内容。'
    return
  }
  try {
    const parsed = JSON.parse(input.value)
    if (mode === 'minify') {
      output.value = JSON.stringify(parsed)
    } else {
      output.value = JSON.stringify(parsed, null, indent.value)
    }
  } catch (err) {
    const where = locate(err.message)
    error.value = `JSON 语法错误：${err.message}${where ? `（约${where}）` : ''}`
  }
}

function sample() {
  input.value = JSON.stringify(
    {
      project: 'WorkShop',
      version: '1.0.0',
      stack: { backend: 'Python / FastAPI', frontend: 'Vue 3' },
      features: ['工具卡片', '分类筛选', '模糊搜索'],
      offline: true,
    },
    null,
    2,
  )
}
</script>

<template>
  <div class="layout">
    <section class="panel">
      <div class="pane-head">
        <span class="label">输入 JSON</span>
        <div class="meta">
          <span class="mono dim">{{ stats.chars }} 字符 · {{ stats.lines }} 行</span>
          <button class="btn" @click="sample">示例</button>
        </div>
      </div>
      <textarea
        v-model="input"
        class="field"
        rows="10"
        placeholder='粘贴 JSON，例如 {"a": 1}'
        spellcheck="false"
      ></textarea>

      <div class="actions">
        <label class="indent">
          缩进
          <select v-model.number="indent" class="field select">
            <option :value="2">2 空格</option>
            <option :value="4">4 空格</option>
          </select>
        </label>
        <button class="btn primary" @click="transform('format')">格式化</button>
        <button class="btn" @click="transform('minify')">压缩</button>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
    </section>

    <section class="panel">
      <div class="pane-head">
        <span class="label">结果</span>
        <CopyButton v-if="output" :text="output" />
      </div>
      <pre v-if="output" class="result mono">{{ output }}</pre>
      <p v-else class="placeholder">点击「格式化」或「压缩」查看结果。</p>
    </section>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.pane-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.pane-head .label {
  margin: 0;
}

.meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dim {
  color: var(--ink-faint);
  font-size: 12px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}

.indent {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: var(--ink-dim);
}

.select {
  width: auto;
  padding: 7px 10px;
}

.result {
  margin: 0;
  max-height: 420px;
  overflow: auto;
  white-space: pre-wrap; /* 压缩后的单行长 JSON 允许折行，不再撑宽容器 */
  word-break: break-all;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 13px;
  line-height: 1.6;
}

.placeholder {
  margin: 0;
  padding: 34px 0;
  text-align: center;
  color: var(--ink-faint);
  font-size: 13.5px;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
