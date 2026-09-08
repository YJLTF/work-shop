# WorkShop · 个人工具箱

一个自用的常用工具收集面板：首页是工具卡片墙，支持分类标签筛选与模糊搜索，点击卡片进入对应工具页。
后端 Python（FastAPI），为将来的复杂数据分析预留能力；前端 Vue 3，界面现代美观；可打包为单个 exe，绿色便携、离线可用。

## 功能一览

- **工具卡片墙**：卡片按分类着色（文本处理 / 开发辅助 / 数据分析 / 生信 / 日常效率），悬停有动效
- **分类筛选 + 模糊搜索**：支持中文名、英文 id、关键词、甚至拼音（如输入 `shi jian` 命中「时间戳转换」），按 `/` 键快速聚焦搜索框
- **深色 / 浅色主题**：一键切换，自动记忆
- **打包版页面退出按钮**：打包成 exe 后页面右上角可优雅退出本地服务
- **内置 7 件工具**：

| 工具 | 分类 | 运行位置 | 说明 |
|------|------|----------|------|
| JSON 格式化 | 文本处理 | 前端 | 格式化 / 压缩 / 校验，错误定位到行列 |
| 正则测试 | 文本处理 | Python | re 引擎实时匹配、分组捕获、批量替换 |
| 哈希计算 | 开发辅助 | Python | 文本与文件 MD5/SHA 系列摘要，大文件流式处理 |
| UUID 生成 | 开发辅助 | 前端 | 批量 UUID v4，大小写 / 连字符 / 花括号选项 |
| 时间戳转换 | 日常效率 | 前端 | 双向转换，秒/毫秒自动识别，本地时区 |
| CSV 统计 | 数据分析 | Python | 行列概况、数值列统计摘要、数据预览 |
| 差异基因分析 | 生信 | Python + 前端 | 上传 xlsx/csv/txt 差异表达表，ECharts 交互式火山图（红=上调、蓝=下调、灰=非显著），阈值与列映射可调，横纵轴均可缩放；识别 KEGG 列后可绘制基因→通路桑基图：点击散点或「框选绘制」一片即联动绘制相关子图（含绘制全部/清空、滚轮缩放），密集时自动隐藏名签；内置随机模拟数据模板可下载 |

## 目录结构

```
work-shop/
├── backend/                 # Python 后端（虚拟环境 .venv/）
│   ├── run.py               # 启动器：起服务 + 自动开浏览器（也是 exe 入口）
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI 装配：/api 路由 + 前端静态资源托管
│       ├── core/
│       │   ├── config.py    # 端口 / 路径 / frozen 判定
│       │   └── registry.py  # 工具注册表：自动发现 app/tools 下的模块
│       └── tools/           # ★ 后端工具：一个 .py 文件 = 一件工具
│           ├── base.py      #     ToolDefinition 与路由工厂
│           ├── regex_tool.py
│           ├── hash_tool.py
│           ├── csv_tool.py
│           └── volcano_tool.py   # 火山图：标准库解析 xlsx/csv/txt
├── frontend/                # Vue 3 + Vite 前端
│   └── src/
│       ├── views/           # HomeView（卡片墙）/ ToolView（工具宿主）
│       ├── components/      # ToolCard、SearchBar、CategoryChips、PageShell…
│       ├── composables/     # useFuzzySearch、useTheme
│       └── tools/           # ★ 前端工具：一个文件夹 = 一件工具
│           ├── registry.js  #     import.meta.glob 自动收集，无需登记
│           ├── json-formatter/{tool.js, ToolJsonFormatter.vue}
│           ├── regex/ …
│           ├── csv-stats/ …
│           └── volcano/ …   #     tool.js + ToolVolcano.vue + analysis.js（纯数据层：
│                               分组/KEGG 解析/桑基图组装，不依赖 Vue 与 ECharts），
│                               ECharts 按需引入，public/sample/ 为模拟数据模板（CSV，带 BOM）
├── scripts/
│   ├── build_exe.py         # PyInstaller 打包（onefile / onedir）
│   ├── make_icon.py         # 生成应用图标与启动占位图
│   ├── make_demo_csv.py     # 生成火山图示例数据模板（随机模拟数据，CSV 体积更小）
│   └── build.bat
├── dev.bat                  # 开发模式（后端 + Vite 热更新）
├── start.bat                # 免打包直接运行完整站点
└── dist/                    # 打包产物 WorkShop.exe
```

## 快速开始

环境要求：Python 3.10+ 与 Node.js 18+。

```bash
# 1. 创建虚拟环境并安装后端依赖
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt

# 2. 安装前端依赖并构建（构建产物会同步到 backend/app/static）
cd frontend && npm install && npm run build && cd ..

# 3. 运行（自动打开浏览器，默认 http://127.0.0.1:8321）
.venv/Scripts/python backend/run.py
```

