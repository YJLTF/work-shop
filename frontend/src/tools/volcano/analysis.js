// 差异基因分析的纯数据层：表格行分组、KEGG 注释解析、桑基图子图组装。
// 不依赖 Vue / ECharts / DOM，输入输出均为普通对象，便于独立理解与复用。

export const COLOR = {
  up: '#e0524f',
  down: '#3f7fd9',
  no: '#9aa3ad',
}

/** 把表格行换算成 (log2FC, -log10(q)) 点并按阈值分成 up / down / no 三组。 */
export function buildGroups(rows, { nameIdx, xIdx, yIdx, fcCut, qCut, xIsLog2 }) {
  const result = { up: [], down: [], no: [], skipped: 0 }
  const yCap = 320 // q=0 时 -log10 会发散，钳到接近双精度下限的读数
  rows.forEach((row, i) => {
    const rawX = Number(row[xIdx])
    const q = Number(row[yIdx])
    let x
    if (xIsLog2) {
      x = Number.isFinite(rawX) ? rawX : NaN
    } else {
      x = rawX > 0 ? Math.log2(rawX) : NaN
    }
    let y
    if (!Number.isFinite(q)) {
      y = NaN
    } else if (q <= 0) {
      y = yCap
    } else {
      y = -Math.log10(q)
    }
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      result.skipped += 1
      return
    }
    const gene = (row[nameIdx] ?? `gene_${i + 1}`).toString()
    const point = { value: [x, y], name: gene, q, row: i }
    if (q <= qCut && Math.abs(x) >= fcCut) {
      result[x >= 0 ? 'up' : 'down'].push(point)
    } else {
      result.no.push(point)
    }
  })
  return result
}

const pathwayCache = new Map() // 原始注释文本 -> 通路名数组（大数据集下同一文本不值得反复解析）

/** 解析 KEGG 注释：'04066(HIF-1 signaling pathway);04216(Ferroptosis)' -> ['HIF-1 signaling pathway', 'Ferroptosis'] */
export function parsePathways(raw) {
  if (!raw) return []
  const cached = pathwayCache.get(raw)
  if (cached) return cached
  const out = new Set()
  for (const part of String(raw).replace(/；/g, ';').split(';')) {
    const t = part.trim()
    if (!t) continue
    const m = t.match(/^\d+\((.+)\)$/)
    const name = (m ? m[1] : t).trim()
    if (name) out.add(name)
  }
  const names = [...out]
  pathwayCache.set(raw, names)
  return names
}

/** 组装桑基图数据（按 mode 取范围）：
 * linked —— 与选中项相关的子图：选中基因 → 该基因的通路 + 共享这些通路的其他显著基因；
 * all    —— 全部有 KEGG 注释的显著基因及其通路；
 * 其余情况返回 null（不绘制）。 */
export function buildSankeyGraph(rows, groups, { keggIdx, mode, selected, pathwayColor, denseLimit = 120 }) {
  if (mode === 'none' || !rows || keggIdx == null || keggIdx < 0) return null

  // 显著基因池，按显著性排序（q 越小越靠前，q 相同则 |log2FC| 大者靠前）
  const pool = []
  for (const kind of ['up', 'down']) {
    for (const p of groups[kind]) {
      const paths = parsePathways(rows[p.row]?.[keggIdx])
      if (paths.length) pool.push({ gene: p.name, kind, paths, q: p.q, x: p.value[0] })
    }
  }
  pool.sort((a, b) => a.q - b.q || Math.abs(b.x) - Math.abs(a.x))

  const links = []
  const pathCount = new Map()
  const geneKind = new Map()
  const genePaths = new Map()
  // allowedPaths 限定只画子图范围内的通路（null = 不限）
  const addGene = (entry, allowedPaths) => {
    if (!entry || geneKind.has(entry.gene)) return
    geneKind.set(entry.gene, entry.kind)
    genePaths.set(entry.gene, entry.paths)
    for (const path of entry.paths) {
      if (allowedPaths && !allowedPaths.has(path)) continue
      links.push({ source: entry.gene, target: path, value: 1 })
      pathCount.set(path, (pathCount.get(path) ?? 0) + 1)
    }
  }

  if (mode === 'all') {
    for (const t of pool) addGene(t, null)
  } else {
    if (!selected) return null // linked 模式但还没有选中项
    const names = selected.type === 'multi' ? selected.names : [selected.name]
    const byName = new Map(pool.map((t) => [t.gene, t]))
    let ptByName = null // 惰性构建：name -> {p, kind}，供没进显著池的选中基因回查
    const centers = []
    for (const selName of new Set(names)) {
      let entry = byName.get(selName) ?? null
      if (!entry) {
        ptByName ??= (() => {
          const m = new Map()
          for (const kind of ['up', 'down', 'no']) {
            for (const p of groups[kind]) m.set(p.name, { p, kind })
          }
          return m
        })()
        const hit = ptByName.get(selName)
        if (hit) {
          const paths = parsePathways(rows[hit.p.row]?.[keggIdx])
          if (paths.length) entry = { gene: selName, kind: hit.kind, paths, q: hit.p.q, x: hit.p.value[0] }
        }
      }
      if (entry && entry.paths.length) centers.push(entry)
    }
    if (!centers.length) return null // 选中的基因都没有 KEGG 注释
    const allowedPaths = new Set(centers.flatMap((c) => c.paths))
    // 选中基因先入列（排最前，渲染在桑基图顶部），再补共享通路的其他显著基因
    for (const c of centers) addGene(c, allowedPaths)
    for (const t of pool) {
      if (t.paths.some((p) => allowedPaths.has(p))) addGene(t, allowedPaths)
    }
  }
  if (!geneKind.size) return null

  // 密集排版优化：通路按规模降序（大通路聚在一起，减少连线交叉）；
  // 基因节点超过 denseLimit 时隐藏基因名标签（悬停 tooltip / 滚轮缩放仍可查看）
  const dense = geneKind.size > denseLimit
  const nodes = []
  for (const [gene, kind] of geneKind) {
    nodes.push({
      name: gene,
      itemStyle: { color: COLOR[kind] },
      // 基因名统一放左侧（通路在右列，名签朝左避开连线）
      label: { position: 'left', show: !dense },
    })
  }
  const pathwayEntries = [...pathCount.entries()].sort((a, b) => b[1] - a[1])
  for (const [path, count] of pathwayEntries) {
    nodes.push({ name: path, pathway: true, value: count, itemStyle: { color: pathwayColor } })
  }
  return {
    nodes,
    links,
    picked: [...genePaths].map(([gene, paths]) => ({ gene, paths })),
    geneCount: geneKind.size,
    pathCount: pathCount.size,
    dense,
  }
}
