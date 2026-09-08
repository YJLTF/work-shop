export default {
  id: 'hash',
  name: '哈希计算',
  description: '文本与文件的 MD5 / SHA 摘要，大文件流式计算',
  category: 'dev',
  icon: 'hash',
  keywords: ['hash', 'haxi', 'md5', 'sha1', 'sha256', 'sha512', '哈希', '摘要', '校验和'],
  backend: true,
  component: () => import('./ToolHash.vue'),
}
