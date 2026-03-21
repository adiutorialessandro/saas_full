from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- MARGINI ---
PDF_MARGINS = {
    "left": 18 * mm,
    "right": 18 * mm,
    "top": 16 * mm,
    "bottom": 14 * mm
}

# --- FONTS ---
def setup_pdf_fonts():
    """
    Inizializza i font personalizzati. 
    Per evitare dipendenze da file .ttf esterni, usiamo i font vettoriali nativi (Helvetica).
    """
    pass

# --- STILI (ParagraphStyles) ---
_base = getSampleStyleSheet()

STYLES = {
    "CoverTitle": ParagraphStyle(
        "CoverTitle",
        parent=_base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=32,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=15,
        leading=36
    ),
    "CoverSubtitle": ParagraphStyle(
        "CoverSubtitle",
        parent=_base["Normal"],
        fontName="Helvetica",
        fontSize=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=10
    ),
    "Heading1": ParagraphStyle(
        "Heading1",
        parent=_base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=25,
        spaceAfter=15
    ),
    "Heading2": ParagraphStyle(
        "Heading2",
        parent=_base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.HexColor("#4fc3f7"), # Azzurro brand
        spaceBefore=15,
        spaceAfter=10
    ),
    "Normal": ParagraphStyle(
        "Normal",
        parent=_base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=colors.HexColor("#334155"),
        leading=16,
        spaceAfter=8
    )
}
