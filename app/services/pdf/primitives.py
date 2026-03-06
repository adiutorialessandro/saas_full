from __future__ import annotations

from math import cos, sin, pi
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .config import (
    DEFAULT_ACCENT,
    DEFAULT_BG,
    DEFAULT_CARD,
    DEFAULT_PRIMARY,
    DEFAULT_STROKE,
    DEFAULT_TEXT,
    DEFAULT_MUTED,
    FOOTER_Y,
    HEADER_H,
    M_L,
    M_R,
    SAFE_W,
    W,
    H,
)
from .utils import badge_color, clamp01, ellipsize, risk_bucket, wrap


def page_bg(c: canvas.Canvas, bg=DEFAULT_BG):
    c.setFillColor(bg)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def watermark(c: canvas.Canvas, text: str = "CONFIDENTIAL"):
    c.saveState()
    c.setFillColor(colors.HexColor("#eef2f7"))
    c.setFont("Helvetica-Bold", 44)
    c.translate(W / 2.0, H / 2.0)
    c.rotate(32)
    c.drawCentredString(0, 0, text)
    c.restoreState()


def header(
    c: canvas.Canvas,
    title: str,
    subtitle: str,
    badge: str,
    primary=DEFAULT_PRIMARY,
    logo_path: Optional[Union[str, Path]] = None,
):
    if isinstance(primary, str):
        primary = colors.HexColor(primary)

    c.setFillColor(primary)
    c.rect(0, H - HEADER_H, W, HEADER_H, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(M_L, H - 14 * mm, title)
    # Subtitle (max 2 righe) — resta sempre DENTRO l'header (evita tagli)
    c.setFillColor(colors.HexColor("#cbd5e1"))
    c.setFont("Helvetica", 9.5)

    # Mettiamo la prima riga ben sopra il bordo basso dell'header.
    # NOTE: usare split("\n") (non split("\\n")) per evitare stringhe rotte.
    sub_y0 = H - 18.0 * mm
    line_gap = 4.8 * mm
    for i, ln in enumerate((subtitle or "").split("\n")[:2]):
        c.drawString(M_L, sub_y0 - i * line_gap, ln)

    if logo_path:
        try:
            c.drawImage(
                str(logo_path),
                W - M_R - 22 * mm,
                H - 20.5 * mm,
                width=18 * mm,
                height=18 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    # Status pill (right, vertically centered in header)
    pill_h = 10 * mm
    label = (badge or "—").upper()
    pill_w = c.stringWidth(label, "Helvetica-Bold", 10) + 16 * mm
    pill_w = max(40 * mm, min(64 * mm, pill_w))

    header_y0 = H - HEADER_H
    # Slightly reduce right inset to push the pill right, but keep a safe margin
    right_inset = max(4 * mm, M_R - 10 * mm)
    bx = W - right_inset - pill_w
    by = header_y0 + (HEADER_H - pill_h) / 2.0

    col = badge_color(badge)
    c.setFillColor(col)
    c.roundRect(bx, by, pill_w, pill_h, pill_h / 2.0, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    # drawCentredString uses baseline; 3.2mm is a good optical centering for size 10
    c.drawCentredString(bx + pill_w / 2.0, by + 3.2 * mm, label)


def footer(c: canvas.Canvas, page: int, total: int, right_label: Optional[str] = None):
    """Footer:
    - Titolo centrato
    - Numero pagina a DESTRA
    - (opzionale) right_label a SINISTRA (per evitare collisioni col numero pagina)
    """
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#9ca3af"))

    y = 8.0 * mm

    # Center: program label
    c.drawCentredString(W / 2.0, y, "Programma Alessio SaaS – Board-ready Report")

    # Right: page counter
    c.drawRightString(W - M_R, y, f"Pagina {page}/{total}")

    # Left: optional label (DEV, etc.)
    if right_label:
        c.drawString(M_L, y, right_label)


def shadow_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, r: float = 10.0):
    """
    Card con ombra. Robust: se qualche valore arriva come stringa (es. "150*mm" o "123.4"),
    lo converte in numero prima di disegnare, evitando crash ReportLab (float + str).
    """
    from reportlab.lib.units import mm as _mm

    def _num(v, name: str) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            t = v.strip()
            # 1) prova float diretto
            try:
                return float(t)
            except Exception:
                pass
            # 2) prova eval ultra-limitato (solo mm), utile se t="150*mm" o simili
            try:
                return float(eval(t, {"__builtins__": {}}, {"mm": _mm}))
            except Exception as e:
                raise TypeError(f"shadow_card(): '{name}' non numerico: {v!r}") from e
        raise TypeError(f"shadow_card(): '{name}' type non supportato: {type(v).__name__}")

    x = _num(x, "x")
    y = _num(y, "y")
    w = _num(w, "w")
    h = _num(h, "h")
    r = _num(r, "r")

    # shadow
    c.saveState()
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.08))
    c.roundRect(x + 1.4, y - 1.4, w, h, r, fill=1, stroke=0)
    c.restoreState()

    # card
    c.saveState()
    c.setFillColor(DEFAULT_CARD)
    c.setStrokeColor(DEFAULT_STROKE)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)
    c.restoreState()


