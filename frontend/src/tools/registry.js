/**
 * 前端工具注册表。
 * 新增工具：在 src/tools/ 下新建文件夹，放入 tool.js（元数据）与工具组件即可，
 * 本文件通过 glob 自动收集，无需手工登记。
 */

const modules = import.meta.glob('./*/tool.js', { eager: true })

export const tools = Object.values(modules)
  .map((mod) => mod.default)
  .filter(Boolean)
  .sort((a, b) => a.name.localeCompare(b.name, 'zh-Hans-CN'))

export function getTool(id) {
  return tools.find((tool) => tool.id === id)
}
