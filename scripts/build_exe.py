"""WorkShop 打包脚本：把前端产物与 FastAPI 后端打成单个 Windows exe。

用法（在项目根目录）:
    .venv/Scripts/python scripts/build_exe.py            # 单文件模式（默认）
    .venv/Scripts/python scripts/build_exe.py --onedir   # 目录模式：启动更快

体积与速度优化手段：
- 只声明真实用到的运行时依赖，未安装的重型库（pandas 等）不会进包
- --exclude-module 剔除无关标准库
- 默认不开 UPX：压缩率有限且容易触发杀软误报（如需可自行加 --upx-dir）
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
STATIC = BACKEND / "app" / "static"
DIST = ROOT / "dist"
BUILD = ROOT / "build" / "pyinstaller"
ICON = ROOT / "build" / "icon.ico"
SPLASH = ROOT / "build" / "splash.png"

EXCLUDES = [
    "tkinter",
    "setuptools",
    "pkg_resources",
    "pydoc_data",
    "unittest",
    "sqlite3",
    "curses",
    "xmlrpc",
    # zipfile 的可选压缩后端，xlsx（deflate）用不到；保留会使 _bz2/_lzma 进包
    "bz2",
    "lzma",
]


def ensure_frontend() -> None:
    dist = ROOT / "frontend" / "dist"
    if not (dist / "index.html").exists():
        print("[build] 未找到前端产物，先构建前端…")
        npm = shutil.which("npm")
        if not npm:
            sys.exit("未找到 npm，请先手动执行: cd frontend && npm run build")
        subprocess.run([npm, "run", "build"], cwd=ROOT / "frontend", check=True)
    # 全量镜像，清掉历史构建残留的旧 hash 资源，避免无用文件进包
    if STATIC.exists():
        shutil.rmtree(STATIC)
    shutil.copytree(dist, STATIC)
    print(f"[sync] 前端产物已同步: {STATIC}")


def tool_modules() -> list[str]:
    """扫描 app/tools 下的工具模块（排除基础设施文件）。"""
    skip = {"__init__.py", "base.py"}
    return sorted(
        p.stem
        for p in (BACKEND / "app" / "tools").glob("*.py")
        if p.name not in skip and not p.name.startswith("_")
    )


def write_frozen_manifest(modules: list[str]) -> None:
    """生成冻结环境下的模块清单：打包后 pkgutil 无法枚举 PYZ 内的模块。"""
    manifest = BACKEND / "app" / "tools" / "_frozen_tools.py"
    manifest.write_text(
        "# 由 scripts/build_exe.py 自动生成，请勿手工修改。\n"
        f"MODULES = {modules!r}\n",
        encoding="utf-8",
    )
    print(f"[build] 工具清单: {manifest} -> {modules}")


def build(mode: str) -> Path:
    modules = tool_modules()
    write_frozen_manifest(modules)

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        f"--{mode}",
        "--noconsole",
        "--name",
        "WorkShop",
        "--icon",
        str(ICON),
        # 双击后立即显示的启动占位图（覆盖解压与导入阶段），服务就绪后由 run.py 调 pyi_splash.close()
        "--splash",
        str(SPLASH),
        "--distpath",
        str(DIST),
        "--workpath",
        str(BUILD),
        "--specpath",
        str(BUILD),
        "--paths",
        str(BACKEND),
        "--add-data",
        f"{STATIC};app/static",
    ]
    # 工具模块通过字符串动态导入，必须显式声明，否则不会被打进包
    for name in modules:
        args += ["--hiddenimport", f"app.tools.{name}"]
    for module in EXCLUDES:
        args += ["--exclude-module", module]
    args.append(str(BACKEND / "run.py"))

    print("[build] PyInstaller 打包中…")
    subprocess.run(args, check=True)

    if mode == "onefile":
        out = DIST / "WorkShop.exe"
    else:
        out = DIST / "WorkShop" / "WorkShop.exe"
    if not out.exists():
        sys.exit(f"打包似乎未产出 {out}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--onedir", action="store_true", help="目录模式（启动更快，产物为文件夹）")
    args = parser.parse_args()

    if not ICON.exists() or not SPLASH.exists():
        print("[build] 缺少图标或启动占位图，先生成…")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_icon.py")], check=True)

    ensure_frontend()
    out = build("onedir" if args.onedir else "onefile")

    size_mb = out.stat().st_size / 1024 / 1024
    print(f"\n打包完成: {out}  ({size_mb:.1f} MB)")
    print("双击运行即可自动打开浏览器。退出可在页面右上角点电源按钮。")


if __name__ == "__main__":
    main()
