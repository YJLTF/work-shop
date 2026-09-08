<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import CopyButton from '../../components/CopyButton.vue'

const now = ref(Date.now())
let timer = null
onMounted(() => (timer = setInterval(() => (now.value = Date.now()), 1000)))
onBeforeUnmount(() => clearInterval(timer))

const nowSec = computed(() => Math.floor(now.value / 1000))

/* 时间戳 → 日期 */
const tsInput = ref('')
const tsResult = ref(null)
const tsError = ref('')

function toRelative(ms) {
  const diff = ms - Date.now()
  const abs = Math.abs(diff)
  const units = [
    [86400000, '天'],
    [3600000, '小时'],
    [60000, '分钟'],
    [1000, '秒'],
  ]
  for (const [size, unit] of units) {
    if (abs >= size) {
      const n = Math.round(abs / size)
      return diff > 0 ? `${n} ${unit}后` : `${n} ${unit}前`
    }
  }
  return '刚刚'
}

function parseTs() {
  tsError.value = ''
  tsResult.value = null
  const raw = tsInput.value.trim()
  if (!raw) {
    tsError.value = '请输入时间戳。'
    return
  }
  if (!/^-?\d+$/.test(raw)) {
    tsError.value = '时间戳应为纯数字（秒为 10 位，毫秒为 13 位）。'
    return
  }
  let ms = Number(raw)
  if (String(Math.abs(ms)).length <= 10) ms *= 1000
  const date = new Date(ms)
  if (Number.isNaN(date.getTime())) {
    tsError.value = '数值超出可表示的时间范围。'
    return
  }
  tsResult.value = {
    ms,
    local: date.toLocaleString('zh-CN', { hour12: false }),
    iso: date.toISOString(),
    weekday: date.toLocaleDateString('zh-CN', { weekday: 'long' }),
    relative: toRelative(ms),
  }
}

/* 日期 → 时间戳 */
const dateInput = ref('')
const dateResult = ref(null)

function toDateInputValue(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}
dateInput.value = toDateInputValue(new Date())

function parseDate() {
  dateResult.value = null
  if (!dateInput.value) return
  const date = new Date(dateInput.value)
  if (Number.isNaN(date.getTime())) return
  dateResult.value = {
    sec: Math.floor(date.getTime() / 1000),
    ms: date.getTime(),
    iso: date.toISOString(),
  }
}
parseDate()
</script>

<template>
  <div class="stack">
    <section class="panel">
      <div class="pane-head">
        <span class="label">当前时间</span>
        <span class="tz mono">本地时区 {{ Intl.DateTimeFormat().resolvedOptions().timeZone }}</span>
      </div>
      <div class="now-row">
        <div class="now-block">
          <span class="now-value mono">{{ nowSec }}</span>
          <span class="now-unit">秒</span>
          <CopyButton :text="String(nowSec)" label="复制" />
        </div>
        <div class="now-block">
          <span class="now-value mono">{{ now }}</span>
          <span class="now-unit">毫秒</span>
          <CopyButton :text="String(now)" label="复制" />
        </div>
      </div>
      <p class="now-date">{{ new Date(now).toLocaleString('zh-CN', { hour12: false }) }}</p>
    </section>

    <div class="columns">
      <section class="panel">
        <span class="label">时间戳 → 日期</span>
        <div class="row">
          <input
            v-model="tsInput"
            class="field"
            placeholder="如 1735689600 或 1735689600000"
            spellcheck="false"
            @keyup.enter="parseTs"
          />
          <button class="btn primary" @click="parseTs">转换</button>
        </div>

        <p v-if="tsError" class="error-text">{{ tsError }}</p>

        <template v-if="tsResult">
          <dl class="result-list">
            <div class="result-item">
              <dt>本地时间</dt>
              <dd class="mono">{{ tsResult.local }}（{{ tsResult.weekday }}）</dd>
              <CopyButton :text="tsResult.local" />
            </div>
            <div class="result-item">
              <dt>ISO 8601</dt>
              <dd class="mono">{{ tsResult.iso }}</dd>
              <CopyButton :text="tsResult.iso" />
            </div>
            <div class="result-item">
              <dt>相对现在</dt>
              <dd>{{ tsResult.relative }}</dd>
            </div>
          </dl>
        </template>
      </section>

      <section class="panel">
        <span class="label">日期 → 时间戳</span>
        <div class="row">
          <input v-model="dateInput" type="datetime-local" step="1" class="field" />
          <button class="btn primary" @click="parseDate">转换</button>
        </div>

        <template v-if="dateResult">
          <dl class="result-list">
            <div class="result-item">
              <dt>秒</dt>
              <dd class="mono">{{ dateResult.sec }}</dd>
              <CopyButton :text="String(dateResult.sec)" />
            </div>
            <div class="result-item">
              <dt>毫秒</dt>
              <dd class="mono">{{ dateResult.ms }}</dd>
              <CopyButton :text="String(dateResult.ms)" />
            </div>
            <div class="result-item">
              <dt>UTC</dt>
              <dd class="mono">{{ dateResult.iso }}</dd>
            </div>
          </dl>
        </template>
      </section>
    </div>
  </div>
</template>

<style scoped>
.stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pane-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.tz {
  font-size: 12px;
  color: var(--ink-faint);
}

.now-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.now-block {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 13px 15px;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
}

.now-value {
  font-size: 20px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.now-unit {
  color: var(--ink-faint);
  font-size: 12.5px;
  flex-shrink: 0;
}

.now-block :last-child {
  margin-left: auto;
}

.now-date {
  margin: 12px 2px 0;
  color: var(--ink-dim);
  font-size: 13.5px;
}

.columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.row {
  display: flex;
  gap: 10px;
}

.row .field {
  flex: 1;
}

.result-list {
  margin: 16px 0 0;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.result-item {
  display: grid;
  grid-template-columns: 76px 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
}

.result-item dt {
  font-size: 12.5px;
  color: var(--ink-dim);
}

.result-item dd {
  margin: 0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .columns,
  .now-row {
    grid-template-columns: 1fr;
  }
}
</style>
