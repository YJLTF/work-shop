<script setup>
import { computed, ref, watch } from 'vue'
import SearchBar from '../components/SearchBar.vue'
import CategoryChips from '../components/CategoryChips.vue'
import ToolCard from '../components/ToolCard.vue'
import { tools } from '../tools/registry'
import { CATEGORIES } from '../tools/categories'
import { fuzzyScore } from '../composables/useFuzzySearch'

const query = ref('')
const category = ref('all')

const counts = computed(() => {
  const result = {}
  for (const cat of CATEGORIES) {
    result[cat.id] = tools.filter((tool) => tool.category === cat.id).length
  }
  return result
})

const filtered = computed(() => {
  let list = tools
  if (category.value !== 'all') {
    list = list.filter((tool) => tool.category === category.value)
  }
  if (query.value.trim()) {
    list = list
      .map((tool) => ({ tool, score: fuzzyScore(tool, query.value) }))
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .map((item) => item.tool)
  }
  return list
})

const searching = computed(() => Boolean(query.value.trim()) || category.value !== 'all')

function resetFilters() {
  query.value = ''
  category.value = 'all'
}
</script>

<template>
  <div class="home">
    <section class="hero">
      <p class="eyebrow mono">WORKBENCH / 工具墙</p>
      <h1>今天要用哪件工具？</h1>
      <p class="sub">共 {{ tools.length }} 件常用工具，全部在本地运行。</p>

      <div class="filters">
        <SearchBar v-model="query" />
        <CategoryChips v-model="category" :counts="counts" />
      </div>
    </section>

    <section class="group">
      <div v-if="filtered.length" class="grid">
        <ToolCard
          v-for="(tool, i) in filtered"
          :key="tool.id"
          :tool="tool"
          :index="i"
        />
      </div>
      <div v-else class="panel empty">
        <p class="empty-title">没有找到匹配「{{ query }}」的工具</p>
        <p class="empty-hint">试试更短的关键词，或者清除筛选条件。</p>
        <button class="btn" @click="resetFilters">清除搜索与筛选</button>
      </div>
    </section>

    <p v-if="searching && filtered.length" class="result-count">
      找到 {{ filtered.length }} 件工具
    </p>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.hero {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 6px 2px 0;
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.22em;
  color: var(--accent);
}

.hero h1 {
  font-size: 30px;
  font-weight: 750;
  letter-spacing: 0.01em;
}

.sub {
  margin: 0;
  color: var(--ink-dim);
  font-size: 14.5px;
}

.filters {
  display: flex;
  flex-direction: column;
  gap: 13px;
  margin-top: 16px;
}

.group {
  display: flex;
  flex-direction: column;
  gap: 13px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.empty {
  text-align: center;
  padding: 44px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.empty-title {
  margin: 0;
  font-weight: 600;
  font-size: 15.5px;
}

.empty-hint {
  margin: 0 0 12px;
  color: var(--ink-dim);
  font-size: 13.5px;
}

.result-count {
  margin: -12px 2px 0;
  font-size: 12.5px;
  color: var(--ink-faint);
}
</style>
