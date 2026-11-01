LIGHT_TEXT = "#ffffff"
DARK_TEXT = "#1a1a1a"
LUMINANCE_THRESHOLD = 0.55


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    digits = hex_color.lstrip("#")
    return int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16)


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    return f"#{red:02x}{green:02x}{blue:02x}"


def relative_luminance(hex_color: str) -> float:
    red, green, blue = hex_to_rgb(hex_color)
    return (0.299 * red + 0.587 * green + 0.114 * blue) / 255


def contrast_text_color(background_hex: str) -> str:
    """Dark text on light backgrounds, light text on dark ones."""
    return DARK_TEXT if relative_luminance(background_hex) > LUMINANCE_THRESHOLD else LIGHT_TEXT


def darken(hex_color: str, fraction: float) -> str:
    """Move each channel towards black by `fraction` (0.0 = unchanged, 1.0 = black)."""
    red, green, blue = (round(channel * (1 - fraction)) for channel in hex_to_rgb(hex_color))
    return rgb_to_hex(red, green, blue)