def bar(c: canvas.Canvas, x: float, y: float, w: float, h: float, score01: float, col):
    score01 = max(0.0, min(1.0, float(score01)))
    r = min(h / 2.0, 7)

    c.setFillColor(colors.HexColor("#eef2f7"))
    c.setStrokeColor(colors.HexColor("#eef2f7"))
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)

    fill_w = max(0.0, min(w, w * score01))
    if fill_w <= 0:
        return

    c.setFillColor(col)
    c.setStrokeColor(colors.transparent)

    if fill_w >= w - 0.01:
        c.roundRect(x, y, w, h, r, fill=1, stroke=0)
        return

    body_x = x + r
    body_w = max(0.0, fill_w - r)
    if body_w > 0:
        c.rect(body_x, y, body_w, h, fill=1, stroke=0)

    cap_cx = x + r
    cap_cy = y + h / 2.0
    c.circle(cap_cx, cap_cy, r, stroke=0, fill=1)


def risk_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    score01: float,
    desc: str,
):
    """Card rischio (3 colonne) con badge sotto il titolo.

    Layout: titolo (centrato) → badge (centrato) → valore (centrato) → barra (in basso).
    NOTE: per richiesta UI, la riga descrittiva (es. "Runway / cashflow") è disabilitata.
    """

    score01 = clamp01(score01, 0.5) or 0.0
    label = risk_bucket(score01)
    col = badge_color(label)

    # Card chrome
    pad = 10 * mm
    shadow_card(c, x, y, w, h, 16)

    top = y + h

    # --- Title (top) ---
    title_y = top - 16 * mm
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 15)
    title_fit = ellipsize(c, title, w - 2 * pad, font="Helvetica-Bold", size=15)
    c.drawCentredString(x + w / 2.0, title_y, title_fit or "")

    # --- Badge (under title, centered) ---
    badge_h = 10 * mm
    badge_w = c.stringWidth(label, "Helvetica-Bold", 10) + 18 * mm
    badge_w = max(34 * mm, min(62 * mm, badge_w))
    badge_x = x + (w - badge_w) / 2.0
    badge_y = title_y - 14 * mm

    c.setFillColor(col)
    c.roundRect(badge_x, badge_y, badge_w, badge_h, badge_h / 2.0, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(badge_x + badge_w / 2.0, badge_y + 3.2 * mm, label)

    # --- Progress bar (bottom) ---
    bar_h = 5.0 * mm
    bar_y = y + 14 * mm

    # --- Value (middle area) ---
    value_size = 34

    # Area utile tra badge e barra (con margini ottici)
    gap_after_badge = 10 * mm
    gap_before_bar = 12 * mm

    content_top = badge_y - gap_after_badge
    content_bottom = bar_y + bar_h + gap_before_bar

    # Centro ottico (ReportLab drawString usa la baseline)
    mid = (content_top + content_bottom) / 2.0
    baseline_adjust = value_size * 0.35  # punti
    value_y = mid - baseline_adjust

    # Clamp di sicurezza
    max_value_y = content_top - 2 * mm
    min_value_y = content_bottom + 2 * mm
    value_y = max(min_value_y, min(max_value_y, value_y))

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", value_size)
    c.drawCentredString(x + w / 2.0, value_y, f"{score01 * 100:.1f}%")

    # --- Progress bar ---
    bar(c, x + pad, bar_y, w - 2 * pad, bar_h, score01, col)

def kpi_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    value: str,
    subtitle: str,
    target: Optional[str] = None,
):
    shadow_card(c, x, y, w, h, 16)
    pad = 10 * 2.83465

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + pad, y + h - 10 * 2.83465, title)

    c.setFont("Helvetica-Bold", 20)
    c.drawString(x + pad, y + h - 22 * 2.83465, value)

    if subtitle and str(subtitle).strip():
        c.setFont("Helvetica", 10)
        c.setFillColor(DEFAULT_MUTED)
        c.drawString(x + pad, y + 6 * mm, str(subtitle))

    if target and str(target).strip():
        c.setFont("Helvetica", 9.5)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawString(x + pad, y + 6.5 * 2.83465, str(target))