日常开发用 `dev.bat`（后端 8321 + Vite 5173 热更新，`/api` 自动代理）；
只想像打包版一样跑已构建的页面，双击 `start.bat`。

## 打包为 exe

```bash
.venv/Scripts/python scripts/build_exe.py            # 单文件 WorkShop.exe（约 16 MB）
.venv/Scripts/python scripts/build_exe.py --onedir   # 目录版：启动快约一半（约 2 秒内）
```

| 模式 | 体积 | 冷启动 | 特点 |
|------|------|--------|------|
| onefile（默认） | ~16 MB | ~4 s | 单文件、好分发，每次启动需解压到临时目录 |
| onedir | ~30 MB 文件夹（主程序 4 MB） | ~2 s | 启动快、无解压，适合本机固定使用 |

双击 exe 后不再「干等」：打包带 `--splash` 启动占位图（黄铜底 W 字标 +「正在启动」），
解压与导入阶段（约 1~2 秒）就会显示，服务就绪后由 `run.py` 自动关闭并打开浏览器。
占位图由 `make_icon.py` 一并生成（`build/splash.png`），改风格只需重跑该脚本。

体积与速度优化手段：运行时依赖刻意精简（FastAPI + uvicorn，未引入 pandas/numpy 前不会进包）；
剔除 tkinter、setuptools、bz2/lzma 等无关模块（zip 的冷门压缩后端，xlsx 用不到）；
默认不用 UPX（压缩收益小且易触发杀软误报）。
进一步压体积的选项（未启用，按需取舍）：UPX 约 -30%；剔除 unicodedata（-419 KB）会破坏
正则工具的 `\N{…}` 命名转义与错误栈显示，不建议。
打包后的程序完全离线运行，数据不出机器；退出可在页面右上角点电源按钮。

常见打包问题：
- **报错「拒绝访问 dist\WorkShop.exe」**：旧的 WorkShop.exe 还在运行锁住了文件，先结束进程再打包；
- **双击 exe 闪退/无响应**：本项目的启动器已处理无控制台环境（stdout/stderr 为 None），
  若自行改造入口代码，注意不要在 `--noconsole` 模式下依赖标准流。

批处理脚本（dev.bat / start.bat / scripts\build.bat）约定：**只写 ASCII 字符并以 CRLF 换行保存**。
cmd.exe 按 ANSI 代码页解码批处理，含中文（无论 UTF-8 还是 GBK 保存）都可能把命令从中间截断，
报「'te' 不是内部或外部命令」之类的错；中文说明请写在 README 或代码注释里。

> AI 编码助手的工作约定（构建验证流程、代码规范、数据红线）见 [AGENTS.md](AGENTS.md)。

## 如何新增一件工具

前端（必做，卡片与页面）——在 `frontend/src/tools/` 建一个文件夹：

```
my-tool/
├── tool.js      # 元数据：id、名称、描述、分类、关键词、图标、组件懒加载
└── ToolMyTool.vue   # 工具组件，页面外壳由 PageShell 统一提供
```

```js
export default {
  id: 'my-tool',
  name: '我的工具',
  description: '一句话描述',
  category: 'dev',            // text / dev / data / bio / quick
  icon: 'hash',               // 见 src/tools/icons.js
  keywords: ['my', 'tool', '工具', 'pinyin'],
  backend: false,             // 为 true 时卡片显示 Python 徽标
  component: () => import('./ToolMyTool.vue'),
}
```

完成。注册表通过 `import.meta.glob` 自动收集，刷新即可看到新卡片。

后端（可选，需要 Python 计算能力时）——在 `backend/app/tools/` 建一个模块：

```python
from pydantic import BaseModel
from app.tools.base import ToolDefinition, tool_router

TOOL = ToolDefinition(id="my-tool", name="我的工具", description="…")
router = tool_router(TOOL.id)      # 自动挂在 /api/tools/my-tool 下

class Req(BaseModel):
    text: str

@router.post("/run")
def run(req: Req):
    return {"result": req.text.upper()}
```

前端组件里用 `api.post('/tools/my-tool/run', { text })` 调用即可（`src/api.js`）。
重新打包时脚本会自动扫描并收录新模块，无需改打包配置。

## 设计说明

视觉概念是「工具墙」：深色工坊里的洞洞板（背景圆点纹理），每类工具有一个「手柄色」，
卡片图标是黄铜色系色板上的线性图标；全部资源本地化（系统字体 + 内联 SVG），无任何 CDN 依赖。
API 文档在打包/开发模式下均可用：`http://127.0.0.1:8321/api/docs`。
