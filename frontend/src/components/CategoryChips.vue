<script setup>
import { computed } from 'vue'
import { CATEGORIES } from '../tools/categories'

const props = defineProps({
  modelValue: { type: String, default: 'all' },
  counts: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:modelValue'])

const chips = computed(() => [
  { id: 'all', label: '全部', count: Object.values(props.counts).reduce((a, b) => a + b, 0), color: 'var(--accent)' },
  ...CATEGORIES.map((c) => ({ ...c, count: props.counts[c.id] || 0 })),
])
</script>

<template>
  <div class="chips" role="tablist" aria-label="按分类筛选">
    <button
      v-for="chip in chips"
      :key="chip.id"
      class="chip"
      :class="{ active: modelValue === chip.id }"
      :style="{ '--chip-color': chip.color }"
      role="tab"
      :aria-selected="modelValue === chip.id"
      @click="emit('update:modelValue', chip.id)"
    >
      <i class="dot" aria-hidden="true"></i>
      {{ chip.label }}
      <span class="count">{{ chip.count }}</span>
    </button>
  </div>
</template>

<style scoped>
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid var(--line-strong);
  background: var(--panel);
  color: var(--ink-dim);
  font-size: 13.5px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.chip .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--chip-color);
  opacity: 0.75;
}

.chip:hover {
  color: var(--ink);
  border-color: var(--chip-color);
}

.chip.active {
  color: var(--ink);
  border-color: var(--chip-color);
  background: color-mix(in srgb, var(--chip-color) 13%, var(--panel));
}

.count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-faint);
}

.chip.active .count {
  color: var(--chip-color);
}
</style>
