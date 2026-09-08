<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const query = defineModel({ type: String, default: '' })
const input = ref(null)

function onKeydown(event) {
  const target = event.target
  const typing = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')
  if (typing) return
  if (event.key === '/' || (event.key === 's' && !event.ctrlKey && !event.metaKey)) {
    event.preventDefault()
    input.value?.focus()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="search">
    <svg class="glass" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.8-3.8" />
    </svg>
    <input
      ref="input"
      v-model="query"
      type="search"
      class="search-input"
      placeholder="搜索工具，如：json、正则、统计…"
      aria-label="搜索工具"
    />
    <span v-if="!query" class="hint"><span class="kbd">/</span></span>
    <button v-else class="clear" aria-label="清空搜索" @click="query = ''">✕</button>
  </div>
</template>

<style scoped>
.search {
  position: relative;
  display: flex;
  align-items: center;
}

.glass {
  position: absolute;
  left: 15px;
  width: 18px;
  height: 18px;
  color: var(--ink-faint);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 13px 52px 13px 44px;
  font-size: 15px;
  color: var(--ink);
  background: var(--panel);
  border: 1px solid var(--line-strong);
  border-radius: 12px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  appearance: none;
}

.search-input::placeholder {
  color: var(--ink-faint);
}

.search-input::-webkit-search-cancel-button {
  display: none;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.hint,
.clear {
  position: absolute;
  right: 14px;
  display: grid;
  place-items: center;
}

.clear {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  color: var(--ink-dim);
  font-size: 12px;
  background: var(--panel-2);
  border: 1px solid var(--line);
}

.clear:hover {
  color: var(--ink);
  border-color: var(--accent);
}
</style>
