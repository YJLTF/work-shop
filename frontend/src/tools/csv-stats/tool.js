export default {
  id: 'csv-stats',
  name: 'CSV 统计',
  description: '上传 CSV 即得行列概况、数值列统计摘要与数据预览',
  category: 'data',
  icon: 'table',
  keywords: ['csv', 'tongji', '统计', '分析', '表格', '数据', 'excel', 'tsv'],
  backend: true,
  component: () => import('./ToolCsvStats.vue'),
}
