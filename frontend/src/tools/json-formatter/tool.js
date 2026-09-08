/** 工具元数据：注册表自动收集，id 需与后端工具 id 一致（如有后端部分）。 */
export default {
  id: 'json-formatter',
  name: 'JSON 格式化',
  description: '格式化、压缩与校验 JSON，语法错误精准定位到行列',
  category: 'text',
  icon: 'braces',
  keywords: ['json', 'format', 'beautify', 'minify', 'geshihua', '格式化', '压缩', '校验', '解析'],
  backend: false,
  component: () => import('./ToolJsonFormatter.vue'),
}
