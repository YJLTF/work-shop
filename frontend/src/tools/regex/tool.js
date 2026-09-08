export default {
  id: 'regex',
  name: '正则测试',
  description: 'Python re 引擎实时匹配、分组捕获与批量替换',
  category: 'text',
  icon: 'regex',
  keywords: ['regex', 'regexp', 'zhengze', '正则', '表达式', '匹配', '替换', 'pattern'],
  backend: true,
  component: () => import('./ToolRegex.vue'),
}
