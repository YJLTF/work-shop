"""正则测试工具：用 Python re 引擎匹配/替换，演示前后端协作型工具。"""
import re

from fastapi import HTTPException
from pydantic import BaseModel

from app.tools.base import ToolDefinition, tool_router

TOOL = ToolDefinition(
    id="regex",
    name="正则测试",
    description="基于 Python re 引擎的匹配测试、分组捕获与批量替换",
)

router = tool_router(TOOL.id)

FLAG_MAP = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL, "x": re.VERBOSE}
MAX_MATCHES = 1000


class MatchRequest(BaseModel):
    pattern: str
    text: str
    flags: list[str] = []
    replace: str | None = None  # 提供时返回替换结果


@router.post("/match")
def match(req: MatchRequest):
    flag = 0
    for ch in req.flags:
        if ch not in FLAG_MAP:
            raise HTTPException(422, detail=f"不支持的标志: {ch}")
        flag |= FLAG_MAP[ch]

    try:
        compiled = re.compile(req.pattern, flag)
    except re.error as exc:
        raise HTTPException(422, detail=f"正则表达式错误：{exc}") from exc

    matches = []
    for m in compiled.finditer(req.text):
        matches.append(
            {
                "match": m.group(0),
                "start": m.start(),
                "end": m.end(),
                "groups": list(m.groups()),
                "named": m.groupdict(),
            }
        )
        if len(matches) >= MAX_MATCHES:
            break

    result = {"count": len(matches), "truncated": len(matches) >= MAX_MATCHES, "matches": matches}
    if req.replace is not None:
        try:
            result["replaced"] = compiled.sub(req.replace, req.text)
        except re.error as exc:
            raise HTTPException(422, detail=f"替换模板错误：{exc}") from exc
    return result
