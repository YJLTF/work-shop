import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 开发时前端请求代理到本地 FastAPI 服务
      '/api': 'http://127.0.0.1:8321',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
