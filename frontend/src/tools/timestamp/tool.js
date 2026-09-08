export default {
  id: 'timestamp',
  name: '时间戳转换',
  description: 'Unix 时间戳与日期互转，秒/毫秒自动识别，本地时区显示',
  category: 'quick',
  icon: 'clock',
  keywords: ['timestamp', 'unix', 'epoch', 'shijian', '时间戳', '日期', '时间', '转换'],
  backend: false,
  component: () => import('./ToolTimestamp.vue'),
}
