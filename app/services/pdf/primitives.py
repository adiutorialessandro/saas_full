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
    W,
)


def page_bg(c: canvas.Canvas) -> None:
    c.setFillColor(DEFAULT_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def shadow_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    radius: float = 12,
    fill_color=DEFAULT_SURFACE,
) -> None:
    c.saveState()
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.05))
    c.roundRect(x + 1.6 * mm, y - 1.4 * mm, w, h, radius, fill=1, stroke=0)

    c.setFillColor(fill_color)
    c.setStrokeColor(DEFAULT_BORDER)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    c.restoreState()


def section_title(
    c: canvas.Canvas,
    x: float,
    y: float,
    title: str,
    subtitle: Optional[str] = None,
) -> None:
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, title)

    if subtitle:
        c.setFillColor(DEFAULT_MUTED)
        c.setFont("Helvetica", 9.4)
        c.drawString(x, y - 5 * mm, subtitle)


def _status_label(overall: str) -> str:
    ov = str(overall or "").upper()
    if ov == "ROSSO":
        return "Priorità alta"
    if ov == "GIALLO":
        return "Attenzione attiva"
    return "Situazione sotto controllo"


def header(
    c: canvas.Canvas,
    title: str,
    subtitle: str,
    overall: str,
    right_label: Optional[str] = None,
) -> None:
    c.saveState()

    c.setFillColor(DEFAULT_PRIMARY)
    c.rect(0, H - 18 * mm, W, 18 * mm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(M_L, H - 11.2 * mm, BRAND_NAME)

    c.setFont("Helvetica", 8.8)
    c.drawRightString(W - M_R, H - 11.2 * mm, right_label or _status_label(overall))

    c.restoreState()

    section_title(c, M_L, H - 27 * mm, title, subtitle)


def footer(c: canvas.Canvas, page_no: int, total: int) -> None:
    c.saveState()
    c.setStrokeColor(DEFAULT_BORDER)
    c.line(M_L, M_B + 6 * mm, W - M_R, M_B + 6 * mm)

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 8.5)
    c.drawString(M_L, M_B + 2 * mm, f"{BRAND_NAME} · Report strategico")
    c.drawRightString(W - M_R, M_B + 2 * mm, f"Pagina {page_no}/{total}")
    c.restoreState()


def badge_color(level: str):
    lvl = str(level or "").upper()
    if lvl == "ROSSO":
        return DEFAULT_DANGER
    if lvl == "GIALLO":
        return DEFAULT_WARNING
    return DEFAULT_SUCCESS


def draw_badge(c: canvas.Canvas, x: float, y: float, text: str, w: float = 24 * mm) -> None:
    col = badge_color(text)
    c.saveState()
    c.setFillColor(col)
    c.roundRect(x, y, w, 7 * mm, 3 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(x + (w / 2), y + 2.2 * mm, str(text).upper())
    c.restoreState()


def progress_bar(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    value_100: float,
) -> None:
    value = max(0.0, min(100.0, float(value_100)))

    c.saveState()
    c.setFillColor(DEFAULT_SURFACE_2)
    c.roundRect(x, y, w, h, h / 2, fill=1, stroke=0)

    if value >= 67:
        fill = DEFAULT_DANGER
    elif value >= 34:
        fill = DEFAULT_WARNING
    else:
        fill = DEFAULT_SUCCESS

    fill_w = max((w * value) / 100.0, h)
    fill_w = min(fill_w, w)

    c.setFillColor(fill)
    c.roundRect(x, y, fill_w, h, h / 2, fill=1, stroke=0)
    c.restoreState()


def score_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    score_value: str,
    subtitle: str,
    progress_value: float,
) -> None:
    shadow_card(c, x, y, w, h)

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.2)
    c.drawString(x + 7 * mm, y + h - 10 * mm, title)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(x + 7 * mm, y + h - 24 * mm, score_value)

    progress_bar(c, x + 7 * mm, y + h - 33 * mm, w - 14 * mm, 5 * mm, progress_value)

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(x + 7 * mm, y + 8 * mm, subtitle)


def risk_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    risk_value: float,
    desc: str,
) -> None:
    shadow_card(c, x, y, w, h)

    if risk_value >= 0.66:
        label = "ROSSO"
    elif risk_value >= 0.33:
        label = "GIALLO"
    else:
        label = "VERDE"

    pct = int(round(max(0, min(1, risk_value)) * 100))

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 6 * mm, y + h - 10 * mm, title)

    draw_badge(c, x + w - 29 * mm, y + h - 13 * mm, label)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(x + 6 * mm, y + h - 26 * mm, f"{pct}%")

    progress_bar(c, x + 6 * mm, y + h - 34 * mm, w - 12 * mm, 4.5 * mm, pct)

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.1)
    c.drawString(x + 6 * mm, y + 8 * mm, desc)


def kpi_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    value: str,
    subtitle: str,
    label: str,
) -> None:
    shadow_card(c, x, y, w, h)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 10.8)
    c.drawString(x + 5 * mm, y + h - 9 * mm, title)

    draw_badge(c, x + w - 28 * mm, y + h - 12 * mm, label, w=22 * mm)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x + 5 * mm, y + h - 20 * mm, value)

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 8.5)
    c.drawString(x + 5 * mm, y + 6 * mm, subtitle)


def bullet_block(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    title: str,
    items: list[str],
    line_gap_mm: float = 7.0,
) -> None:
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, title)

    c.setFont("Helvetica", 9.4)
    yy = y - 7 * mm
    for item in items:
        c.setFillColor(DEFAULT_ACCENT)
        c.circle(x + 1.5 * mm, yy + 1.4 * mm, 1.3 * mm, fill=1, stroke=0)

        c.setFillColor(DEFAULT_TEXT)
        c.drawString(x + 5 * mm, yy, item)
        yy -= line_gap_mm * mm