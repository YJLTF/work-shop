/**
 * 轻量模糊搜索：
 * - 完整命中按字段加权（名称 > 关键词 > 标识 > 描述）
 * - 否则尝试子序列匹配（如 "js" 可命中 "json"），连续片段额外加分
 * 返回带 score 的数组（0 表示不匹配），由调用方过滤排序。
 */

const WEIGHTS = { name: 100, keywords: 60, id: 50, description: 20, category: 15 }

function isSubsequence(query, target) {
  let i = 0
  for (const ch of target) {
    if (ch === query[i]) i++
    if (i === query.length) return true
  }
  return false
}

function longestCommonChunk(query, target) {
  let best = 0
  let current = 0
  let ti = 0
  for (const ch of query) {
    const found = target.indexOf(ch, ti)
    if (found === -1) {
      current = 0
      ti = 0
    } else {
      current = found === ti ? current + 1 : 1
      ti = found + 1
      best = Math.max(best, current)
    }
  }
  return best
}

function scoreField(query, field, weight) {
  if (!field) return 0
  const target = field.toLowerCase()
  if (target.includes(query)) return weight + Math.min(query.length * 2, 20)
  if (isSubsequence(query, target)) {
    const chunk = longestCommonChunk(query, target)
    return Math.round(weight * 0.5 + chunk * 4)
  }
  return 0
}

function scoreWith(query, tool) {
  return Math.max(
    scoreField(query, tool.name, WEIGHTS.name),
    scoreField(query, (tool.keywords || []).join(' '), WEIGHTS.keywords),
    scoreField(query, tool.id.replace(/-/g, ' '), WEIGHTS.id),
    scoreField(query, tool.description, WEIGHTS.description),
    scoreField(query, tool.categoryLabel, WEIGHTS.category),
  )
}

export function fuzzyScore(tool, rawQuery) {
  const query = rawQuery.trim().toLowerCase()
  if (!query) return 0
  // 「shi jian」这类带空格的输入，去掉空格后再试一次（命中拼音关键词）
  const compact = query.replace(/\s+/g, '')
  return Math.max(scoreWith(query, tool), compact === query ? 0 : scoreWith(compact, tool))
}
