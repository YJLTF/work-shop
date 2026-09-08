<script setup>
import { ref, computed, watch, onBeforeUnmount, nextTick, toRaw } from 'vue'
import * as echarts from 'echarts/core'
import { ScatterChart, SankeyChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  ToolboxComponent,
  MarkLineComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ZRRect from 'zrender/lib/graphic/shape/Rect'
import { api } from '../../api'
import { useTheme } from '../../composables/useTheme'
import { COLOR, buildGroups, buildSankeyGraph } from './analysis'

echarts.use([
  ScatterChart,
  SankeyChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  ToolboxComponent,
  MarkLineComponent,
  CanvasRenderer,
])

const { theme } = useTheme()

// 主题相关配色（散点图与桑基图共用）
const GOLD = '#e8a33d'
const inkDim = computed(() => (theme.value === 'light' ? '#57607a' : '#a3abbe'))
const lineColor = computed(() => (theme.value === 'light' ? '#c2c8d6' : '#333c52'))
const tooltipBg = computed(() => (theme.value === 'light' ? '#ffffff' : '#1f2534'))
const tooltipInk = computed(() => (theme.value === 'light' ? '#1d2330' : '#e9ecf4'))

const meta = ref(null) // 后端解析结果：columns / detect / rows
const busy = ref(false)
const error = ref('')
const fileInput = ref(null)
const dragged = ref(false)

// 列映射与阈值（换文件或用户调整后，绘图全部在前端即时重算）
const nameIdx = ref(0)
const xIdx = ref(0)
const yIdx = ref(0)
const fcCut = ref(1)
const qCut = ref(0.05)
const keggIdx = ref(-1) // KEGG 注释列，-1 = 无（隐藏桑基图）

// 散点 ↔ 桑基图联动选中项：
// { type:'gene', name, kind, dataIndex } 或 { type:'multi', names:[...] }
const selected = ref(null)
// 桑基图绘制范围：none 未绘制（默认） / linked 与选中项相关的子图 / all 全部显著基因
const sankeyMode = ref('none')
const brushing = ref(false) // 散点图框选模式进行中
let brushShape = null // 拖拽时画在画布上的金色选框（zrender 图形，与事件同坐标系）
let brushStartPixel = null

const chartEl = ref(null)
let chart = null
let resizeObserver = null

const sankeyEl = ref(null)
let sankeyChart = null
let sankeyResizeObserver = null
let markedPoints = [] // 当前散点上标记（select 态）的点
let suppressPointLabels = false // 框选点过多时隐藏基因名标签，避免画面糊掉

// 示例数据为随机生成的模拟表格（scripts/make_demo_csv.py 可重新生成），
// 仅用于演示数据格式，不含任何真实项目数据。
const SAMPLE = {
  url: `${import.meta.env.BASE_URL}sample/volcano_demo.csv`,
  filename: 'volcano_demo.csv',
}

const xIsLog2 = computed(() => {
  if (!meta.value) return true
  return /log2/i.test(meta.value.columns[xIdx.value] || '')
})

const yIsQval = computed(() => {
  if (!meta.value) return true
  return !/^p[-_. ]?(val|value)$/i.test(meta.value.columns[yIdx.value] || '')
})

/** 上传/加载示例共用一套 busy / 错误 / 应用解析结果的流程。 */
async function runParse(load) {
  busy.value = true
  error.value = ''
  meta.value = null
  try {
    applyMeta(await load())
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

function toForm(file) {
  const form = new FormData()
  form.append('file', file)
  return form
}

function parseFile(file) {
  if (file) runParse(() => api.postForm('/tools/volcano/parse', toForm(file)))
}

async function loadSample() {
  await runParse(async () => {
    const blob = await (await fetch(SAMPLE.url)).blob()
    return api.postForm('/tools/volcano/parse', toForm(new File([blob], SAMPLE.filename)))
  })
}

function applyMeta(data) {
  meta.value = data
  const d = data.detect
  nameIdx.value = d.name ?? 0
  xIdx.value = d.log2fc ?? d.fc ?? 0
  yIdx.value = d.qval ?? d.pval ?? 0
  keggIdx.value = d.kegg ?? -1
  sankeyMode.value = 'none'
}

const groups = computed(() =>
  meta.value
    ? buildGroups(meta.value.rows, {
        nameIdx: nameIdx.value,
        xIdx: xIdx.value,
        yIdx: yIdx.value,
        fcCut: fcCut.value,
        qCut: qCut.value,
        xIsLog2: xIsLog2.value,
      })
    : { up: [], down: [], no: [], skipped: 0 }
)

const counts = computed(() => {
  const g = groups.value
  return {
    total: g.up.length + g.down.length + g.no.length,
    up: g.up.length,
    down: g.down.length,
    no: g.no.length,
  }
})

/** 桑基图数据：按 sankeyMode 组装（纯逻辑在 analysis.js）。 */
const sankeyData = computed(() => {
  if (!meta.value || keggIdx.value < 0) return null
  return buildSankeyGraph(meta.value.rows, groups.value, {
    keggIdx: keggIdx.value,
    mode: sankeyMode.value,
    selected: selected.value,
    pathwayColor: theme.value === 'light' ? '#8291b8' : '#6a7699',
  })
})

const sankeyHint = computed(() => {
  if (keggIdx.value < 0 || !meta.value) return ''
  if (brushing.value) return '框选模式：在散点图上拖拽框选，松开即绘制相关子图'
  const d = sankeyData.value
  if (d) {
    const sel = selected.value
    const scope =
      sankeyMode.value === 'all'
        ? '全部有 KEGG 注释的显著基因'
        : sel
          ? sel.type === 'multi'
            ? `选中的 ${sel.names.length} 个基因`
            : `「${sel.name}」`
          : ''
    return (
      `已绘制${scope}相关的子图：${d.geneCount} 个基因 · ${d.pathCount} 条通路` +
      (d.dense ? ' · 基因较多已隐藏名称，悬停可查看，滚轮可缩放' : '')
    )
  }
  if (sankeyMode.value === 'linked' && selected.value) {
    const label =
      selected.value.type === 'multi'
        ? `${selected.value.names.length} 个选中基因`
        : `「${selected.value.name}」`
    return `与${label}相关的子图为空（均无 KEGG 注释），未绘制`
  }
  return '点击散点图中的基因点，或用「框选绘制」框选一片，绘制与其相关的子图；也可点击「绘制全部」'
})

const KIND_BY_PREFIX = [
  ['上调', 'up'],
  ['下调', 'down'],
  ['非显著', 'no'],
]

function kindOf(seriesName) {
  for (const [prefix, kind] of KIND_BY_PREFIX) {
    if (seriesName.startsWith(prefix)) return kind
  }
  return null
}

function buildOption() {
  const g = groups.value
  const dim = inkDim.value
  const axis = theme.value === 'light' ? '#7b859c' : '#4c5878'
  const thresholdY = qCut.value > 0 ? -Math.log10(qCut.value) : 0

  // 点击散点后的“标记”样式：金色描边 + 基因名标签（select 态，仅选中点生效）；
  // 框选点数过多时 suppressPointLabels 会临时关掉标签
  const pointSelect = {
    selectedMode: 'multiple',
    select: {
      itemStyle: { borderColor: GOLD, borderWidth: 2, opacity: 1 },
      label: {
        show: true,
        position: 'top',
        formatter: (p) => (suppressPointLabels ? '' : p.name),
        color: GOLD,
        fontSize: 11,
        fontWeight: 600,
      },
    },
  }

  const visual = [
    {
      name: '非显著 no',
      type: 'scatter',
      data: toRaw(g.no),
      symbolSize: 4.5,
      itemStyle: { color: COLOR.no, opacity: 0.45 },
      z: 2,
      large: true,
      ...pointSelect,
    },
    {
      name: '下调 down',
      type: 'scatter',
      data: toRaw(g.down),
      symbolSize: 5.5,
      itemStyle: { color: COLOR.down, opacity: 0.85 },
      z: 3,
      ...pointSelect,
    },
    {
      name: '上调 up',
      type: 'scatter',
      data: toRaw(g.up),
      symbolSize: 5.5,
      itemStyle: { color: COLOR.up, opacity: 0.85 },
      z: 4,
      ...pointSelect,
      markLine: {
        silent: true,
        symbol: 'none',
        animation: false,
        lineStyle: { type: 'dashed', color: dim, width: 1 },
        label: { formatter: '{c}', color: dim, fontSize: 10 },
        data: [
          { xAxis: fcCut.value },
          { xAxis: -fcCut.value },
          { yAxis: thresholdY },
        ],
      },
    },
  ]

  // 视觉散点只有 ~5px，直接悬浮很难命中。每组叠一层同数据的透明大符号
  // （约 12px）专门承接鼠标事件，与视觉系列同名，图例开关联动。
  const hitArea = (name, data, z) => ({
    name,
    type: 'scatter',
    data,
    symbolSize: 12,
    itemStyle: { color: 'rgba(0,0,0,0)' },
    emphasis: { disabled: true },
    z,
  })

  const series = [
    visual[0],
    hitArea(visual[0].name, toRaw(g.no), 2),
    visual[1],
    hitArea(visual[1].name, toRaw(g.down), 3),
    visual[2],
    hitArea(visual[2].name, toRaw(g.up), 4),
  ]

  return {
    backgroundColor: 'transparent',
    animation: false,
    textStyle: { fontFamily: 'inherit' },
    legend: {
      left: 16,
      top: 14,
      data: ['上调 up', '非显著 no', '下调 down'],
      textStyle: { color: dim },
      itemWidth: 14,
      itemHeight: 9,
    },
    grid: {
      left: 80, right: 56, top: 64, bottom: 88,
      show: true, borderColor: axis, borderWidth: 1,
    },
    tooltip: {
      trigger: 'item',
      ...tooltipBase.value,
      padding: [10, 14, 12],
      borderRadius: 8,
      extraCssText: 'box-shadow: 0 6px 18px rgba(0,0,0,.18);',
      formatter: (p) => {
        const kind = kindOf(p.seriesName) ?? 'no'
        const [x, y] = p.value
        const keyColor = theme.value === 'light' ? '#6b7280' : '#98a1b5'
        const mono = 'ui-monospace, SFMono-Regular, Consolas, monospace'
        const statusText = { up: '上调 ↑', down: '下调 ↓', no: '非显著' }[kind]
        const row = (key, val) =>
          `<span style="color:${keyColor}">${key}</span>` +
          `<span style="text-align:right;font-family:${mono};font-variant-numeric:tabular-nums;">${val}</span>`
        return [
          `<div style="display:flex;align-items:center;gap:7px;font-weight:600;font-size:13px;margin-bottom:8px;">` +
            `<span style="flex:0 0 auto;width:8px;height:8px;border-radius:50%;background:${COLOR[kind]};"></span>` +
            `${p.name}</div>`,
          `<div style="display:grid;grid-template-columns:auto 1fr;column-gap:20px;row-gap:4px;">`,
          row('log2(FC)', x.toFixed(3)),
          row(yIsQval.value ? 'qval' : 'pval', p.data.q.toExponential(3)),
          row('-log10', y.toFixed(3)),
          `</div>`,
          `<div style="margin-top:9px;text-align:center;font-weight:600;font-size:12px;` +
            `color:${COLOR[kind]};background:${COLOR[kind]}26;border:1px solid ${COLOR[kind]}59;` +
            `border-radius:5px;padding:3px 0;">${statusText}</div>`,
        ].join('')
      },
    },
    toolbox: {
      right: 16,
      top: 2,
      iconStyle: { borderColor: dim },
      emphasis: { iconStyle: { borderColor: GOLD } },
      feature: {
        saveAsImage: { title: '保存图片', name: 'volcano' },
        restore: { title: '还原' },
      },
    },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0 },
      { type: 'inside', yAxisIndex: 0 },
      { type: 'slider', xAxisIndex: 0, bottom: 14, height: 16, showDetail: false },
      // 纵轴滑条：top/bottom 与 grid 对齐，保证和绘图区同高
      { type: 'slider', yAxisIndex: 0, right: 14, top: 64, bottom: 88, width: 16, showDetail: false },
    ],
    xAxis: {
      type: 'value',
      name: 'log2 of Fold change',
      nameLocation: 'center',
      nameGap: 38,
      nameTextStyle: { color: dim, fontSize: 13 },
      axisLabel: { color: dim },
      axisLine: { lineStyle: { color: axis } },
      axisTick: { show: true, lineStyle: { color: axis } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: yIsQval.value ? '-log10 of qval' : '-log10 of pval',
      nameLocation: 'center',
      nameGap: 44,
      nameTextStyle: { color: dim, fontSize: 13 },
      axisLabel: { color: dim },
      axisLine: { lineStyle: { color: axis } },
      axisTick: { show: true, lineStyle: { color: axis } },
      splitLine: { show: false },
    },
    series,
  }
}

/** 两种图表共用的 tooltip 外观。 */
const tooltipBase = computed(() => ({
  confine: true,
  backgroundColor: tooltipBg.value,
  borderColor: lineColor.value,
  textStyle: { color: tooltipInk.value, fontSize: 12 },
}))

/** 图表容器在 v-if 内，每次重建 DOM 后都要重新绑定 ECharts 实例。 */
function ensureChart() {
  const el = chartEl.value
  if (!el) return null
  if (chart && chart.dom === el) return chart
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = echarts.init(el)
  chart.on('click', onScatterClick)
  const zr = chart.getZr()
  zr.on('mousedown', onBrushDown)
  zr.on('mousemove', onBrushMove)
  zr.on('mouseup', onBrushUp)
  zr.on('globalout', onBrushUp)
  resizeObserver = new ResizeObserver(() => chart?.resize())
  resizeObserver.observe(el)
  return chart
}

function redraw() {
  const c = ensureChart()
  if (!c || !meta.value) return
  // 重绘（换数据/改阈值/换主题）后选中状态失效
  selected.value = null
  markedPoints = []
  suppressPointLabels = false
  exitBrushMode()
  c.setOption(buildOption(), { notMerge: true })
}

/* ---------- 散点 ↔ 桑基图联动 ---------- */

const VISUAL_INDEX = { no: 0, down: 2, up: 4 } // series 数组里视觉系列的下标（夹在命中层之间）

function onScatterClick(params) {
  if (brushing.value) return // 框选模式下的按下/抬起不当作点选
  if (params.componentType !== 'series') return
  const kind = kindOf(params.seriesName)
  if (!kind) return
  if (
    selected.value?.type === 'gene' &&
    selected.value.name === params.name &&
    selected.value.dataIndex === params.dataIndex
  ) {
    clearSelection()
    return
  }
  selected.value = { type: 'gene', name: params.name, kind, dataIndex: params.dataIndex }
  removeBrushShape() // 改为单点选中，之前框选留下的选框一并清除
  if (sankeyMode.value !== 'all') sankeyMode.value = 'linked'
}

/* ----- 框选绘制：自研实现——监听鼠标拖拽画矩形，convertFromPixel 换算数据坐标后
 * 自行筛点。不用 ECharts brush 组件：它会把一排刷选图标自动塞进工具条，
 * 且 brushSelected 事件的选中计算与事件时序在部分环境下不稳定。 ----- */

/** 「框选绘制」开关：再点一次或按 Esc 取消（不影响已生成的选中态）。 */
function toggleBrushSelect() {
  if (!chart) return
  if (brushing.value) exitBrushMode()
  else brushing.value = true
}

function onBrushEsc(e) {
  if (e.key === 'Escape') exitBrushMode()
}

watch(brushing, (on) => {
  if (on) window.addEventListener('keydown', onBrushEsc)
  else window.removeEventListener('keydown', onBrushEsc)
})

function onBrushDown(e) {
  if (!brushing.value) return
  removeBrushShape()
  brushStartPixel = [e.offsetX, e.offsetY]
  // 选框直接画在画布上：与鼠标事件同坐标系，保证可见
  brushShape = new ZRRect({
    shape: { x: e.offsetX, y: e.offsetY, width: 0, height: 0 },
    style: { fill: 'rgba(232,163,77,0.15)', stroke: 'rgba(232,163,77,0.9)', lineWidth: 1.5 },
    z: 1e5,
    silent: true,
  })
  chart.getZr().add(brushShape)
}

function onBrushMove(e) {
  if (!brushing.value || !brushStartPixel || !brushShape) return
  updateBrushRect(e.offsetX, e.offsetY)
}

function onBrushUp() {
  if (!brushing.value || !brushStartPixel) return
  brushing.value = false
  brushStartPixel = null
  // 选框保留在画布上，直到下一次框选/清空/重绘
  const rect = brushShape.shape
  const rectInfo = { x: rect.x, y: rect.y, w: rect.width, h: rect.height }
  if (rectInfo.w < 4 || rectInfo.h < 4) {
    removeBrushShape()
    return // 太小视为误触
  }
  if (!chart) return
  const tl = chart.convertFromPixel({ gridIndex: 0 }, [rectInfo.x, rectInfo.y])
  const br = chart.convertFromPixel({ gridIndex: 0 }, [rectInfo.x + rectInfo.w, rectInfo.y + rectInfo.h])
  const x1 = Math.min(tl[0], br[0])
  const x2 = Math.max(tl[0], br[0])
  const y1 = Math.min(tl[1], br[1])
  const y2 = Math.max(tl[1], br[1])
  const g = toRaw(groups.value)
  const names = new Set()
  for (const kind of ['up', 'down', 'no']) {
    for (const p of g[kind]) {
      const [x, y] = p.value
      if (x >= x1 && x <= x2 && y >= y1 && y <= y2) names.add(p.name)
    }
  }
  if (!names.size) return
  selected.value = { type: 'multi', names: [...names] }
  if (sankeyMode.value !== 'all') sankeyMode.value = 'linked'
}

function updateBrushRect(px, py) {
  const x = Math.min(brushStartPixel[0], px)
  const y = Math.min(brushStartPixel[1], py)
  brushShape.setShape({ x, y, width: Math.abs(px - brushStartPixel[0]), height: Math.abs(py - brushStartPixel[1]) })
}

function removeBrushShape() {
  if (brushShape) {
    chart?.getZr().remove(brushShape)
    brushShape = null
  }
}

/** 退出框选模式并移除选框（不影响已生成的选中态） */
function exitBrushMode() {
  brushing.value = false
  brushStartPixel = null
  removeBrushShape()
}

function clearSelection() {
  selected.value = null
}

function drawAllSankey() {
  exitBrushMode()
  sankeyMode.value = 'all'
}

function clearSankey() {
  exitBrushMode()
  sankeyMode.value = 'none'
  clearSelection()
}

/** 在散点数据里查这些基因名对应的点。一次遍历（框选可能给出成百上千个名字，
 * 逐名扫描全量点会明显卡顿）。 */
function findGenePoints(names) {
  const wanted = names instanceof Set ? names : new Set(names)
  const marks = []
  const g = toRaw(groups.value)
  for (const kind of ['up', 'down', 'no']) {
    const pts = g[kind]
    for (let i = 0; i < pts.length; i++) {
      if (wanted.has(pts[i].name)) marks.push({ seriesIndex: VISUAL_INDEX[kind], dataIndex: i })
    }
  }
  return marks
}

/** 选中项变化：在散点上做/撤金色标记。
 * 桑基图的高亮不走这里——linked 模式下图随选中项整体重建（见 sankeyStructKey），
 * all 模式下由单独的高亮 watcher 只改样式。 */
function syncSelection() {
  if (!chart) return
  applyPointAction('unselect', markedPoints)
  markedPoints = []
  if (!selected.value) {
    suppressPointLabels = false
    return
  }
  const names = selected.value.type === 'multi' ? selected.value.names : [selected.value.name]
  const marks = findGenePoints(names)
  suppressPointLabels = marks.length > 30
  if (marks.length > 400) marks = marks.slice(0, 400) // 逐点标记太重，多选时只标记一部分
  applyPointAction('select', marks)
  markedPoints = marks
}

watch(selected, () => nextTick(syncSelection))

/** 批量下发 select/unselect，框选大量点时避免逐点 dispatch 卡顿。
 * 注意撤销标记必须用 unselect——downplay 只作用于 emphasis 态，撤不掉 select 态。 */
function applyPointAction(type, marks) {
  if (!marks.length) return
  chart.dispatchAction({ type, batch: marks.map((m) => ({ seriesIndex: m.seriesIndex, dataIndex: m.dataIndex })) })
}

function ensureSankey() {
  const el = sankeyEl.value
  if (!el) return null
  if (sankeyChart && sankeyChart.dom === el) return sankeyChart
  sankeyResizeObserver?.disconnect()
  sankeyChart?.dispose()
  sankeyChart = echarts.init(el)
  sankeyResizeObserver = new ResizeObserver(() => sankeyChart?.resize())
  sankeyResizeObserver.observe(el)
  return sankeyChart
}

/** 按当前选中项改写桑基图节点/连线的透明度。
 * all 模式：选中节点及其邻接高亮、其余压暗；linked 模式：图本身就是选区，全部正常显示。
 * 选中节点（core）额外加金色描边 + 光晕 + 名签，密集模式下也能一眼找到；
 * 全部走样式而非 dispatch highlight，避免被后续鼠标 hover 状态冲掉。 */
function styledSankeyData({ nodes, links }) {
  const sel = selected.value
  const dim = !!sel && sankeyMode.value === 'all'
  const core = new Set()
  const active = new Set()
  if (sel) {
    const names = sel.type === 'multi' ? sel.names : [sel.name]
    names.forEach((n) => {
      core.add(n)
      active.add(n)
    })
    for (const t of sankeyData.value?.picked ?? []) {
      if (names.includes(t.gene)) t.paths.forEach((p) => active.add(p))
    }
  }
  return {
    nodes: nodes.map((n) => {
      const isCore = core.has(n.name)
      return {
        ...n,
        itemStyle: {
          ...n.itemStyle,
          opacity: !dim || active.has(n.name) ? 1 : 0.12,
          ...(isCore
            ? { borderColor: GOLD, borderWidth: 2, shadowBlur: 10, shadowColor: 'rgba(232,163,77,0.85)' }
            : {}),
        },
        label: isCore
          ? { show: true, position: n.label?.position ?? 'right', color: GOLD, fontWeight: 700, fontSize: 13 }
          : n.label,
      }
    }),
    links: links.map((l) => ({
      ...l,
      lineStyle: {
        opacity: dim
          ? active.has(l.source) && active.has(l.target)
            ? 0.4
            : 0.03
          : 0.25,
      },
    })),
  }
}

function buildSankeyOption(data) {
  const { nodes, links } = styledSankeyData(data)
  const dim = inkDim.value
  return {
    backgroundColor: 'transparent',
    animation: false,
    textStyle: { fontFamily: 'inherit' },
    tooltip: {
      ...tooltipBase.value,
      formatter: (p) => {
        if (p.dataType === 'edge') return ''
        const unit = p.data.pathway ? '个显著基因' : '条 KEGG 通路'
        return `${p.name}<br/>${p.value} ${unit}`
      },
    },
    toolbox: {
      right: 16,
      top: 2,
      iconStyle: { borderColor: dim },
      emphasis: { iconStyle: { borderColor: GOLD } },
      feature: {
        saveAsImage: { title: '保存图片', name: 'kegg-sankey' },
        restore: { title: '还原缩放' },
      },
    },
    series: [
      {
        type: 'sankey',
        roam: true, // 滚轮缩放 + 拖拽平移
        left: 110, top: 12, right: 230, bottom: 12,
        nodeWidth: 10,
        nodeGap: 5,
        nodeAlign: 'justify',
        emphasis: { focus: 'adjacency' },
        blur: { itemStyle: { opacity: 0.12 }, lineStyle: { opacity: 0.03 } },
        data: nodes,
        links,
        lineStyle: { color: 'gradient', opacity: 0.25, curveness: 0.5 },
        label: { color: dim, fontSize: 11 },
        itemStyle: { borderWidth: 0 },
      },
    ],
  }
}

function renderSankey() {
  const data = sankeyData.value
  if (!data || !data.nodes.length) {
    sankeyResizeObserver?.disconnect()
    sankeyChart?.dispose()
    sankeyChart = null
    return
  }
  const c = ensureSankey()
  if (c) c.setOption(buildSankeyOption(data), { notMerge: true })
}

/** 桑基图只在“结构性输入”变化时整体重建：绘制范围、列映射、阈值、主题，
 * 以及 linked 模式下的选中名单（它决定画哪些点）。用输入做 key，避免对整图
 * JSON.stringify 这类昂贵比对。all 模式的选中只影响高亮，不在此列。 */
const sankeyStructKey = computed(() => {
  const sel = selected.value
  const selPart =
    sankeyMode.value === 'linked' && sel
      ? sel.type === 'multi'
        ? 'm:' + sel.names.join('\u0002')
        : 'g:' + sel.name + '#' + sel.dataIndex
      : ''
  return [
    nameIdx.value, xIdx.value, yIdx.value, fcCut.value, qCut.value,
    keggIdx.value, sankeyMode.value, theme.value, selPart,
  ].join('|')
})

watch(sankeyStructKey, () => nextTick(renderSankey))

/** all 模式下选中变化只改高亮样式（merge 更新，保留缩放/平移状态） */
watch(selected, () => {
  if (sankeyMode.value === 'all' && sankeyChart && sankeyData.value) {
    nextTick(() => {
      const { nodes, links } = styledSankeyData(sankeyData.value)
      sankeyChart?.setOption({ series: [{ data: nodes, links }] })
    })
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onBrushEsc)
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = null
  sankeyResizeObserver?.disconnect()
  sankeyChart?.dispose()
  sankeyChart = null
})

watch([groups, theme], () => nextTick(redraw), { deep: false })

const truncateHint = computed(() =>
  meta.value?.truncated
    ? `数据量较大，仅绘制前 ${meta.value.maxRows.toLocaleString('zh-CN')} 行（共 ${meta.value.totalRows.toLocaleString('zh-CN')} 行）`
    : ''
)
</script>

<template>
  <div class="stack">
    <section
      v-if="!meta"
      class="panel dropzone"
      :class="{ busy, dragged }"
      role="button"
      tabindex="0"
      @click="fileInput?.click()"
      @keydown.enter="fileInput?.click()"
      @dragover.prevent="dragged = true"
      @dragleave="dragged = false"
      @drop.prevent="dragged = false; parseFile($event.dataTransfer.files?.[0])"
    >
      <input ref="fileInput" type="file" accept=".xlsx,.csv,.txt,.tsv" hidden @change="parseFile($event.target.files[0])" />
      <p class="dz-title">{{ busy ? '正在解析…' : '拖入差异表达结果表，或点击选择' }}</p>
      <p class="dz-hint">支持 xlsx / csv / txt（tsv），自动识别基因名、log2(FC)、pval/qval、KEGG 列，单文件上限 15 万行</p>
      <p class="dz-hint sample-line">
        没有数据？
        <button class="btn" :disabled="busy" @click.stop="loadSample">加载示例数据（模拟数据模板）</button>
        <a class="btn" :href="SAMPLE.url" download="volcano_demo.csv" @click.stop>下载模板文件</a>
      </p>
    </section>

    <p v-if="error" class="error-text">{{ error }}</p>

    <template v-if="meta">
      <div class="summary">
        <div class="stat panel">
          <span class="stat-num mono">{{ counts.total.toLocaleString('zh-CN') }}</span>
          <span class="stat-label">基因总数</span>
        </div>
        <div class="stat panel up-card">
          <span class="stat-num mono">{{ counts.up.toLocaleString('zh-CN') }}</span>
          <span class="stat-label">上调显著</span>
        </div>
        <div class="stat panel down-card">
          <span class="stat-num mono">{{ counts.down.toLocaleString('zh-CN') }}</span>
          <span class="stat-label">下调显著</span>
        </div>
        <div class="stat panel">
          <span class="stat-num mono">{{ counts.no.toLocaleString('zh-CN') }}</span>
          <span class="stat-label">非显著</span>
        </div>
        <div class="stat panel wide">
          <span class="stat-file">{{ meta.filename }}</span>
          <span class="stat-actions">
            <a class="btn" :href="SAMPLE.url" download="volcano_demo.csv">下载模板</a>
            <button class="btn" :disabled="busy" @click="loadSample">示例数据</button>
            <button class="btn" @click="fileInput?.click()">{{ busy ? '解析中…' : '重新上传' }}</button>
          </span>
        </div>
        <input ref="fileInput" type="file" accept=".xlsx,.csv,.txt,.tsv" hidden @change="parseFile($event.target.files[0])" />
      </div>

      <p v-if="truncateHint" class="hint">{{ truncateHint }}<span v-if="groups.skipped">；{{ groups.skipped }} 行因数值缺失/非法未绘制</span></p>

      <section class="panel controls">
        <label class="ctl">
          <span class="ctl-label">基因名列</span>
          <select v-model.number="nameIdx">
            <option v-for="(c, i) in meta.columns" :key="i" :value="i">{{ c }}</option>
          </select>
        </label>
        <label class="ctl">
          <span class="ctl-label">横轴列（log2FC 或 FC）</span>
          <select v-model.number="xIdx">
            <option v-for="(c, i) in meta.columns" :key="i" :value="i">{{ c }}</option>
          </select>
        </label>
        <label class="ctl">
          <span class="ctl-label">纵轴列（qval / pval）</span>
          <select v-model.number="yIdx">
            <option v-for="(c, i) in meta.columns" :key="i" :value="i">{{ c }}</option>
          </select>
        </label>
        <label class="ctl">
          <span class="ctl-label">KEGG 列（桑基图，可无）</span>
          <select v-model.number="keggIdx">
            <option :value="-1">无</option>
            <option v-for="(c, i) in meta.columns" :key="i" :value="i">{{ c }}</option>
          </select>
        </label>
        <label class="ctl">
          <span class="ctl-label">|log2FC| ≥</span>
          <input v-model.number="fcCut" type="number" min="0" step="0.1" />
        </label>
        <label class="ctl">
          <span class="ctl-label">q 值 ≤</span>
          <input v-model.number="qCut" type="number" min="0" step="0.01" />
        </label>
      </section>

      <section class="panel chart-panel">
        <div ref="chartEl" class="chart" :class="{ brushing }"></div>
      </section>

      <section v-if="keggIdx >= 0" class="panel chart-panel">
        <p class="sankey-hint">
          <span>基因 → KEGG 通路桑基图 · {{ sankeyHint }} · 点击散点图基因点联动高亮，再次点击同一节点或「清空」取消</span>
          <span class="sankey-actions">
            <button
              class="btn"
              :class="{ active: brushing }"
              :title="brushing ? '再点一次或按 Esc 取消框选' : '拖拽框选一片基因点，绘制相关子图'"
              @click="toggleBrushSelect"
            >框选绘制</button>
            <button class="btn" @click="drawAllSankey">绘制全部</button>
            <button class="btn" @click="clearSankey">清空</button>
          </span>
        </p>
        <div v-if="sankeyData" ref="sankeyEl" class="chart sankey-chart"></div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dropzone {
  border-style: dashed;
  border-width: 1.5px;
  border-color: var(--line-strong);
  text-align: center;
  padding: 60px 20px;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.dropzone:hover,
.dropzone:focus-visible,
.dropzone.dragged {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.dz-title {
  margin: 0;
  font-weight: 600;
  font-size: 15.5px;
}

.dz-hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--ink-faint);
}

.sample-line {
  margin-top: 18px;
  display: flex;
  gap: 10px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
}

.error-text {
  margin: 0;
  color: var(--danger);
  font-size: 13.5px;
}

.hint {
  margin: 0;
  color: var(--ink-faint);
  font-size: 13px;
}

.summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr) 2fr;
  gap: 12px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 16px;
}

