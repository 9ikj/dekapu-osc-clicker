import base64
import io

from PIL import Image, ImageDraw, ImageFont


def _build_icon(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def scale(value: float) -> int:
        return int(round(value * size / 256))

    draw.rounded_rectangle((scale(16), scale(16), scale(240), scale(240)), radius=scale(56), fill=(126, 179, 255, 255))
    draw.rounded_rectangle((scale(44), scale(52), scale(212), scale(180)), radius=scale(34), fill=(255, 255, 255, 255))
    draw.polygon([(scale(80), scale(180)), (scale(92), scale(154)), (scale(140), scale(180))], fill=(255, 255, 255, 255))
    draw.ellipse((scale(160), scale(66), scale(188), scale(94)), fill=(255, 226, 122, 255))
    draw.ellipse((scale(184), scale(94), scale(200), scale(110)), fill=(255, 211, 92, 255))
    draw.ellipse((scale(60), scale(66), scale(72), scale(78)), fill=(255, 255, 255, 220))

    try:
        font_sp = ImageFont.truetype("arial.ttf", scale(52))
        font_name = ImageFont.truetype("arial.ttf", scale(28))
    except Exception:
        font_sp = ImageFont.load_default()
        font_name = ImageFont.load_default()

    draw.text((size // 2, scale(118)), "SP", anchor="mm", fill=(112, 130, 255, 255), font=font_sp)
    draw.text((size // 2, scale(204)), "助手", anchor="mm", fill=(255, 255, 255, 255), font=font_name)
    return image


def _encode_png_base64() -> str:
    image = _build_icon(256)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


WINDOW_ICON_PNG_BASE64 = _encode_png_base64()


def get_window_icon_png_bytes() -> bytes:
    return base64.b64decode(WINDOW_ICON_PNG_BASE64)


def get_tray_icon_image(size: int = 64) -> Image.Image:
    return _build_icon(size)
