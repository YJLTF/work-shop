<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { notifyConnectionLost } from '../../api'

const ENCODINGS = [
  { value: 'auto', label: '自动检测' },
  { value: 'utf-8', label: 'UTF-8' },
  { value: 'utf-8-sig', label: 'UTF-8（带 BOM）' },
  { value: 'utf-16', label: 'UTF-16' },
  { value: 'gbk', label: 'GBK' },
  { value: 'gb18030', label: 'GB18030' },
  { value: 'big5', label: 'Big5（繁体中文）' },
  { value: 'latin-1', label: 'Latin-1（西欧）' },
]

const LINE_ENDING_LABELS = {
  keep: '保持原样',
  crlf: 'CRLF（Windows）',
  lf: 'LF（Unix/macOS）',
  cr: 'CR（经典 Mac）',
}

const DELIMITER_LABELS = { ',': '逗号', '\t': '制表符', ';': '分号', '|': '竖线' }

const file = ref(null)
const busy = ref(false)
const error = ref('')
const report = ref(null)
const downloadUrl = ref('')
const outName = ref('')
const fileInput = ref(null)
const dragged = ref(false)

// 键名与后端 convert 接口的 Form 字段一一对应，勿改成驼峰
const opts = ref({
  from_format: 'auto',
  to_format: 'csv',
  from_encoding: 'auto',
  to_encoding: 'utf-8',
  line_endings: 'keep',
  quote_mode: 'minimal',
  blank_lines: 'skip',
})

