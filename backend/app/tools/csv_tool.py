"""CSV 快速统计工具：纯标准库实现的列级统计，预留数据分析能力的样板。

未来引入 pandas / numpy 后，在此模式下扩展更复杂的分析逻辑即可，
依赖的增加只会影响该工具模块与打包体积，不影响面板框架。
"""
import csv
import io
import statistics

from fastapi import HTTPException, UploadFile

from app.tools.base import ToolDefinition, tool_router

TOOL = ToolDefinition(
    id="csv-stats",
    name="CSV 统计",
    description="上传 CSV 快速获得行列概况与数值列的统计摘要",
)

router = tool_router(TOOL.id)

MAX_ROWS = 200_000
PREVIEW_ROWS = 8


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "gbk", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(422, detail="无法识别文件编码，请使用 UTF-8 或 GBK")


def _is_number(value: str) -> bool:
    if value is None or value == "":
        return False
    try:
        float(value)
        return True
    except ValueError:
        return False


@router.post("/stats")
async def csv_stats(file: UploadFile):
    raw = await file.read()
    text = _decode(raw)

    try:
        sample = text[:4096]
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        class dialect:  # 嗅探失败时退回逗号
            delimiter = ","

    rows = list(csv.reader(io.StringIO(text), dialect))
    rows = [r for r in rows if any(cell.strip() for cell in r)]
    if not rows:
        raise HTTPException(422, detail="文件中没有有效数据行")

    if len(rows) > MAX_ROWS:
        raise HTTPException(422, detail=f"行数超过上限 {MAX_ROWS:,}，请先拆分文件")

    header, body = rows[0], rows[1:]
    width = len(header)

    columns = []
    for col in range(width):
        values = [row[col] if col < len(row) else "" for row in body]
        non_empty = [v for v in values if v.strip() != ""]
        numeric = [float(v) for v in non_empty if _is_number(v)]
        numeric_ratio = len(numeric) / len(non_empty) if non_empty else 0

        entry = {
            "name": header[col].strip() or f"列{col + 1}",
            "type": "number" if non_empty and numeric_ratio >= 0.9 else "text",
            "total": len(values),
            "missing": len(values) - len(non_empty),
        }
        if entry["type"] == "number" and numeric:
            entry["stats"] = {
                "min": min(numeric),
                "max": max(numeric),
                "mean": round(statistics.fmean(numeric), 4),
                "median": round(statistics.median(numeric), 4),
                "stdev": round(statistics.stdev(numeric), 4) if len(numeric) > 1 else 0.0,
            }
        else:
            distinct = {v for v in non_empty}
            entry["stats"] = {
                "distinct": len(distinct),
                "top": max(distinct, key=lambda v: non_empty.count(v)) if distinct else None,
            }
        columns.append(entry)

    return {
        "filename": file.filename or "unnamed.csv",
        "rows": len(body),
        "cols": width,
        "columns": columns,
        "preview": [r[:width] for r in body[:PREVIEW_ROWS]],
    }
