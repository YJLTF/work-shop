<script setup>
import { computed } from 'vue'
import { getCategory } from '../tools/categories'

const props = defineProps({
  tool: { type: Object, default: null },
  title: { type: String, default: '' },
})

const category = computed(() => (props.tool ? getCategory(props.tool.category) : null))
</script>

<template>
  <div class="page-shell">
    <RouterLink to="/" class="back">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M14.5 5.5 8 12l6.5 6.5" />
      </svg>
      返回工具墙
    </RouterLink>

    <header class="page-head">
      <div class="titles">
        <h1>{{ tool ? tool.name : title }}</h1>
        <p v-if="tool?.description">{{ tool.description }}</p>
      </div>
      <span v-if="category" class="cat-tag" :style="{ '--cat': category.color }">
        <i aria-hidden="true"></i>{{ category.label }}
      </span>
    </header>

    <slot />
  </div>
</template>

<style scoped>
.page-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  align-self: flex-start;
  font-size: 13.5px;
  color: var(--ink-dim);
  padding: 6px 10px;
  margin-left: -10px;
  border-radius: 8px;
  transition: color 0.15s ease, background 0.15s ease;
}

.back:hover {
  color: var(--ink);
  background: var(--panel-2);
}

.back svg {
  width: 15px;
  height: 15px;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.titles h1 {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.titles p {
  margin: 6px 0 0;
  font-size: 14px;
  color: var(--ink-dim);
}

.cat-tag {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 13px;
  border-radius: 999px;
  font-size: 12.5px;
  color: var(--cat);
  border: 1px solid color-mix(in srgb, var(--cat) 35%, transparent);
  background: color-mix(in srgb, var(--cat) 10%, transparent);
}

.cat-tag i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--cat);
}
</style>