def triad_progress(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    score: int,
    accent=DEFAULT_ACCENT,
):
    if isinstance(accent, str):
        accent = colors.HexColor(accent)

    track_h = 7 * 2.83465
    track_w = w
    c.setFillColor(colors.HexColor("#eef2f7"))
    c.roundRect(x, y, track_w, track_h, 7, fill=1, stroke=0)

    s = max(0, min(100, int(score)))
    c.setFillColor(accent)
    c.roundRect(x, y, track_w * (s / 100.0), track_h, 7, fill=1, stroke=0)


def draw_radar(
    c: canvas.Canvas,
    cx: float,
    cy: float,
    r: float,
    labels: List[str],
    values: List[float],      # risks 0..1
    benchmark: List[float],   # risks 0..1
    accent=DEFAULT_ACCENT,
):
    if isinstance(accent, str):
        accent = colors.HexColor(accent)

    n = max(1, len(labels))
    if len(values) != n or len(benchmark) != n:
        values = (values + [0.5] * n)[:n]
        benchmark = (benchmark + [0.45] * n)[:n]

    ang = 2 * pi / n

    c.setStrokeColor(colors.HexColor("#e5e7eb"))
    c.setLineWidth(1)
    for p in (0.25, 0.50, 0.75, 1.0):
        c.circle(cx, cy, r * p, stroke=1, fill=0)

    for i in range(n):
        x = cx + r * cos(i * ang)
        y = cy + r * sin(i * ang)
        c.line(cx, cy, x, y)

    # Company polygon (resilience = 1-risk)
    pts: List[Tuple[float, float]] = []
    for i in range(n):
        resilience = 1.0 - (clamp01(values[i], 0.5) or 0.5)
        rr = r * resilience
        pts.append((cx + rr * cos(i * ang), cy + rr * sin(i * ang)))

    path = c.beginPath()
    path.moveTo(pts[0][0], pts[0][1])
    for p in pts[1:]:
        path.lineTo(p[0], p[1])
    path.close()

    c.setFillColor(accent)
    c.setStrokeColor(colors.transparent)
    c.drawPath(path, fill=1, stroke=0)

    # Benchmark outline
    pts_b: List[Tuple[float, float]] = []
    for i in range(n):
        resilience_b = 1.0 - (clamp01(benchmark[i], 0.45) or 0.45)
        rr = r * resilience_b
        pts_b.append((cx + rr * cos(i * ang), cy + rr * sin(i * ang)))

    path_b = c.beginPath()
    path_b.moveTo(pts_b[0][0], pts_b[0][1])
    for p in pts_b[1:]:
        path_b.lineTo(p[0], p[1])
    path_b.close()

    c.setStrokeColor(colors.HexColor("#111827"))
    c.setLineWidth(1)
    c.drawPath(path_b, fill=0, stroke=1)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica", 10)
    label_offset = 16
    for i in range(n):
        lx = cx + (r + label_offset) * cos(i * ang)
        ly = cy + (r + label_offset) * sin(i * ang)
        c.drawCentredString(lx, ly, labels[i])
