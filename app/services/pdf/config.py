from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm

PAGE_SIZE = landscape(A4)
W, H = PAGE_SIZE

M_L = 18 * mm
M_R = 18 * mm
M_T = 16 * mm
M_B = 14 * mm

SAFE_W = W - M_L - M_R
SAFE_H = H - M_T - M_B

DEFAULT_PRIMARY = colors.HexColor("#0f172a")
DEFAULT_ACCENT = colors.HexColor("#2563eb")
DEFAULT_SUCCESS = colors.HexColor("#16a34a")
DEFAULT_WARNING = colors.HexColor("#d97706")
DEFAULT_DANGER = colors.HexColor("#dc2626")
DEFAULT_TEXT = colors.HexColor("#0f172a")
DEFAULT_MUTED = colors.HexColor("#64748b")
DEFAULT_BORDER = colors.HexColor("#e2e8f0")
DEFAULT_SURFACE = colors.HexColor("#ffffff")
DEFAULT_SURFACE_2 = colors.HexColor("#f8fafc")
DEFAULT_BG = colors.HexColor("#f1f5f9")

BRAND_NAME = "SaaS Full"
PDF_TITLE = "Business Strategic Scan"
PDF_SUBTITLE = "Executive business report"