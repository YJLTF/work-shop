<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../../api'

const pattern = ref(String.raw`(\d{4})-(\d{2})-(\d{2})`)
const text = ref(
  '项目启动：2026-01-15\n版本发布：2026-03-08\n复盘会议：2026-06-30\n下次评审：2026-09-22',
)
const replace = ref(String.raw`[\2/\3/\1]`)
const flags = ref({ i: false, m: false, s: false, x: false })

const loading = ref(false)
const error = ref('')
const result = ref(null)

const activeFlags = computed(() => Object.entries(flags.value).filter(([, on]) => on).map(([f]) => f))

let timer = null
async function run() {
  if (!pattern.value || !text.value) {
    result.value = null
    error.value = ''
    return
  }
  loading.value = true
  error.value = ''
  try {
    result.value = await api.post('/tools/regex/match', {
      pattern: pattern.value,
      text: text.value,
      flags: activeFlags.value,
      replace: replace.value || null,
    })
  } catch (err) {
    error.value = err.message
    result.value = null
  } finally {
    loading.value = false
  }
}

watch([pattern, text, replace, activeFlags], () => {
  clearTimeout(timer)
  timer = setTimeout(run, 300)
}, { deep: true })
run()

/** 高亮预览：按匹配位置切片 */
const segments = computed(() => {
  if (!result.value) return []
  const list = []
  let cursor = 0
  for (const m of result.value.matches) {
    if (m.start > cursor) list.push({ text: text.value.slice(cursor, m.start), hit: false })
    list.push({ text: text.value.slice(m.start, m.end), hit: true })
    cursor = m.end
  }
  if (cursor < text.value.length) list.push({ text: text.value.slice(cursor), hit: false })
  return list
})
</script>

<template>
  <div class="layout">
    <section class="panel">
      <span class="label">正则表达式</span>
      <input v-model="pattern" class="field mono" placeholder="例如 (\w+)@(\w+)" spellcheck="false" />

      <div class="flags">
        <label v-for="(label, f) in { i: '忽略大小写', m: '多行 ^$', s: '点号匹配换行', x: '宽松模式' }" :key="f" class="flag">
          <input v-model="flags[f]" type="checkbox" />
          <code>{{ f }}</code>
          {{ label }}
        </label>
      </div>

      <span class="label mt">测试文本</span>
      <textarea v-model="text" class="field" rows="7" placeholder="粘贴要匹配的文本" spellcheck="false"></textarea>

      <span class="label mt">替换模板（可选，支持 $1、$2…）</span>
      <input v-model="replace" class="field mono" placeholder="留空则不执行替换" spellcheck="false" />

      <p v-if="error" class="error-text">{{ error }}</p>
    </section>

    <section class="panel">
      <div class="pane-head">
        <span class="label">
          匹配结果
          <span v-if="result" class="count mono">{{ result.count }} 处{{ result.truncated ? '（已截断）' : '' }}</span>
        </span>
        <span v-if="loading" class="loading-hint">计算中…</span>
      </div>

      <template v-if="result && result.count">
        <div class="preview mono" aria-label="高亮预览"><template v-for="(seg, i) in segments" :key="i"><mark v-if="seg.hit">{{ seg.text }}</mark><template v-else>{{ seg.text }}</template></template></div>

        <table v-if="result.matches.some((m) => m.groups.length || Object.keys(m.named).length)" class="data-table groups">
          <thead>
            <tr>
              <th>#</th>
              <th>匹配</th>
              <th>分组</th>
              <th>位置</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(m, i) in result.matches" :key="i">
              <td class="mono">{{ i + 1 }}</td>
              <td class="mono">{{ m.match }}</td>
              <td class="mono">{{ m.groups.filter(Boolean).join(', ') || Object.values(m.named).filter(Boolean).join(', ') || '—' }}</td>
              <td class="mono dim">{{ m.start }}–{{ m.end }}</td>
            </tr>
          </tbody>
        </table>

        <template v-if="result.replaced !== undefined">
          <span class="label mt">替换结果</span>
          <pre class="replaced mono">{{ result.replaced }}</pre>
        </template>
      </template>

      <p v-else-if="result" class="placeholder">没有匹配，调整表达式或文本再试。</p>
      <p v-else class="placeholder">输入正则与文本后自动开始匹配。</p>
    </section>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  gap: 16px;
  align-items: start;
}

.flags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  margin-top: 10px;
}

.flag {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: var(--ink-dim);
  cursor: pointer;
}

.flag input {
  accent-color: var(--accent);
}

.flag code {
  font-family: var(--font-mono);
  color: var(--accent);
}

.mt {
  margin-top: 16px;
}

.pane-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.count {
  margin-left: 8px;
  font-size: 12px;
  color: var(--accent);
}

.loading-hint {
  font-size: 12.5px;
  color: var(--ink-faint);
}

.preview {
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 13px;
  max-height: 180px;
  overflow: auto;
  white-space: pre-wrap;
  line-height: 1.7;
}

.preview mark {
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: 3px;
  padding: 0 2px;
  font-weight: 600;
}

.groups {
  margin-top: 16px;
}

.dim {
  color: var(--ink-faint);
}

.replaced {
  margin: 0;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 13px;
  max-height: 160px;
  overflow: auto;
  white-space: pre-wrap;
}

.placeholder {
  margin: 0;
  padding: 30px 0;
  text-align: center;
  color: var(--ink-faint);
  font-size: 13.5px;
}

@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