function formatBytes(n) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(2)} MB`
}

function pickFile(f) {
  if (!f) return
  file.value = f
  report.value = null
  error.value = ''
  // 按扩展名预填格式选项，其余选项保留用户上次的选择
  const ext = (f.name.split('.').pop() || '').toLowerCase()
  if (ext === 'tsv' || ext === 'tab') {
    opts.value.from_format = 'tsv'
    opts.value.to_format = 'csv'
  } else if (ext === 'csv') {
    opts.value.from_format = 'csv'
    opts.value.to_format = 'tsv'
  } else {
    opts.value.from_format = 'auto'
    opts.value.to_format = 'csv'
  }
}

async function toError(res) {
  let detail = res.statusText || `请求失败 (${res.status})`
  try {
    const body = await res.json()
    const d = body.detail
    if (typeof d === 'string') detail = d
    else if (Array.isArray(d)) detail = d.map((item) => item.msg || JSON.stringify(item)).join('；')
    else if (d) detail = JSON.stringify(d)
  } catch {
    /* 保留默认信息 */
  }
  return new Error(detail)
}

function outFileName() {
  const name = file.value?.name || 'converted'
  const dot = name.lastIndexOf('.')
  const stem = dot > 0 ? name.slice(0, dot) : name
  return `${stem}.${opts.value.to_format}`
}

function triggerDownload() {
  const a = document.createElement('a')
  a.href = downloadUrl.value
  a.download = outName.value
  document.body.appendChild(a)
  a.click()
  a.remove()
}

async function convert() {
  if (!file.value || busy.value) return
  busy.value = true
  error.value = ''
  report.value = null
  try {
    const form = new FormData()
    form.append('file', file.value)
    for (const [key, value] of Object.entries(opts.value)) form.append(key, value)

    let res
    try {
      res = await fetch('/api/tools/csv-tsv/convert', { method: 'POST', body: form })
    } catch {
      notifyConnectionLost()
      throw new Error('无法连接本地服务，转换未执行。')
    }
    if (!res.ok) throw await toError(res)

    const blob = await res.blob()
    const raw = res.headers.get('X-Convert-Report')
    report.value = raw ? JSON.parse(raw) : null
    outName.value = outFileName()
    if (downloadUrl.value) URL.revokeObjectURL(downloadUrl.value)
    downloadUrl.value = URL.createObjectURL(blob)
    triggerDownload()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

function pickFromDialog() {
  fileInput.value?.click()
}

function onDrop(event) {
  dragged.value = false
  pickFile(event.dataTransfer.files?.[0])
}

function reset() {
  file.value = null
  report.value = null
  error.value = ''
}

onBeforeUnmount(() => {
  if (downloadUrl.value) URL.revokeObjectURL(downloadUrl.value)
})
</script>

<template>
  <div class="stack">
    <section
      v-if="!file"
      class="panel dropzone"
      :class="{ dragged }"
      role="button"
      tabindex="0"
      @click="pickFromDialog"
      @keydown.enter="pickFromDialog"
      @dragover.prevent="dragged = true"
      @dragleave="dragged = false"
      @drop.prevent="onDrop"
    >
      <input ref="fileInput" type="file" accept=".csv,.tsv,.tab,.txt" hidden @change="pickFile($event.target.files[0])" />
      <p class="dz-title">拖入 CSV / TSV 文件，或点击选择</p>
      <p class="dz-hint">单文件上限 100 MB；支持 CSV、TSV 及任意逗号 / 制表符 / 分号分隔的文本表</p>
    </section>

    <template v-if="file">
      <section class="panel">
        <div class="file-row">
          <div class="file-meta">
            <span class="file-name mono">{{ file.name }}</span>
            <span class="file-size">{{ formatBytes(file.size) }}</span>
          </div>
          <button class="btn" @click="reset">← 换一个文件</button>
        </div>

        <div class="opts">
          <div class="opt">
            <label class="label" for="ct-from-format">源格式</label>
            <select id="ct-from-format" v-model="opts.from_format" class="field">
              <option value="auto">自动检测</option>
              <option value="csv">CSV（逗号分隔）</option>
              <option value="tsv">TSV（制表符分隔）</option>
            </select>
          </div>
          <div class="opt">
            <label class="label" for="ct-to-format">目标格式</label>
            <select id="ct-to-format" v-model="opts.to_format" class="field">
              <option value="csv">CSV（逗号分隔）</option>
              <option value="tsv">TSV（制表符分隔）</option>
            </select>
          </div>
          <div class="opt">
            <label class="label" for="ct-from-encoding">源编码</label>
            <select id="ct-from-encoding" v-model="opts.from_encoding" class="field">
              <option v-for="item in ENCODINGS" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </div>
          <div class="opt">
            <label class="label" for="ct-to-encoding">目标编码</label>
            <select id="ct-to-encoding" v-model="opts.to_encoding" class="field">
              <option v-for="item in ENCODINGS.filter((e) => e.value !== 'auto')" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>
          </div>
          <div class="opt">
            <label class="label" for="ct-line-endings">换行符</label>
            <select id="ct-line-endings" v-model="opts.line_endings" class="field">
              <option value="keep">保持原样</option>
              <option value="crlf">CRLF（Windows）</option>
              <option value="lf">LF（Unix/macOS）</option>
            </select>
          </div>
          <div class="opt">
            <label class="label" for="ct-quote">引号风格</label>
            <select id="ct-quote" v-model="opts.quote_mode" class="field">
              <option value="minimal">按需添加（推荐）</option>
              <option value="all">全部字段加引号</option>
            </select>
          </div>
          <div class="opt">
            <label class="label" for="ct-blank">空行处理</label>
            <select id="ct-blank" v-model="opts.blank_lines" class="field">
              <option value="skip">跳过空行</option>
              <option value="keep">保留空行</option>
            </select>
          </div>
          <div class="opt action">
            <span class="label">执行</span>
            <button class="btn primary convert-btn" :disabled="busy" @click="convert">
              {{ busy ? '转换中…' : '转换并下载' }}
            </button>
          </div>
        </div>
      </section>

      <p v-if="error" class="error-text">{{ error }}</p>

      <section v-if="report" class="panel">
        <div class="pane-head">
          <span class="label">转换结果</span>
          <button class="btn" @click="triggerDownload">重新下载 {{ outName }}</button>
        </div>
        <div class="facts">
          <div class="fact">
            <span class="fact-label">源编码</span>
            <span class="fact-value">
              {{ report.source_encoding }}
              <span v-if="report.source_auto_detected" class="tag">自动检测</span>
            </span>
          </div>
          <div class="fact">
            <span class="fact-label">目标编码</span>
            <span class="fact-value">{{ report.output_encoding }}</span>
          </div>
          <div class="fact">
            <span class="fact-label">换行符</span>
            <span class="fact-value">
              {{ LINE_ENDING_LABELS[report.source_line_ending] || report.source_line_ending }}
              → {{ LINE_ENDING_LABELS[report.output_line_ending] || report.output_line_ending }}
            </span>
          </div>
          <div class="fact">
            <span class="fact-label">分隔符</span>
            <span class="fact-value">
              {{ DELIMITER_LABELS[report.delimiter_in] || report.delimiter_in }}
              → {{ DELIMITER_LABELS[report.delimiter_out] || report.delimiter_out }}
            </span>
          </div>
          <div class="fact">
            <span class="fact-label">行列</span>
            <span class="fact-value mono">{{ report.rows.toLocaleString('zh-CN') }} 行 × {{ report.cols }} 列</span>
          </div>
          <div class="fact">
            <span class="fact-label">输出大小</span>
            <span class="fact-value mono">
              {{ formatBytes(report.output_bytes) }}
              <span class="dim">· {{ report.elapsed_ms }} ms</span>
            </span>
          </div>
          <div v-if="report.blank_removed" class="fact">
            <span class="fact-label">空行</span>
            <span class="fact-value mono">已跳过 {{ report.blank_removed }} 行</span>
          </div>
        </div>

        <p v-for="(w, i) in report.warnings" :key="i" class="warn-text">⚠ {{ w }}</p>

        <template v-if="report.preview.length">
          <span class="label preview-label">输出预览（前 {{ report.preview.length }} 行原始文本）</span>
          <pre class="mono preview">{{ report.preview.join('\n') }}</pre>
        </template>
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

.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.file-meta {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 12.5px;
  color: var(--ink-dim);
  white-space: nowrap;
}

.opts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px 16px;
}

.opt {
  display: flex;
  flex-direction: column;
}

.opt.action {
  justify-content: flex-end;
}

.convert-btn {
  width: 100%;
}

.facts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 10px 18px;
  margin-top: 4px;
}

.fact {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.fact-label {
  font-size: 12.5px;
  color: var(--ink-dim);
}

.fact-value {
  font-size: 13.5px;
}

.tag {
  font-size: 11.5px;
  padding: 1px 8px;
  border-radius: 999px;
  margin-left: 4px;
  color: var(--cat-data);
  border: 1px solid color-mix(in srgb, var(--cat-data) 40%, transparent);
  background: color-mix(in srgb, var(--cat-data) 10%, transparent);
}

.dim {
  color: var(--ink-dim);
}

.warn-text {
  color: var(--accent);
  font-size: 13px;
  margin: 12px 0 0;
}

.pane-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.preview-label {
  display: block;
  margin-top: 16px;
}

.preview {
  margin: 0;
  padding: 12px 14px;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 220px;
  overflow: auto;
}

@media (max-width: 640px) {
  .file-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
