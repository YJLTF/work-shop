export default {
  id: 'volcano',
  name: '差异基因分析',
  description: '上传差异表达结果表，交互式火山图展示上调/下调/非显著基因的整体分布',
  category: 'bio',
  icon: 'volcano',
  keywords: ['volcano', 'huoshantu', '火山图', '差异', '基因', '表达', '生信', '转录组', 'DEG', 'fc', 'qval', 'excel'],
  backend: true,
  component: () => import('./ToolVolcano.vue'),
}
