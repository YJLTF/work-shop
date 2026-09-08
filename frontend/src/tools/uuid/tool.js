export default {
  id: 'uuid',
  name: 'UUID 生成',
  description: '批量生成 UUID v4，支持大写、去连字符、包裹花括号',
  category: 'dev',
  icon: 'copy',
  keywords: ['uuid', 'guid', 'v4', 'id', 'shengcheng', '生成', '标识符'],
  backend: false,
  component: () => import('./ToolUuid.vue'),
}
