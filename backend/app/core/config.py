"""全局配置：路径、端口、运行模式。

打包成 exe 后（frozen 模式）可执行文件所在目录即工作目录，
数据文件写在 exe 旁的 data/ 目录，保持绿色便携。
"""
import os
import sys
from pathlib import Path

APP_NAME = "WorkShop"
APP_VERSION = "1.1.0"


def is_frozen() -> bool:
    """是否运行在 PyInstaller 打包环境中。"""
    return getattr(sys, "frozen", False)


def app_root() -> Path:
    """应用根目录：打包后为 exe 所在目录，开发时为项目根目录。"""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def static_dir() -> Path:
    """前端构建产物目录（随 exe 打包）。"""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", ".")) / "app" / "static"
    return Path(__file__).resolve().parents[1] / "static"


def data_dir() -> Path:
    """持久化数据目录，供未来数据分析类工具存放结果。"""
    d = app_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def default_port() -> int:
    return int(os.environ.get("WORKSHOP_PORT", "8321"))
