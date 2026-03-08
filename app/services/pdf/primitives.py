from __future__ import annotations

from typing import Optional

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .config import (
    BRAND_NAME,
    DEFAULT_ACCENT,
    DEFAULT_BG,
    DEFAULT_BORDER,
    DEFAULT_DANGER,
    DEFAULT_MUTED,
    DEFAULT_PRIMARY,
    DEFAULT_SUCCESS,
    DEFAULT_SURFACE,
    DEFAULT_SURFACE_2,
    DEFAULT_TEXT,
    DEFAULT_WARNING,
    H,
    M_B,
    M_L,
    M_R,
    M_T,
    SAFE_W,
    W,
)
from .utils import risk_label, risk_pct


def page_bg(c: canvas.Canvas) -> None:
    c.setFillColor(DEFAULT_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def shadow_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, radius: float = 12) -> None:
    c.saveState()
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.04))
    c.roundRect(x + 1.5 * mm, y - 1.5 * mm, w, h, radius, fill=1, stroke=0)
    c.setFillColor(DEFAULT_SURFACE)
    c.setStrokeColor(DEFAULT_BORDER)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    c.restoreState()


def section_title(c: canvas.Canvas, x: float, y: float, title: str, subtitle: Optional[str] = None) -> None:
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, title)
    if subtitle:
        c.setFillColor(DEFAULT_MUTED)
        c.setFont("Helvetica", 9.5)
        c.drawString(x, y - 5 * mm, subtitle)


def header(
    c: canvas.Canvas,
    title: str,
    subtitle: str,
    overall: str,
    right_label: Optional[str] = None,
) -> None:
    c.setFillColor(DEFAULT_PRIMARY)
    c.rect(0, H - 18 * mm, W, 18 * mm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(M_L, H - 11.5 * mm, BRAND_NAME)

    c.setFont("Helvetica", 8.8)
    c.drawRightString(W - M_R, H - 11.5 * mm, right_label or PDF_header_status(overall))

    section_title(c, M_L, H - M_T - 8 * mm, title, subtitle)


def PDF_header_status(overall: str) -> str:
    return f"Stato report: {overall}"


def footer(c: canvas.Canvas, page_no: int, total: int) -> None:
    c.setStrokeColor(DEFAULT_BORDER)
    c.line(M_L, M_B + 6 * mm, W - M_R, M_B + 6 * mm)
    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 8.5)
    c.drawString(M_L, M_B + 2 * mm, f"{BRAND_NAME} · Report strategico")
    c.drawRightString(W - M_R, M_B + 2 * mm, f"Pagina {page_no}/{total}")


def badge_color(level: str):
    lvl = str(level or "").upper()
    if lvl == "ROSSO":
        return DEFAULT_DANGER
    if lvl == "GIALLO":
        return DEFAULT_WARNING
    return DEFAULT_SUCCESS


def draw_badge(c: canvas.Canvas, x: float, y: float, text: str) -> None:
    col = badge_color(text)
    c.saveState()
    c.setFillColor(col)
    c.roundRect(x, y, 23 * mm, 7 * mm, 3 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(x + 11.5 * mm, y + 2.2 * mm, str(text))
    c.restoreState()


def progress_bar(c: canvas.Canvas, x: float, y: float, w: float, h: float, value_100: float) -> None:
    value = max(0.0, min(100.0, float(value_100)))
    c.setFillColor(DEFAULT_SURFACE_2)
    c.roundRect(x, y, w, h, h / 2, fill=1, stroke=0)

    if value >= 67:
        fill = DEFAULT_DANGER
    elif value >= 34:
        fill = DEFAULT_WARNING
    else:
        fill = DEFAULT_SUCCESS

    c.setFillColor(fill)
    c.roundRect(x, y, (w * value) / 100.0, h, h / 2, fill=1, stroke=0)


def risk_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str, risk_value: float, desc: str) -> None:
    shadow_card(c, x, y, w, h)
    label = risk_label(risk_value)
    pct = risk_pct(risk_value)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 6 * mm, y + h - 10 * mm, title)

    draw_badge(c, x + w - 29 * mm, y + h - 13 * mm, label)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(x + 6 * mm, y + h - 24 * mm, f"{pct}%")

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.3)
    c.drawString(x + 6 * mm, y + 9 * mm, desc)


def kpi_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str, value: str, subtitle: str, label: str) -> None:
    shadow_card(c, x, y, w, h)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 5 * mm, y + h - 9 * mm, title)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(x + 5 * mm, y + h - 19 * mm, value)

    draw_badge(c, x + w - 28 * mm, y + h - 12 * mm, label)

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 8.6)
    c.drawString(x + 5 * mm, y + 6 * mm, subtitle)