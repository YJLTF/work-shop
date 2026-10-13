"""CSV/TSV 互转工具：纯标准库完成分隔符、编码与换行符转换。

编码自动检测按 BOM → UTF-8 严格校验 → GB18030 → Latin-1 兜底的顺序进行，
不引入 chardet 等第三方依赖，保持打包体积可控。
"""
import csv
import io
import json
import re
import time
from urllib.parse import quote

from fastapi import Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.tools.base import ToolDefinition, tool_router

TOOL = ToolDefinition(
    id="csv-tsv",
    name="CSV/TSV 转换",
    description="CSV 与 TSV 互转，可同时转换编码（UTF-8/GBK 等）与换行符（CRLF/LF）",
)

router = tool_router(TOOL.id)

MAX_BYTES = 100 * 1024 * 1024
MAX_ROWS = 2_000_000
PREVIEW_LINES = 5
PREVIEW_WIDTH = 300  # 单条预览记录截断长度，防止超宽行撑爆报告头

# 编码代号 → (解码用 codec, 展示名)；latin-1 永不解码失败，仅作自动检测的兜底
ENCODINGS = {
    "utf-8": ("utf-8", "UTF-8"),
    "utf-8-sig": ("utf-8-sig", "UTF-8（带 BOM）"),
    "utf-16": ("utf-16", "UTF-16"),
    "gbk": ("gbk", "GBK"),
    "gb18030": ("gb18030", "GB18030"),
    "big5": ("big5", "Big5（繁体中文）"),
    "latin-1": ("latin-1", "Latin-1（西欧）"),
}
DELIMITERS = {"csv": ",", "tsv": "\t"}
LINE_ENDINGS = {
    "crlf": ("\r\n", "CRLF（Windows）"),
    "lf": ("\n", "LF（Unix/macOS）"),
    "cr": ("\r", "CR（经典 Mac）"),
}
QUOTE_MODES = {"minimal": csv.QUOTE_MINIMAL, "all": csv.QUOTE_ALL}
BLANK_MODES = ("skip", "keep")

_EMBEDDED_NEWLINE = re.compile(r"\r\n|\r|\n")

# 默认单字段 128 KB 限制对表格数据太紧，放宽以支持长文本列
csv.field_size_limit(16 * 1024 * 1024)


def _require(value: str, allowed, what: str) -> str:
    if value not in allowed:
        raise HTTPException(422, detail=f"{what}取值无效：{value}")
    return value


def _auto_detect_encoding(raw: bytes) -> tuple[str, list[str]]:
    """返回编码代号与警告；无法严格判定时按 Latin-1 兜底并提示。"""
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", []
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return "utf-16", []
    try:
        raw.decode("utf-8")
        return "utf-8", []
    except UnicodeDecodeError:
        pass
    try:
        raw.decode("gb18030")
        return "gb18030", []
    except UnicodeDecodeError:
        pass
    return "latin-1", ["无法确定源编码，已按 Latin-1 解码，请核对结果或手动指定源编码"]


def _decode(raw: bytes, encoding_key: str) -> tuple[str, str, list[str]]:
    """按指定或自动检测的编码解码，返回 (文本, 展示名, 警告列表)。"""
    warnings: list[str] = []
    if encoding_key == "auto":
        encoding_key, warnings = _auto_detect_encoding(raw)
        codec, label = ENCODINGS[encoding_key]
    else:
        codec, label = ENCODINGS[encoding_key]
        # 用户指定 utf-8 时容忍 BOM：直接按 utf-8 解会在首列留下 \ufeff
        if codec == "utf-8":
            codec = "utf-8-sig"
        try:
            return raw.decode(codec), label, warnings
        except UnicodeDecodeError as exc:
            raise HTTPException(
                422, detail=f"无法按 {label} 解码：第 {exc.start + 1} 字节附近不是合法的 {label} 序列，可改用自动检测"
            ) from exc
    return raw.decode(codec), label, warnings


def _detect_line_ending(raw: bytes) -> str:
    """按出现次数判定源换行符；单行或空文件无从判断时默认 LF。"""
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    cr = raw.count(b"\r") - crlf
    if crlf and crlf >= lf and crlf >= cr:
        return "crlf"
    if lf:
        return "lf"
    if cr:
        return "cr"
    return "lf"


def _sniff_delimiter(text: str) -> str:
    """取样本中出现最多的候选分隔符；全都未出现时退回逗号。

    比 csv.Sniffer 稳健：不依赖引号结构推断，对常规表格足够准。
    """
    sample = text[:65536]
    counts = {d: sample.count(d) for d in (",", "\t", ";", "|")}
    best = max(counts, key=counts.get)
    return best if counts[best] else ","


