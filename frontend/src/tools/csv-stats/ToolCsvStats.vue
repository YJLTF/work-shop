<script setup>
import { ref } from 'vue'
import { api } from '../../api'

const result = ref(null)
const busy = ref(false)
const error = ref('')
const fileInput = ref(null)
const dragged = ref(false)

function formatNumber(n) {
  if (n === null || n === undefined) return '—'
  if (typeof n !== 'number') return n
  return Math.abs(n) >= 1000 ? n.toLocaleString('zh-CN') : String(n)
}

async function analyze(file) {
  if (!file) return
  busy.value = true
  error.value = ''
  result.value = null
  try {
    const form = new FormData()
    form.append('file', file)
    result.value = await api.postForm('/tools/csv-stats/stats', form)
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
  dragged.value = false
  analyze(event.dataTransfer.files?.[0])
}

function statSummary(column) {
  const s = column.stats || {}
  if (column.type === 'number') {
    return `最小 ${formatNumber(s.min)} · 最大 ${formatNumber(s.max)} · 均值 ${formatNumber(s.mean)} · 中位数 ${formatNumber(s.median)} · 标准差 ${formatNumber(s.stdev)}`
  }
  return `不同值 ${formatNumber(s.distinct)} · 最常见 ${s.top ?? '—'}`
}
</script>

<template>
  <div class="stack">
    <section
      v-if="!result"
      class="panel dropzone"
      :class="{ busy, dragged }"
      role="button"
      tabindex="0"
      @click="pickFile"
      @keydown.enter="pickFile"
      @dragover.prevent="dragged = true"
      @dragleave="dragged = false"
      @drop.prevent="onDrop"
    >
      <input ref="fileInput" type="file" accept=".csv,.tsv,.txt" hidden @change="analyze($event.target.files[0])" />
      <p class="dz-title">{{ busy ? '正在分析…' : '拖入 CSV 文件，或点击选择' }}</p>
      <p class="dz-hint">支持逗号 / 分号 / 制表符分隔，UTF-8 或 GBK 编码，单文件上限 20 万行</p>
    </section>

    <p v-if="error" class="error-text">{{ error }}</p>

    <template v-if="result">
      <div class="summary">
        <div class="stat panel">
          <span class="stat-num mono">{{ result.rows.toLocaleString('zh-CN') }}</span>
          <span class="stat-label">数据行</span>
        </div>
        <div class="stat panel">
          <span class="stat-num mono">{{ result.cols }}</span>
          <span class="stat-label">列</span>
        </div>
        <div class="stat panel wide">
          <span class="stat-file">{{ result.filename }}</span>
          <span class="stat-label">
            <button class="btn" @click="result = null">← 分析其他文件</button>
          </span>
        </div>
      </div>

      <section class="panel">
        <span class="label">列摘要</span>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>列名</th>
                <th>类型</th>
                <th>缺失</th>
                <th>统计</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="col in result.columns" :key="col.name">
                <td class="col-name">{{ col.name }}</td>
                <td>
                  <span class="type" :class="col.type">{{ col.type === 'number' ? '数值' : '文本' }}</span>
                </td>
                <td class="mono">{{ col.missing }}</td>
                <td class="stat-cell">{{ statSummary(col) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel">
        <span class="label">数据预览（前 {{ result.preview.length }} 行）</span>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th v-for="(name, i) in result.columns.map((c) => c.name)" :key="i">{{ name }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, r) in result.preview" :key="r">
                <td v-for="(cell, c) in row" :key="c" class="mono">{{ cell }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dropzone {
  border-style: dashed;
  border-width: 1.5px;
  border-color: var(--line-strong);
  text-align: center;
  padding: 60px 20px;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.dropzone:hover,
.dropzone:focus-visible,
.dropzone.dragged {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.dz-title {
  margin: 0;
  font-weight: 600;
  font-size: 15.5px;
}

.dz-hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--ink-faint);
}

.summary {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  gap: 12px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 18px;
}

.stat-num {
  font-size: 26px;
  font-weight: 650;
  color: var(--accent);
}

.stat-label {
  font-size: 12.5px;
  color: var(--ink-dim);
}

.stat.wide {
  justify-content: space-between;
}

.stat-file {
  font-family: var(--font-mono);
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat.wide .stat-label {
  text-align: right;
}

.type {
  font-size: 12px;
  padding: 2px 9px;
  border-radius: 999px;
  border: 1px solid;
}

.type.number {
  color: var(--cat-data);
  border-color: color-mix(in srgb, var(--cat-data) 40%, transparent);
  background: color-mix(in srgb, var(--cat-data) 10%, transparent);
}

.type.text {
  color: var(--ink-dim);
  border-color: var(--line-strong);
}

.col-name {
  font-weight: 600;
}

.stat-cell {
  color: var(--ink-dim);
  font-size: 13px;
}

.table-wrap {
  overflow-x: auto;
}

@media (max-width: 760px) {
  .summary {
    grid-template-columns: 1fr;
  }
}
</style>
