"""后端工具的定义与注册。

新增一个后端工具只需两步：
1. 在 app/tools/ 下新建模块，模块级暴露 TOOL（ToolDefinition）和 router（APIRouter）；
2. 完成。registry 会自动发现并挂载到 /api/tools/<prefix> 下。
"""
from dataclasses import dataclass

from fastapi import APIRouter


@dataclass
class ToolDefinition:
    """后端工具的元数据，用于 /api/tools 列表与前端展示。"""

    id: str                # 全局唯一，需与前端工具目录名一致
    name: str              # 展示名
    description: str       # 一句话描述
    version: str = "1.0.0"


def tool_router(tool_id: str, tag: str | None = None) -> APIRouter:
    """为工具创建统一前缀的路由：/api/tools/<tool_id>。"""
    return APIRouter(prefix=f"/tools/{tool_id}", tags=[tag or tool_id])