.stat-num {
  font-size: 24px;
  font-weight: 650;
  color: var(--ink-dim);
}

.up-card .stat-num {
  color: #e0524f;
}

.down-card .stat-num {
  color: #3f7fd9;
}

.stat-label {
  font-size: 12.5px;
  color: var(--ink-dim);
}

.stat.wide {
  justify-content: space-between;
}

.stat-file {
  font-family: var(--font-mono);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: auto;
}

.stat-actions .btn {
  padding: 7px 4px;
  font-size: 13px;
  white-space: nowrap;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 14px 22px;
  align-items: flex-end;
}

.ctl {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 0 0 auto;
  max-width: 100%;
}

.ctl-label {
  font-size: 12px;
  color: var(--ink-faint);
}

.ctl select,
.ctl input {
  background: var(--panel-2);
  color: var(--ink);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  font-size: 13px;
  font-family: inherit;
  width: 240px;
  min-width: 0;
  max-width: 100%;
}

.ctl select:focus,
.ctl input:focus {
  outline: none;
  border-color: var(--accent);
}

.ctl input[type='number'] {
  width: 96px;
}

.chart-panel {
  padding: 6px;
}

.chart {
  width: 100%;
  height: 560px;
}

.chart.brushing {
  cursor: crosshair;
}

.sankey-chart {
  height: 660px;
}

.sankey-hint {
  margin: 10px 12px 0;
  font-size: 12.5px;
  color: var(--ink-faint);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.sankey-actions {
  display: flex;
  gap: 8px;
  flex: 0 0 auto;
}

.sankey-actions .btn {
  padding: 4px 12px;
  font-size: 12.5px;
}

.sankey-actions .btn.active {
  border-color: var(--accent);
  color: var(--accent);
}

@media (max-width: 900px) {
  .summary {
    grid-template-columns: 1fr 1fr;
  }

  .stat.wide {
    grid-column: 1 / -1;
  }

  .chart {
    height: 420px;
  }

  .sankey-chart {
    height: 480px;
  }
}
</style>
