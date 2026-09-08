# AGENTS.md · AI 编码助手工作约定

本项目是个人工具箱（Vue 3 + Vite 前端，FastAPI 后端，可 PyInstaller 打包为单 exe）。
AI 助手在此仓库工作时请遵循以下约定，README.md 侧重使用说明，这里侧重开发与验证规范。

## 常用命令

```bash
# 后端（在仓库根目录）
.venv/Scripts/python backend/run.py                # 起服务 + 自动开浏览器，默认 127.0.0.1:8321

# 前端
cd frontend && npm run build                       # 构建到 frontend/dist

# 构建产物同步（改完前端必须做，start.bat / 打包版跑的是 backend/app/static）
rm -rf backend/app/static/assets backend/app/static/index.html
cp -r frontend/dist/. backend/app/static/

# 开发模式热更新（无需同步 static）
dev.bat                                            # 后端 8321 + Vite 5173，/api 自动代理
```

- 用户可能自己开着一个 8321 的旧实例。**验证时用环境变量换端口**：
  `WORKSHOP_NO_BROWSER=1 WORKSHOP_PORT=8399 python backend/run.py`（后台运行，测完停掉）。
- 后端依赖刻意精简（FastAPI + uvicorn，xlsx 用标准库 zipfile + ElementTree 解析）。
  **不要引入 pandas / openpyxl / numpy** 等重依赖，会显著增大打包体积。

## 代码规范

- 前端工具一个文件夹 = 一件工具（`frontend/src/tools/<id>/`）：`tool.js` 元数据 +
  `Tool*.vue` 组件，注册表用 `import.meta.glob` 自动收集，无需登记。
- ECharts 一律按需引入（`echarts/core` + `echarts.use`），不要整包 import。
- 复杂工具把**纯数据逻辑抽到独立模块**（如 volcano/analysis.js），不依赖 Vue / ECharts / DOM，
  组件只留交互与渲染胶水。
- 批处理脚本（dev.bat / start.bat / scripts\build.bat）**只写 ASCII 字符并以 CRLF 换行保存**；
  含中文（UTF-8 或 GBK）会被 cmd.exe 从命令中间截断，报「'te' 不是内部或外部命令」类错误。
- UI 文案用中文；代码注释解释「为什么」，不复述「做什么」。
- 后端工具一个模块 = 一件工具（`backend/app/tools/<id>_tool.py`），用 `ToolDefinition` +
  `tool_router` 挂到 `/api/tools/<id>` 下。

## 数据红线

- **不要把用户的真实数据留在仓库里**。用户上传的原始文件（如根目录的
  PY_CR200VSPY_CR0_Gene_differential_expression.xlsx）属于用户自己，不得复制进代码、
  示例或 static；测试用临时子集用完即删。
- 示例数据一律用 `scripts/make_demo_csv.py` 生成的随机模拟数据。

## 验证流程（改完前端/后端必做）

1. `cd frontend && npm run build` —— 有编译错误先修；
2. 同步 `frontend/dist` → `backend/app/static`（命令见上）；
3. 换端口后台起服务，浏览器或 curl 冒烟验证核心交互（例：火山图点击/框选/绘制全部/清空、
   主题切换重绘）；
4. 测完停掉服务、关闭测试标签页，清理临时文件，不留后台进程。

## 已知坑（踩过的坑，勿重复踩）

- **cmd 批处理**：见上，ASCII + CRLF 是硬约束。
- **ECharts brush 组件**会把一排刷选图标自动塞进 toolbox 且 `brushSelected` 时序不稳，
  框选用自研 zr 鼠标事件 + `convertFromPixel` 实现（见 ToolVolcano.vue）。
- **select 态标记的撤销必须用 `unselect`**（批量 dispatch），`downplay` 只作用于 emphasis。
- sankey 的 label 加 backgroundColor/padding 等富文本属性会导致渲染崩溃，只改简单样式。
- 数千点的选中要**批量 dispatch**（`batch`）且封顶（当前 400 个），逐点 dispatch 会冻结页面。
