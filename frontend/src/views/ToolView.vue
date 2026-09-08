<script setup>
import { computed, defineAsyncComponent, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PageShell from '../components/PageShell.vue'
import { notifyConnectionLost } from '../api'
import { getTool } from '../tools/registry'

const route = useRoute()
const tool = computed(() => getTool(route.params.id))
const loadError = ref(false)

const component = computed(() => {
  if (!tool.value) return null
  loadError.value = false
  return defineAsyncComponent({
    loader: tool.value.component,
    onError: () => {
      loadError.value = true
      // 加载失败很可能是服务已退出，让外壳感知并给出明确提示
      notifyConnectionLost()
    },
  })
})

watch(() => route.params.id, () => (loadError.value = false))
</script>

<template>
  <PageShell :tool="tool">
    <template v-if="tool && component && !loadError">
      <Suspense>
        <component :is="component" :key="tool.id" />
        <template #fallback>
          <div class="panel loading">
            <span class="spinner" aria-hidden="true"></span>
            正在加载工具…
          </div>
        </template>
      </Suspense>
    </template>

    <div v-else class="panel missing">
      <template v-if="loadError">
        <p class="missing-title">工具加载失败</p>
        <p class="missing-hint">组件文件缺失或存在错误，请检查控制台输出。</p>
      </template>
      <template v-else>
        <p class="missing-title">没有「{{ route.params.id }}」这件工具</p>
        <p class="missing-hint">它可能还未创建，或 id 与注册信息不一致。</p>
      </template>
      <RouterLink to="/" class="btn">回到工具墙</RouterLink>
    </div>
  </PageShell>
</template>

<style scoped>
.loading,
.missing {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 52px 20px;
  color: var(--ink-dim);
}

.missing-title {
  margin: 0;
  font-weight: 650;
  font-size: 15.5px;
  color: var(--ink);
}

.missing-hint {
  margin: 0 0 10px;
  font-size: 13.5px;
}

.spinner {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2.5px solid var(--line-strong);
  border-top-color: var(--accent);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
