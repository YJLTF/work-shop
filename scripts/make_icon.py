"""生成应用图标 build/icon.ico 与启动占位图 build/splash.png：黄铜圆角底 + 深色 W 字标。

仅需在打包前运行一次：.venv/Scripts/python scripts/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "icon.ico"
SPLASH = ROOT / "build" / "splash.png"

BRASS = (232, 163, 61, 255)
DARK = (22, 19, 10, 255)
SIZE = 256


def rounded(size: int, ratio: float = 0.22) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [0, 0, size - 1, size - 1],
        radius=int(size * ratio),
        fill=BRASS,
    )
    return img


def letter(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    # 优先使用系统粗体字体
    for candidate in ("segoeuib.ttf", "arialbd.ttf", "msyhbd.ttc", "arial.ttf"):
        try:
            font = ImageFont.truetype(candidate, int(SIZE * 0.62))
            break
        except OSError:
            continue
    else:
        font = ImageFont.load_default()

    left, top, right, bottom = draw.textbbox((0, 0), "W", font=font)
    width, height = right - left, bottom - top
    draw.text(
        ((SIZE - width) / 2 - left, (SIZE - height) / 2 - top - SIZE * 0.01),
        "W",
        font=font,
        fill=DARK,
    )


def _font(size: int):
    for candidate in ("msyhbd.ttc", "segoeuib.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def splash() -> None:
    """启动占位图：exe 双击后由 PyInstaller --splash 立即显示，服务就绪后关闭。"""
    width, height = 460, 280
    img = Image.new("RGB", (width, height), BRASS)
    draw = ImageDraw.Draw(img)

    def center_text(text: str, font, top: float, fill=DARK) -> None:
        left, t, right, _ = draw.textbbox((0, 0), text, font=font)
        draw.text(((width - (right - left)) / 2 - left, top - t), text,
                  font=font, fill=fill)

    center_text("W", _font(96), 52)
    center_text("正在启动 WorkShop …", _font(22), 184)
    SPLASH.parent.mkdir(exist_ok=True)
    img.save(SPLASH, format="PNG")
    print(f"启动占位图已生成: {SPLASH}")


def main() -> None:
    img = rounded(SIZE)
    letter(img)
    OUT.parent.mkdir(exist_ok=True)
    img.save(
        OUT,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"图标已生成: {OUT}")
    splash()


if __name__ == "__main__":
    main()
