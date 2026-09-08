"""工具注册表：自动发现 app/tools/ 下的工具模块。

约定优于配置：模块内暴露 TOOL 与 router 即完成注册，
无需在别处手工登记，保证高内聚低耦合。
"""
import importlib
import pkgutil

import app.tools as tools_pkg


def _module_names() -> list[str]:
    """枚举工具模块名：开发模式走文件系统；打包模式下 PYZ 无法枚举，
    回退到构建时由 scripts/build_exe.py 生成的 _frozen_tools.py 清单。"""
    found = [
        mod_info.name
        for mod_info in pkgutil.iter_modules(tools_pkg.__path__)
        if not mod_info.name.startswith("_")
    ]
    if found:
        return found
    try:
        from app.tools._frozen_tools import MODULES

        return list(MODULES)
    except ImportError:
        return []


def discover() -> tuple[list, list]:
    """扫描工具包，返回 (ToolDefinition 列表, APIRouter 列表)。"""
    tools, routers = [], []
    for name in _module_names():
        module = importlib.import_module(f"{tools_pkg.__name__}.{name}")
        tool = getattr(module, "TOOL", None)
        router = getattr(module, "router", None)
        if tool is not None:
            tools.append(tool)
        if router is not None:
            routers.append(router)
    tools.sort(key=lambda t: t.id)
    return tools, routers