@router.post("/convert")
async def convert(
    file: UploadFile,
    to_format: str = Form("csv"),
    from_format: str = Form("auto"),
    from_encoding: str = Form("auto"),
    to_encoding: str = Form("utf-8"),
    line_endings: str = Form("keep"),
    quote_mode: str = Form("minimal"),
    blank_lines: str = Form("skip"),
):
    started = time.perf_counter()
    _require(to_format, DELIMITERS, "目标格式")
    _require(from_format, DELIMITERS.keys() | {"auto"}, "源格式")
    _require(from_encoding, ENCODINGS.keys() | {"auto"}, "源编码")
    _require(to_encoding, ENCODINGS, "目标编码")
    _require(line_endings, LINE_ENDINGS.keys() | {"keep"}, "换行符")
    _require(quote_mode, QUOTE_MODES, "引号风格")
    _require(blank_lines, BLANK_MODES, "空行处理")

    raw = await file.read()
    if not raw:
        raise HTTPException(422, detail="上传的文件是空的")
    if len(raw) > MAX_BYTES:
        raise HTTPException(422, detail=f"文件超过 {MAX_BYTES // (1024 * 1024)} MB 上限，请先拆分")

    text, source_label, warnings = _decode(raw, from_encoding)
    source_ending = _detect_line_ending(raw)

    if from_format == "auto":
        delimiter_in = _sniff_delimiter(text)
    else:
        delimiter_in = DELIMITERS[from_format]

    # 「保持原样」落成具体的源换行符，后续写入与字段内换行归一化共用同一目标
    ending_key = source_ending if line_endings == "keep" else line_endings
    ending = LINE_ENDINGS[ending_key][0]

    out_buf = io.StringIO()
    writer = csv.writer(
        out_buf,
        delimiter=DELIMITERS[to_format],
        quoting=QUOTE_MODES[quote_mode],
        lineterminator=ending,
    )

    rows = 0
    cols = 0
    blank_removed = 0
    preview: list[str] = []
    try:
        # newline=''：不做通用换行翻译，\r\n / \r / \n 交给 csv 模块按记录切分
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter_in)
        for row in reader:
            if not row:  # csv.reader 对真正的空行返回 []
                blank_removed += 1
                if blank_lines == "keep":
                    writer.writerow(row)
                continue
            # 引号字段里的换行同样归一化到目标换行符，保证整个文件风格一致
            row = [_EMBEDDED_NEWLINE.sub(ending, c) if ("\r" in c or "\n" in c) else c for c in row]
            rows += 1
            cols = max(cols, len(row))
            writer.writerow(row)
            if rows <= PREVIEW_LINES:
                buf = io.StringIO()
                csv.writer(
                    buf,
                    delimiter=DELIMITERS[to_format],
                    quoting=QUOTE_MODES[quote_mode],
                    lineterminator="",
                ).writerow(row)
                preview.append(buf.getvalue()[:PREVIEW_WIDTH])
            if rows > MAX_ROWS:
                raise HTTPException(422, detail=f"行数超过上限 {MAX_ROWS:,}，请先拆分文件")
    except csv.Error as exc:
        raise HTTPException(422, detail=f"第 {rows + 1} 行附近解析失败：{exc}") from exc

    body_text = out_buf.getvalue()
    out_codec, out_label = ENCODINGS[to_encoding]
    try:
        data = body_text.encode(out_codec)
    except UnicodeEncodeError as exc:
        bad = body_text[exc.start]
        raise HTTPException(
            422,
            detail=f"目标编码 {out_label} 无法表示字符 “{bad}”（U+{ord(bad):04X}，输出第 {exc.start + 1} 字符附近），请改用 UTF-8 或 GB18030",
        ) from exc

    filename = file.filename or ""
    stem = re.split(r"[\\/]", filename)[-1]
    stem = re.sub(r"\.(csv|tsv|txt|tab)$", "", stem, flags=re.IGNORECASE) or "converted"
    download_name = f"{stem}.{to_format}"
    report = {
        "source_encoding": source_label,
        "source_auto_detected": from_encoding == "auto",
        "delimiter_in": delimiter_in,
        "source_line_ending": source_ending,
        "output_encoding": out_label,
        "delimiter_out": DELIMITERS[to_format],
        "output_line_ending": ending_key,
        "rows": rows,
        "cols": cols,
        "blank_removed": blank_removed,
        "output_bytes": len(data),
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "warnings": warnings,
        "preview": preview,
    }
    return Response(
        content=data,
        media_type="text/tab-separated-values" if to_format == "tsv" else "text/csv",
        headers={
            # blob 下载的文件名由前端决定，这里仅作为直链场景的兜底
            "Content-Disposition": f"attachment; filename=\"converted.{to_format}\"; filename*=UTF-8''{quote(download_name)}",
            # ensure_ascii 保证报告头是纯 ASCII，绕开 HTTP 头的 latin-1 限制
            "X-Convert-Report": json.dumps(report, ensure_ascii=True),
        },
    )
