<script setup>
import { computed } from 'vue'
import { getCategory } from '../tools/categories'
import ToolIcon from './ToolIcon.vue'

const props = defineProps({
  tool: { type: Object, required: true },
  index: { type: Number, default: 0 },
})

const category = computed(() => getCategory(props.tool.category))
const style = computed(() => ({
  '--cat': category.value.color,
  '--enter-delay': `${Math.min(props.index * 45, 400)}ms`,
}))
</script>

<template>
  <RouterLink :to="`/tool/${tool.id}`" class="tool-card" :style="style">
    <div class="card-top">
      <span class="icon-plate">
        <ToolIcon :name="tool.icon" />
      </span>
      <span v-if="tool.backend" class="engine">Python</span>
    </div>

    <h3 class="name">{{ tool.name }}</h3>
    <p class="desc">{{ tool.description }}</p>

    <div class="card-foot">
      <span class="cat">
        <i class="cat-dot" aria-hidden="true"></i>
        {{ category.label }}
      </span>
      <span class="open">打开 →</span>
    </div>
  </RouterLink>
</template>

<style scoped>
.tool-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow-card);
  /* 大量卡片时跳过离屏卡片的布局与绘制（原生懒渲染，不影响 Ctrl+F 与锚点） */
  content-visibility: auto;
  contain-intrinsic-size: auto 178px;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease,
    opacity 0.4s ease;
  animation: card-in 0.45s cubic-bezier(0.22, 0.9, 0.3, 1) both;
  animation-delay: var(--enter-delay);
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tool-card:hover {
  transform: translateY(-4px);
  border-color: color-mix(in srgb, var(--cat) 55%, var(--line-strong));
  box-shadow: var(--shadow-lift);
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 4px;
}

.icon-plate {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: var(--cat);
  background: color-mix(in srgb, var(--cat) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--cat) 26%, transparent);
  transition: transform 0.18s ease;
}

.tool-card:hover .icon-plate {
  transform: rotate(-5deg) scale(1.06);
}

.icon-plate svg {
  width: 23px;
  height: 23px;
}

.engine {
  font-family: var(--font-mono);
  font-size: 10.5px;
  letter-spacing: 0.08em;
  color: var(--ink-dim);
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  padding: 3px 9px;
}

.name {
  font-size: 16.5px;
  font-weight: 650;
}

.desc {
  margin: 0;
  flex: 1;
  font-size: 13.5px;
  color: var(--ink-dim);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.cat {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  color: var(--ink-dim);
}

.cat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--cat);
}

.open {
  font-size: 12.5px;
  color: var(--cat);
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.tool-card:hover .open,
.tool-card:focus-visible .open {
  opacity: 1;
  transform: translateX(0);
}
</style>
