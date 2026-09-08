"""生成差异基因分析的示例数据模板（随机模拟数据，与任何真实项目无关）。

用法（在项目根目录）:
    .venv/Scripts/python scripts/make_demo_csv.py

产物: frontend/public/sample/volcano_demo.csv
表结构与常见差异分析结果表一致（gene_id / gene_name / fc / log2(fc) /
pval / qval / regulation / significant），数值全部随机生成，
分布模拟真实火山图：大部分基因为非显著，少量显著上调/下调，
q 值按从小到大排序。

用 CSV 而非 xlsx：数据无格式/公式，CSV 纯文本进 exe 包时可再被 zlib
压缩约 65%（xlsx 已是 deflate 压缩包，压不动），省约 240 KB。
编码用 utf-8-sig（带 BOM），保证 Excel 双击打开不乱码。
"""

import csv
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "frontend" / "public" / "sample" / "volcano_demo.csv"

random.seed(20260905)

HEADER = ["gene_id", "gene_name", "fc", "log2(fc)", "pval", "qval", "regulation", "significant", "KEGG"]

# 模拟 KEGG 注释：通路 ID(通路名)，分号分隔，格式与常见差异分析交付表格一致。
# 全部为通用示例通路名，随机分配（约 1/4 基因无注释），与任何真实项目无关。
KEGG_POOL = [
    "04066(HIF-1 signaling pathway)",
    "04151(PI3K-Akt signaling pathway)",
    "04010(MAPK signaling pathway)",
    "04115(p53 signaling pathway)",
    "04150(mTOR signaling pathway)",
    "04621(NOD-like receptor signaling pathway)",
    "04978(Mineral absorption)",
    "05200(Pathways in cancer)",
    "04216(Ferroptosis)",
    "00860(Porphyrin metabolism)",
    "04722(Neurotrophin signaling pathway)",
    "04141(Protein processing in endoplasmic reticulum)",
]


def rand_kegg(is_sig: bool) -> str:
    """显著基因约 3/4 有注释（1~3 条通路），非显著基因约 9/10 无注释。"""
    roll = random.random()
    if is_sig and roll > 0.25:
        count = random.choices([1, 2, 3], weights=[5, 3, 2])[0]
    elif not is_sig and roll > 0.9:
        count = 1
    else:
        return ""
    return ";".join(random.sample(KEGG_POOL, count))

# 目标形态（模拟全量基因的火山图，与参考图一致）：
#   灰色中央丘与蓝/红两翼共享同一条「包络」曲线，整体构成一个平滑的下凹：
#   从 x=0 处 ~10 的高度平滑爬升，在 |x|≈2.6 处到达峰顶（蓝 ~36 / 红 ~44），
#   再按指数衰减平滑下降，外侧拖着 y≈0~5 的低平尾巴直到 |x|≈15。
points: list[tuple[float, float]] = []

X_CUT = 1.0        # 显著性横轴阈值
PEAK_AT = 2.6      # 包络峰顶位置
E_CENTER = 10.0    # x=0 处的包络高度
E_FLOOR = 1.6      # 远端包络下限


def envelope(ax: float, peak: float, decay: float) -> float:
    """点云上边界：峰前二次爬升、峰后指数衰减，保证交界处平滑。"""
    if ax < PEAK_AT:
        return E_CENTER + (peak - E_CENTER) * (ax / PEAK_AT) ** 2
    return max(E_FLOOR, peak * math.exp(-(ax - PEAK_AT) / decay))


def sample_y(ax: float, peak: float, decay: float, heavy: float = 1.5) -> float:
    """在包络之下取 y：幂次采样让点越靠近底部越密。"""
    y = envelope(ax, peak, decay) * random.uniform(0.02, 1.0) ** heavy
    return max(0.03, y)


def sample_ax(mean: float, cap: float) -> float:
    """显著点的 |x|：阈值处最密，向外指数变稀。"""
    while True:
        ax = X_CUT + random.expovariate(1 / mean)
        if ax <= cap:
            return ax


def add(x: float, y: float) -> None:
    points.append((x, y))


# ---- 灰色非显著：中央丘（与两翼同一条包络，交界处平滑相连） ----
for _ in range(3600):
    while True:
        x = random.gauss(0, 0.55)
        if abs(x) < X_CUT:
            break
    add(x, sample_y(abs(x), peak=40.0, decay=3.2))

# ---- 沿 y≈0 的低平长带：铺满整条横轴直到 |x|≈15 ----
for _ in range(700):
    x = math.copysign(15 * random.uniform(0, 1) ** 1.6, random.uniform(-1, 1))
    y = min(5.0, 0.03 + random.expovariate(1 / 0.9))
    add(x, y)

# ---- 蓝色下调：左翼 ----
for _ in range(1900):  # 密集主体
    ax = sample_ax(mean=2.0, cap=15.0)
    add(-ax, sample_y(ax, peak=36.0, decay=3.0))
for _ in range(5):  # 翼顶散点（对应原图 y≈50~62 的几颗）
    add(-random.uniform(2.2, 3.6), random.uniform(48, 62))

# ---- 红色上调：右翼（更多、更高、拖得更远） ----
for _ in range(2300):  # 密集主体
    ax = sample_ax(mean=2.4, cap=15.0)
    add(ax, sample_y(ax, peak=44.0, decay=3.6, heavy=1.35))
for _ in range(10):  # 翼顶散点（对应原图 y≈55~105 的散点）
    add(random.uniform(2.0, 7.5), random.uniform(55, 105))
add(6.5, 211.3)  # 全图最高的一颗


def rand_gene_name(i: int) -> str:
    # 带行号保证唯一：MCK + 随机字母 + 四位序号
    return f"MCK{random.choice('ABCDEFGJKMNPQRSTUVWXYZ')}{i:04d}"


def make_row(i: int, x: float, y: float) -> list:
    qval = 10 ** (-y)
    pval = min(1.0, qval * random.uniform(1, 30))
    regulation = "up" if x >= 1 and qval <= 0.05 else ("down" if x <= -1 and qval <= 0.05 else "no")
    is_sig = regulation != "no"
    return [
        f"MOCKG{i:07d}",
        rand_gene_name(i),
        round(2**x, 6),
        round(x, 6),
        f"{pval:.6g}",
        f"{qval:.6g}",
        regulation,
        "yes" if is_sig else "no",
        rand_kegg(is_sig),
    ]


def main() -> None:
    rows = [make_row(i, x, y) for i, (x, y) in enumerate(points, 1)]
    rows.sort(key=lambda r: float(r[5]))  # 按 qval 从小到大，贴近常见交付表格
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)
    sig = sum(1 for r in rows if r[7] == "yes")
    up = sum(1 for r in rows if r[6] == "up")
    down = sum(1 for r in rows if r[6] == "down")
    print(f"[demo] 已生成 {OUT}（共 {len(rows)} 行：上调 {up} / 下调 {down} / 非显著 {len(rows) - sig}）")


if __name__ == "__main__":
    main()
