"""哈希计算工具：文本与文件（流式分块）的 MD5 / SHA 系列摘要。"""
import hashlib

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel

from app.tools.base import ToolDefinition, tool_router

TOOL = ToolDefinition(
    id="hash",
    name="哈希计算",
    description="计算文本或文件的 MD5、SHA-1、SHA-256 等摘要，支持大文件流式处理",
)

router = tool_router(TOOL.id)

ALGORITHMS = ("md5", "sha1", "sha256", "sha512")
CHUNK_SIZE = 1024 * 1024  # 1MB，避免大文件占用内存


def _validate(algorithms: list[str]) -> list[str]:
    picked = [a for a in algorithms if a in ALGORITHMS] or ["md5", "sha256"]
    return picked


def _digests(hashes: dict) -> dict:
    return {name: h.hexdigest() for name, h in hashes.items()}


class TextRequest(BaseModel):
    text: str
    algorithms: list[str] = ["md5", "sha1", "sha256", "sha512"]


@router.post("/text")
def hash_text(req: TextRequest):
    hashes = {name: hashlib.new(name) for name in _validate(req.algorithms)}
    data = req.text.encode("utf-8")
    for h in hashes.values():
        h.update(data)
    return {"kind": "text", "length": len(data), "digests": _digests(hashes)}


@router.post("/file")
async def hash_file(file: UploadFile, algorithms: str = "md5,sha1,sha256,sha512"):
    picked = _validate([a.strip() for a in algorithms.split(",") if a.strip()])
    hashes = {name: hashlib.new(name) for name in picked}
    size = 0
    while chunk := await file.read(CHUNK_SIZE):
        size += len(chunk)
        for h in hashes.values():
            h.update(chunk)
    return {
        "kind": "file",
        "filename": file.filename or "unnamed",
        "size": size,
        "digests": _digests(hashes),
    }
