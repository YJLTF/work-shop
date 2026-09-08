/** 工具分类：颜色对应「工具手柄色」，在卡片、标签、页面外壳中复用。 */

export const CATEGORIES = [
  { id: 'text', label: '文本处理', color: 'var(--cat-text)' },
  { id: 'dev', label: '开发辅助', color: 'var(--cat-dev)' },
  { id: 'data', label: '数据分析', color: 'var(--cat-data)' },
  { id: 'bio', label: '生信', color: 'var(--cat-bio)' },
  { id: 'quick', label: '日常效率', color: 'var(--cat-quick)' },
]

const categoryMap = Object.fromEntries(CATEGORIES.map((c) => [c.id, c]))

export function getCategory(id) {
  return categoryMap[id] || CATEGORIES[0]
}
