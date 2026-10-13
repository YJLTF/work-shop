export default {
  id: 'csv-tsv',
  name: 'CSV/TSV 转换',
  description: 'CSV 与 TSV 互转，可同时转换编码（UTF-8/GBK 等）与换行符（CRLF/LF）',
  category: 'data',
  icon: 'convert',
  keywords: ['csv', 'tsv', 'zhuanhuan', '转换', '编码', 'encoding', 'gbk', 'utf-8', '换行', 'crlf', 'lf', '分隔符', 'delimiter', 'excel', 'txt'],
  backend: true,
  component: () => import('./ToolCsvTsv.vue'),
}
