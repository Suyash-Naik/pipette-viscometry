"""Visual theme for the interactive fitter.

Colours come from a validated categorical palette: series slot 1 (blue) for
aspiration, slot 2 (orange) for retraction. Raw data and all text wear neutral
ink tokens so identity is carried by the coloured marks, never by coloured text.
"""

from dataclasses import dataclass
import math

from matplotlib import font_manager

# Preferred UI sans, in order. Resolved once so matplotlib never warns per-artist
# about families that are not installed.
FONT_STACK = ["Segoe UI", "Inter", "Helvetica Neue", "Arial", "DejaVu Sans"]


def _resolve_font(candidates: list[str]) -> str:
    available = {f.name for f in font_manager.fontManager.ttflist}
    return next((name for name in candidates if name in available), "DejaVu Sans")


FONT = _resolve_font(FONT_STACK)


@dataclass(frozen=True)
class Theme:
    page: str          # figure background
    surface: str       # axes / card background
    ink: str           # primary text
    ink_secondary: str # labels
    muted: str         # axis ticks, meta text
    grid: str          # hairline gridlines
    axis: str          # spines / baselines
    raw: str           # raw data points
    asp: str           # aspiration series
    ret: str           # retraction series
    good: str          # status: ready
    critical: str      # status: error
    btn_face: str      # secondary button fill
    btn_hover: str
    accent_hover: str  # primary button hover

    @classmethod
    def light(cls) -> "Theme":
        return cls(
            page="#f9f9f7", surface="#fcfcfb",
            ink="#0b0b0b", ink_secondary="#52514e", muted="#898781",
            grid="#e1e0d9", axis="#c3c2b7", raw="#898781",
            asp="#2a78d6", ret="#eb6834",
            good="#0ca30c", critical="#d03b3b",
            btn_face="#f0efec", btn_hover="#e1e0d9", accent_hover="#1c5cab",
        )

    @classmethod
    def dark(cls) -> "Theme":
        return cls(
            page="#0d0d0d", surface="#1a1a19",
            ink="#ffffff", ink_secondary="#c3c2b7", muted="#898781",
            grid="#2c2c2a", axis="#383835", raw="#898781",
            asp="#3987e5", ret="#d95926",
            good="#0ca30c", critical="#d03b3b",
            btn_face="#2c2c2a", btn_hover="#383835", accent_hover="#2a78d6",
        )

    @classmethod
    def named(cls, name: str) -> "Theme":
        return cls.dark() if str(name).lower() == "dark" else cls.light()


_SUPERSCRIPT = str.maketrans("-0123456789", "\u207b\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079")


def format_value(value: float | None, sig: int = 4) -> str:
    """Human-readable number: plain decimals in the readable range, unicode
    scientific notation (1.234 x 10^-5) outside it."""
    if value is None or not math.isfinite(value):
        return "\u2014"
    if value == 0:
        return "0"
    magnitude = abs(value)
    if 1e-3 <= magnitude < 1e5:
        return f"{value:,.{sig}g}"
    exponent = math.floor(math.log10(magnitude))
    mantissa = value / (10 ** exponent)
    return f"{mantissa:.3f} \u00d7 10{str(exponent).translate(_SUPERSCRIPT)}"
