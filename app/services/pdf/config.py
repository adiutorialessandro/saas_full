from __future__ import annotations

from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm

# =========================================================
# Layout (Landscape board-pack)
# =========================================================
PAGE_SIZE = landscape(A4)
W, H = PAGE_SIZE

M_L = 18 * mm
M_R = 18 * mm
M_T = 16 * mm
M_B = 16 * mm

SAFE_W = W - M_L - M_R
SAFE_H = H - M_T - M_B

HEADER_H = 22 * mm
FOOTER_Y = 6 * mm

DEFAULT_TOTAL_PAGES = 5

# =========================================================
# Branding (white-label)
# =========================================================
DEFAULT_PRIMARY = colors.HexColor("#0b1220")
DEFAULT_ACCENT = colors.HexColor("#3b82f6")
DEFAULT_BG = colors.HexColor("#f3f4f6")
DEFAULT_CARD = colors.white
DEFAULT_STROKE = colors.HexColor("#e5e7eb")
DEFAULT_TEXT = colors.HexColor("#111827")
DEFAULT_MUTED = colors.HexColor("#6b7280")

# =========================================================
# Sector benchmarks: values are "risk" 0..1 (0 good, 1 critical)
# NOTE: if you don't have real benchmark source -> keep disabled via benchmark_meta
# =========================================================
SECTOR_BENCHMARKS: Dict[str, List[float]] = {
    "SaaS": [0.35, 0.40, 0.45],
    "Ecommerce": [0.30, 0.35, 0.50],
    "Agency": [0.40, 0.45, 0.55],
    "Servizi": [0.40, 0.45, 0.55],
    "Default": [0.35, 0.40, 0.45],
}
