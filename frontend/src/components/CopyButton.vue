<script setup>
import { ref } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  label: { type: String, default: '复制' },
  disabled: { type: Boolean, default: false },
})

const copied = ref(false)
let timer = null

async function copy() {
  if (props.disabled || !props.text) return
  try {
    await navigator.clipboard.writeText(props.text)
  } catch {
    /* 剪贴板不可用时静默失败 */
    return
  }
  copied.value = true
  clearTimeout(timer)
  timer = setTimeout(() => (copied.value = false), 1400)
}
</script>

<template>
  <button class="btn copy-btn" :disabled="disabled || !text" @click="copy">
    {{ copied ? '已复制 ✓' : label }}
  </button>
</template>

<style scoped>
.copy-btn {
  padding: 6px 12px;
  font-size: 12.5px;
}

.copy-btn:not(:disabled):not(.copied) {
  color: var(--ink-dim);
}
</style>
