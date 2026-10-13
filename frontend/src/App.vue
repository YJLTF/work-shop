<script setup>
import { onMounted, ref } from 'vue'
import { api, onConnectionLost } from './api'
import { useTheme } from './composables/useTheme'
// 兜底版本号取自 package.json；页脚实际显示以后端 /api/health 返回为准
import pkg from '../package.json'

const { theme, toggle } = useTheme()
const packaged = ref(false)
const version = ref(pkg.version)
// null | 'exiting'（正在停止） | 'stopped'（已退出） | 'lost'（连接断开）
const shutdownState = ref(null)
let healthTimer = null

function markLost() {
  if (shutdownState.value) return
  shutdownState.value = 'lost'
  clearInterval(healthTimer)
}

onMounted(async () => {
  try {
    const health = await api.get('/health')
    packaged.value = Boolean(health.packaged)
    // 版本号以后端为准，避免与 config.py 漂移
    if (health.version) version.value = health.version
    // 后端曾在线才开启探活：若一开始就是纯前端模式，不应误报"连接断开"
    healthTimer = setInterval(async () => {
      if (shutdownState.value) {
        clearInterval(healthTimer)
        return
      }
      try {
        await api.get('/health')
      } catch {
        markLost()
      }
    }, 10_000)
  } catch {
    /* 后端未就绪时页面仍可用（纯前端工具） */
  }
})

// 服务在别处被关闭（如关掉控制台窗口）时，任何请求失败都会进入告别页
onConnectionLost(markLost)

async function exitApp() {
  if (shutdownState.value) return
  if (!confirm('退出将停止本地服务并关闭 WorkShop，确定吗？')) return
  shutdownState.value = 'exiting'
  clearInterval(healthTimer)
  try {
    await api.post('/shutdown')
  } catch {
    /* 服务可能已先行停止 */
  }
  shutdownState.value = 'stopped'
}
</script>

<template>
  <div v-if="shutdownState" class="shutdown-screen" role="status">
    <div class="shutdown-card">
      <span class="shutdown-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <path d="M12 3v8" />
          <path d="M6.3 6.5a8 8 0 1 0 11.4 0" />
        </svg>
      </span>
      <h1 v-if="shutdownState === 'exiting'">正在停止服务…</h1>
      <h1 v-else-if="shutdownState === 'lost'">与服务器的连接已断开</h1>
      <h1 v-else>WorkShop 已停止</h1>
      <p class="shutdown-text">
        {{
          shutdownState === 'exiting'
            ? '正在退出本地服务，请稍候。'
            : shutdownState === 'lost'
              ? '本地服务可能已退出或未响应，此页面暂不可用。'
              : '本地服务已退出，此页面已完成使命。'
        }}
      </p>
      <p class="shutdown-hint">
        再次使用时，重新运行 <span class="mono">WorkShop.exe</span> 即可打开工具箱。
      </p>
    </div>
  </div>

  <div v-else class="app">
    <header class="app-header">
      <RouterLink to="/" class="brand">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M9.4 3.6 7.8 5.2a2.2 2.2 0 0 0 0 3.1l1.5 1.5-1 1-1.5-1.5a2.2 2.2 0 0 0-3.1 0L2.1 11l3.3 3.3 1.8-1.8 6.4 6.4 2.7 1 .9-.9-1-2.7-6.4-6.4 1.8-1.8L8.3 4.8Z"
              fill="currentColor"
            />
          </svg>
        </span>
        <span class="brand-text">
          <strong>WorkShop</strong>
          <small>个人工具箱</small>
        </span>
      </RouterLink>

      <div class="header-actions">
        <button
          class="icon-btn"
          :title="theme === 'dark' ? '切换到浅色' : '切换到深色'"
          @click="toggle"
        >
          <svg v-if="theme === 'dark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <circle cx="12" cy="12" r="4.2" />
            <path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5 5l1.7 1.7M17.3 17.3 19 19M19 5l-1.7 1.7M6.7 17.3 5 19" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11Z" />
          </svg>
        </button>

        <button
          v-if="packaged"
          class="icon-btn exit"
          title="退出服务"
          :disabled="shutdownState === 'exiting'"
          @click="exitApp"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <path d="M12 3v8" />
            <path d="M6.3 6.5a8 8 0 1 0 11.4 0" />
          </svg>
        </button>
      </div>
    </header>

    <main class="app-main">
      <RouterView />
    </main>

    <footer class="app-footer">
      <span class="mono">WorkShop v{{ version }}</span>
      <span class="dot" aria-hidden="true">·</span>
      <span>本地运行 · 数据不出机器</span>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 服务退出后的告别页：覆盖全部内容，纯前端状态，不依赖网络 */
.shutdown-screen {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  background: var(--bg);
  padding: 24px;
  animation: fade-in 0.35s ease both;
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.shutdown-card {
  max-width: 420px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.shutdown-icon {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  margin-bottom: 8px;
  color: var(--ink-faint);
  border: 1.5px solid var(--line-strong);
  background: var(--panel);
}

.shutdown-icon svg {
  width: 26px;
  height: 26px;
}

.shutdown-card h1 {
  font-size: 21px;
  font-weight: 700;
}

.shutdown-text {
  margin: 0;
  color: var(--ink-dim);
  font-size: 14px;
}

.shutdown-hint {
  margin: 10px 0 0;
  color: var(--ink-faint);
  font-size: 12.5px;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 28px 14px;
  border-bottom: 1px solid var(--line);
  background: color-mix(in srgb, var(--bg) 82%, transparent);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 20;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: var(--accent);
  color: var(--on-accent);
  box-shadow: 0 3px 10px -3px var(--accent);
}

.brand-mark svg {
  width: 21px;
  height: 21px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.brand-text strong {
  font-family: var(--font-mono);
  font-size: 16.5px;
  letter-spacing: 0.06em;
}

.brand-text small {
  font-size: 11.5px;
  color: var(--ink-dim);
  letter-spacing: 0.28em;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--ink-dim);
  transition: color 0.15s ease, border-color 0.15s ease;
}

.icon-btn:hover {
  color: var(--ink);
  border-color: var(--accent);
}

.icon-btn.exit {
  color: var(--danger);
}

.icon-btn svg {
  width: 18px;
  height: 18px;
}

.app-main {
  flex: 1;
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 30px 28px 60px;
}

.app-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 18px;
  border-top: 1px solid var(--line);
  color: var(--ink-faint);
  font-size: 12.5px;
}

.app-footer .mono {
  font-size: 12px;
}

.dot {
  color: var(--ink-faint);
}

@media (max-width: 640px) {
  .app-header,
  .app-main {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>
