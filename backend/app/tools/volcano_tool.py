"""差异基因分析工具：解析差异表达分析结果表，返回绘图所需的数据点。

支持 xlsx / csv / txt（tsv 等），全部用标准库实现（zipfile + ElementTree 解析
xlsx），不引入 pandas / openpyxl，保持打包体积精简。列的语义匹配在前端可调，
后端只负责读表、数值化与一套启发式默认列识别。
"""
import csv
import io
import math
import re
import zipfile
from xml.etree import ElementTree as ET

from fastapi import HTTPException, UploadFile

from app.tools.base import ToolDefinition, tool_router

TOOL = ToolDefinition(
    id="volcano",
    name="差异基因分析",
    description="上传差异表达结果表（xlsx/csv/txt），交互式火山图展示上调/下调/非显著基因分布",
)

router = tool_router(TOOL.id)

MAX_ROWS = 150_000

_MISSING = {"", "na", "n/a", "nan", "none", "null", "-", "--", "."}

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "gbk", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(422, detail="无法识别文件编码，请使用 UTF-8 或 GBK")


def _cell_str(value: str | None) -> str | None:
    """空值/NA 归一为 None，其余保留原文本。"""
    if value is None:
        return None
    text = value.strip()
    return None if text.lower() in _MISSING else text


def _as_number(text: str | None) -> float | None:
    if text is None:
        return None
    try:
        value = float(text.replace(",", ""))
    except ValueError:
        return None
    return None if math.isnan(value) or math.isinf(value) else value


def _col_index(ref: str) -> int:
    """'BC12' -> 列号（0 基）。"""
    letters = re.match(r"[A-Z]+", ref.upper())
    index = 0
    for ch in letters.group():
        index = index * 26 + (ord(ch) - 64)
    return index - 1


def _parse_xlsx(raw: bytes) -> list[list[str | None]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        raise HTTPException(422, detail="xlsx 文件已损坏，无法解析")

    shared: list[str] = []
    if "xl/sharedStrings.xml" in archive.namelist():
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        for si in root.findall(f"{NS}si"):
            shared.append("".join(t.text or "" for t in si.iter(f"{NS}t")))

    sheets = sorted(n for n in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))
    if not sheets:
        raise HTTPException(422, detail="xlsx 中没有找到工作表")
    sheet = ET.fromstring(archive.read(sheets[0]))

    rows: list[list[str | None]] = []
    for row in sheet.iter(f"{NS}row"):
        values: dict[int, str | None] = {}
        for cell in row:
            ref = cell.get("r")
            if ref is None:
                continue
            col = _col_index(ref)
            v = cell.find(f"{NS}v")
            if cell.get("t") == "s" and v is not None:
                values[col] = shared[int(v.text)]
            elif cell.get("t") == "inlineStr":
                values[col] = "".join(t.text or "" for t in cell.iter(f"{NS}t"))
            elif v is not None:
                values[col] = v.text
        if values:
            width = max(values) + 1
            rows.append([_cell_str(values.get(i)) for i in range(width)])
    return rows


def _parse_delimited(raw: bytes, filename: str) -> list[list[str | None]]:
    text = _decode(raw)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        class dialect:  # 嗅探失败时按扩展名退回
            delimiter = "\t" if filename.lower().endswith((".txt", ".tsv")) else ","

    rows = [
        [_cell_str(cell) for cell in row]
        for row in csv.reader(io.StringIO(text), dialect)
    ]
    return [row for row in rows if any(cell is not None for cell in row)]


def _match(header: list[str], patterns: list[str]) -> int | None:
    """按优先级在表头里找列名（小写包含匹配）。"""
    lowered = [h.lower().replace(" ", "").replace("_", "").replace("-", "").replace(".", "") for h in header]
    for pattern in patterns:
        for i, name in enumerate(lowered):
            if pattern in name:
                return i
    return None


def _detect_columns(header: list[str], rows: list[list[str | None]]) -> dict:
    n = len(header)

    name = _match(header, ["genename", "geneid", "gene", "symbol", "id", "name"])
    if name is None:  # 退回第一个以文本为主的列
        for i in range(n):
            sample = [r[i] for r in rows[:50] if i < len(r) and r[i] is not None]
            if sample and sum(1 for v in sample if _as_number(v) is None) / len(sample) > 0.8:
                name = i
                break
    name = 0 if name is None else name

    # 列名在 _match 里已做小写与去符号归一，模式串写最简形态即可：
    # q-value/q_value 都归一成 qvalue，p-value/p_value 同理
    log2fc = _match(header, ["log2fc", "log2foldchange", "log2(fc)"])
    # 没有现成 log2FC 列时，退而求其次找原始 FC 列（或任何含 log2 的列）作横轴
    fc = (
        _match(header, ["foldchange", "fc"])
        if log2fc is not None
        else _match(header, ["log2", "foldchange", "fc"])
    )

    qval = _match(header, ["qval", "qvalue", "padj", "fdr"])
    pval = _match(header, ["pval", "pvalue"])
    if qval is None and pval is not None:
        qval, pval = pval, None  # 只有 p 值列：直接把它当纵轴用

    regulation = _match(header, ["regulation", "regulate", "updown", "change_type"])
    significant = _match(header, ["significant", "sig"])
    kegg = _match(header, ["kegg", "pathway", "通路"])

    return {
        "name": name,
        "log2fc": log2fc,
        "fc": fc,
        "qval": qval,
        "pval": pval,
        "regulation": regulation,
        "significant": significant,
        "kegg": kegg,
    }


@router.post("/parse")
async def parse(file: UploadFile):
    raw = await file.read()
    if not raw:
        raise HTTPException(422, detail="文件为空")
    if len(raw) > 50 * 1024 * 1024:
        raise HTTPException(422, detail="文件超过 50 MB 上限")

    filename = file.filename or "data"
    if filename.lower().endswith(".xlsx"):
        rows = _parse_xlsx(raw)
    elif filename.lower().endswith((".csv", ".txt", ".tsv")):
        rows = _parse_delimited(raw, filename)
    else:
        raise HTTPException(422, detail="仅支持 xlsx / csv / txt / tsv 文件")

    if len(rows) < 2:
        raise HTTPException(422, detail="文件需要包含表头和至少一行数据")

    header = [str(cell) if cell is not None else f"列{i + 1}" for i, cell in enumerate(rows[0])]
    body = rows[1:]
    width = len(header)
    truncated = len(body) > MAX_ROWS
    if truncated:
        body = body[:MAX_ROWS]

    body = [row + [None] * (width - len(row)) if len(row) < width else row[:width] for row in body]
    detect = _detect_columns(header, body)

    return {
        "filename": filename,
        "totalRows": len(rows) - 1,
        "truncated": truncated,
        "maxRows": MAX_ROWS,
        "columns": header,
        "detect": detect,
        "rows": body,
    }
