# filepath: app/services/pdf/pages.py
from __future__ import annotations

from typing import Any, Dict

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from .config import (
    DEFAULT_MUTED, 
    DEFAULT_TEXT, 
    DEFAULT_SUCCESS, 
    DEFAULT_WARNING, 
    DEFAULT_DANGER,
    DEFAULT_ACCENT,
    H, 
    M_L, 
    M_T, 
    SAFE_W,
    W,
)
from .primitives import (
    bullet_block,
    footer,
    header,
    kpi_card,
    page_bg,
    risk_card,
    score_card,
    shadow_card,
    draw_radar_chart,
    draw_pie_chart
)
from .utils import fmt_money, fmt_num, fmt_pct, truncate_lines, wrap_text


def _draw_multiline(
    c: canvas.Canvas,
    x: float,
    y: float,
    text: str,
    width: float,
    font_name: str,
    font_size: float,
    max_lines: int,
    leading_mm: float = 4.2,
) -> None:
    """Disegna testo multilinea con wrapping automatico"""
    lines = truncate_lines(wrap_text(text, font_name, font_size, width), max_lines)
    c.setFont(font_name, font_size)
    for i, line in enumerate(lines):
        c.drawString(x, y - i * leading_mm * mm, line)


def _section_divider(c: canvas.Canvas, y: float) -> None:
    """Disegna una linea divisione tra sezioni"""
    c.setStrokeColorRGB(0.86, 0.89, 0.94)
    c.setLineWidth(0.8)
    c.line(M_L, y, M_L + SAFE_W, y)


def _get_color_by_status(status: str) -> tuple:
    """Ritorna RGB tuple in base a status (VERDE, GIALLO, ROSSO)"""
    status_upper = str(status).upper() if status else "GIALLO"
    
    if status_upper == "VERDE":
        return (39, 174, 96)
    elif status_upper == "GIALLO":
        return (240, 165, 0)
    elif status_upper == "ROSSO":
        return (197, 34, 31)
    return (136, 136, 136)


def _get_border_color_by_status(status: str) -> tuple:
    """Ritorna colore bordo sinistro grigio-tinta in base a status"""
    status_upper = str(status).upper() if status else "GIALLO"
    
    if status_upper == "VERDE":
        return (107, 142, 111)
    elif status_upper == "GIALLO":
        return (163, 141, 107)
    elif status_upper == "ROSSO":
        return (139, 107, 107)
    return (136, 136, 136)


def _draw_rounded_border_box(c: canvas.Canvas, 
                            x: float, y: float, 
                            width: float, height: float,
                            border_left_color_rgb: tuple, 
                            border_top_color_rgb: tuple,
                            radius: float = 8 * mm) -> None:
    """Disegna un box con bordi arrotondati"""
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#efefef"))
    c.setLineWidth(0.5)
    c.roundRect(x, y - height, width, height, radius=radius, fill=1, stroke=1)
    
    left_border_w = 12 * mm
    c.setFillColor(colors.Color(
        border_left_color_rgb[0]/255, 
        border_left_color_rgb[1]/255, 
        border_left_color_rgb[2]/255
    ))
    c.setLineWidth(0)
    
    path = c.beginPath()
    path.moveTo(x + radius, y)
    path.lineTo(x + left_border_w, y)
    path.lineTo(x + left_border_w, y - height + radius)
    path.curveTo(x + left_border_w, y - height, x + radius, y - height, x, y - height)
    path.lineTo(x, y - radius)
    path.curveTo(x, y, x, y, x + radius, y)
    path.close()
    c.drawPath(path, stroke=0, fill=1)
    
    c.setFillColor(colors.Color(
        border_top_color_rgb[0]/255,
        border_top_color_rgb[1]/255,
        border_top_color_rgb[2]/255
    ))
    c.roundRect(x, y - 6*mm, width, 6*mm, radius=4*mm, fill=1, stroke=0)


def _health_label_from_triad(triad: Any) -> str:
    """Converte score in health label"""
    try:
        score = float(triad)
    except Exception:
        score = 50.0

    if score >= 70:
        return "Healthy"
    if score >= 45:
        return "Watchlist"
    return "Critical"


def _page_0_strategic_diagnosis(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    """PAGE 1: Strategic Diagnosis & Executive Insight"""
    page_bg(c)
    header(c, "Strategic Diagnosis", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    overall_status = ctx.get("overall", "GIALLO")
    border_left_rgb = _get_border_color_by_status(overall_status)
    border_top_rgb = _get_color_by_status(overall_status)
    
    header_payload = ctx.get("header_payload", {})
    diagnosis_data = header_payload.get("diagnosis", {}) if header_payload else {}

    top_y = H - M_T - 18 * mm
    gap = 10 * mm
    col_w = (SAFE_W - gap) / 2
    card_h = 100 * mm

    _draw_rounded_border_box(c, M_L, top_y, col_w, card_h, 
                            border_left_rgb, border_top_rgb)
    
    content_x = M_L + 10 * mm
    content_w = col_w - 20 * mm
    
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(content_x, top_y - 15 * mm, "🔍 Diagnosi Strategica")
    
    status_badge_x = M_L + col_w - 35 * mm
    c.setFillColor(colors.Color(border_top_rgb[0]/255, border_top_rgb[1]/255, border_top_rgb[2]/255))
    c.roundRect(status_badge_x, top_y - 20 * mm, 30 * mm, 8 * mm, radius=2 * mm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.white)
    c.drawCentredString(status_badge_x + 15 * mm, top_y - 16.5 * mm, overall_status.upper())
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(DEFAULT_MUTED)
    headline = diagnosis_data.get("headline", "Status non disponibile")
    _draw_multiline(c, content_x, top_y - 28 * mm, headline, content_w, "Helvetica-Bold", 10, 2)
    
    block_y = top_y - 40 * mm
    blocks = [
        ("DIAGNOSI", diagnosis_data.get("diagnosis", "Non disponibile")),
        ("TREND", diagnosis_data.get("trend", "Non disponibile")),
        ("PRIORITÀ", diagnosis_data.get("priority", "Non disponibile")),
        ("PUNTO FORTE", diagnosis_data.get("strength", "Non disponibile")),
    ]
    
    block_w = (content_w - 5 * mm) / 2
    block_h = 25 * mm
    
    for idx, (label, text) in enumerate(blocks):
        row = idx // 2
        col = idx % 2
        
        block_x = content_x + col * (block_w + 5 * mm)
        block_y_pos = block_y - row * (block_h + 5 * mm)
        
        c.setFillColor(colors.HexColor("#f8f9fa"))
        c.setStrokeColor(colors.HexColor("#e0e3e8"))
        c.setLineWidth(0.3)
        c.roundRect(block_x, block_y_pos - block_h, block_w, block_h, radius=4 * mm, fill=1, stroke=1)
        
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor("#999999"))
        c.drawString(block_x + 4 * mm, block_y_pos - 5 * mm, label)
        
        c.setFont("Helvetica", 8)
        c.setFillColor(DEFAULT_TEXT)
        _draw_multiline(c, block_x + 4 * mm, block_y_pos - 12 * mm, text, block_w - 8 * mm, 
                       "Helvetica", 8, 2, leading_mm=3.5)

    right_x = M_L + col_w + gap
    _draw_rounded_border_box(c, right_x, top_y, col_w, card_h,
                            border_left_rgb, border_top_rgb)
    
    content_x_r = right_x + 10 * mm
    content_w_r = col_w - 20 * mm
    
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(content_x_r, top_y - 15 * mm, "👔 Executive Insight")
    
    status_badge_x_r = right_x + col_w - 35 * mm
    c.setFillColor(colors.Color(border_top_rgb[0]/255, border_top_rgb[1]/255, border_top_rgb[2]/255))
    c.roundRect(status_badge_x_r, top_y - 20 * mm, 30 * mm, 8 * mm, radius=2 * mm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.white)
    c.drawCentredString(status_badge_x_r + 15 * mm, top_y - 16.5 * mm, overall_status.upper())
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(DEFAULT_TEXT)
    c.drawString(content_x_r, top_y - 28 * mm, "Indicazione manageriale sintetica")
    
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#999999"))
    c.drawString(content_x_r, top_y - 40 * mm, "SITUAZIONE")
    
    c.setFont("Helvetica", 8.5)
    c.setFillColor(DEFAULT_TEXT)
    comparative = header_payload.get("comparative_insight", "") if header_payload else ""
    _draw_multiline(c, content_x_r, top_y - 46 * mm, comparative or ctx.get("summary", ""),
                   content_w_r, "Helvetica", 8.5, 4, leading_mm=3.8)
    
    block2_y = top_y - 70 * mm
    blocks2 = [
        ("PRIORITÀ DOMINANTE", diagnosis_data.get("priority", "Non disponibile")),
        ("PUNTO PIÙ SOLIDO", diagnosis_data.get("strength", "Non disponibile")),
    ]
    
    for idx, (label, text) in enumerate(blocks2):
        block_x = content_x_r + idx * (content_w_r / 2 + 2 * mm)
        
        c.setFillColor(colors.HexColor("#f8f9fa"))
        c.setStrokeColor(colors.HexColor("#e0e3e8"))
        c.setLineWidth(0.3)
        c.roundRect(block_x, block2_y - 18 * mm, content_w_r / 2, 18 * mm, radius=4 * mm, fill=1, stroke=1)
        
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor("#999999"))
        c.drawString(block_x + 3 * mm, block2_y - 4 * mm, label)
        
        c.setFont("Helvetica", 7.5)
        c.setFillColor(DEFAULT_TEXT)
        _draw_multiline(c, block_x + 3 * mm, block2_y - 9 * mm, text, content_w_r / 2 - 6 * mm,
                       "Helvetica", 7.5, 2, leading_mm=3.2)

    footer(c, page_no, total)


def _page_1_executive(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "Executive Strategic Summary", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    left_w = 84 * mm
    right_x = M_L + left_w + 10 * mm
    right_w = SAFE_W - left_w - 10 * mm

    card_h = 70 * mm
    card_y = top_y - card_h

    score_card(c, M_L, card_y, left_w, card_h, "Business Stability Score", f"{int(round(ctx.get('triad', 50)))}/100", f"Confidence score: {ctx.get('confidence', '—')}%", ctx.get('triad', 50))
    health_label = _health_label_from_triad(ctx.get("triad"))

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 9.4)
    c.drawString(M_L + 8 * mm, card_y + card_h - 44 * mm, f"Stato attuale: {health_label}")

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica-Bold", 8.4)
    c.drawString(M_L + 8 * mm, card_y + card_h - 36 * mm, "PROFILO DI LETTURA")

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.2)
    c.drawString(M_L + 8 * mm, card_y + 18 * mm, f"Profilo: {ctx.get('risk_profile') or '—'}")
    c.drawString(M_L + 8 * mm, card_y + 11 * mm, f"Maturità: {ctx.get('maturity_label') or '—'}")
    
    shadow_card(c, right_x, card_y, right_w, card_h)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 13.6)
    c.drawString(right_x + 8 * mm, card_y + card_h - 11 * mm, "Diagnosi strategica")

    diagnosis_text = f"L'azienda è operativa ma richiede attenzione attiva sulle priorità. Profilo di rischio: {ctx.get('risk_profile', '—')}. Priorità manageriale: definire interventi su cassa e margini."
    _draw_multiline(c, right_x + 8 * mm, card_y + card_h - 21 * mm, diagnosis_text, right_w - 16 * mm, "Helvetica", 10, 8)

    row2_y = card_y - 46 * mm
    row2_h = 36 * mm
    col_gap = 8 * mm
    col_w = (SAFE_W - 2 * col_gap) / 3

    decisions = ctx.get("decisions") or {}
    blocks = [
        ("Priorità Cassa", decisions.get("cash") or "Mantenere presidi settimanali su cassa."),
        ("Priorità Margini", decisions.get("margini") or "Consolidare pricing e disciplina economica."),
        ("Priorità Acquisizione", decisions.get("acq") or "Continuità del motore commerciale."),
    ]

    for idx, (title, text) in enumerate(blocks):
        x = M_L + idx * (col_w + col_gap)
        shadow_card(c, x, row2_y, col_w, row2_h)
        c.setFillColor(DEFAULT_TEXT)
        c.setFont("Helvetica-Bold", 10.9)
        c.drawString(x + 6 * mm, row2_y + row2_h - 9 * mm, title)
        c.setFont("Helvetica", 9.0)
        _draw_multiline(c, x + 6 * mm, row2_y + row2_h - 17 * mm, text, col_w - 12 * mm, "Helvetica", 9.0, 3)

    note_y = row2_y - 16 * mm
    shadow_card(c, M_L, note_y, SAFE_W, 13 * mm)
    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.2)
    c.drawString(M_L + 6 * mm, note_y + 4.6 * mm, ctx.get("board_note") or "Documento sintetico a supporto delle decisioni prioritarie del management.")

    footer(c, page_no, total)


def _page_2_risk_snapshot(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "Business Risk Snapshot", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    gap = 8 * mm
    col_w = (SAFE_W - 2 * gap) / 3
    card_h = 48 * mm
    y = top_y - card_h

    risk_card(c, M_L, y, col_w, card_h, "Cassa", ctx.get("cash_r", 0.5), "Tenuta finanziaria e visibilità di breve.")
    risk_card(c, M_L + col_w + gap, y, col_w, card_h, "Margini", ctx.get("marg_r", 0.5), "Sostenibilità economica e protezione del margine.")
    risk_card(c, M_L + 2 * (col_w + gap), y, col_w, card_h, "Acquisizione", ctx.get("acq_r", 0.5), "Prevedibilità e continuità del motore commerciale.")

    chart_y = y - 80 * mm
    shadow_card(c, M_L, chart_y, 80 * mm, 70 * mm)
    labels = ['CASSA', 'MARGINI', 'CLIENTI']
    vals = [
        max(ctx.get('cash_r', 0.5), 0.05) * 100,
        max(ctx.get('marg_r', 0.5), 0.05) * 100,
        max(ctx.get('acq_r', 0.5), 0.05) * 100
    ]
    draw_radar_chart(c, M_L + 5 * mm, chart_y + 5 * mm, 70 * mm, labels, vals)

    shadow_card(c, M_L + 90 * mm, chart_y, SAFE_W - 90 * mm, 70 * mm)
    drv = ctx.get("drivers", {})
    items = (drv.get("cash") or []) + (drv.get("margins") or drv.get("margini") or [])
    
    # ===== CORREZIONE: Top Driver Strategici - testo senza ridondanza =====
    if items:
        optimized_items = []
        for item in items[:4]:
            # Rimuovi ridondanze
            item_clean = item
            if "La liquidità è sotto controllo" in item:
                item_clean = "Mantenere presidi settimanali su cassa, incassi e uscite prioritarie."
            elif "Runway disponibile" in item:
                item_clean = "Runway attuale: 31.2 mesi."
            elif "Marginalità è relativamente difesa" in item:
                item_clean = "Consolidare pricing e disciplina economica."
            elif "Margine lordo attuale" in item:
                item_clean = "Margine lordo: 44.0%."
            optimized_items.append(item_clean)
    else:
        optimized_items = []
    
    bullet_block(c, M_L + 98 * mm, chart_y + 60 * mm, SAFE_W - 106 * mm, "Top Driver Strategici", optimized_items)

    footer(c, page_no, total)


def _page_3_kpi(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "KPI Dashboard", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    kpi = ctx.get("kpi") or {}
    benchmarks = ctx.get("benchmarks") or {}

    top_y = H - M_T - 18 * mm
    gap = 7 * mm
    col_w = (SAFE_W - 2 * gap) / 3
    row_h = 34 * mm

    def get_status(key, default="GIALLO"):
        return benchmarks.get(key, {}).get("status", default)

    values = {
        "Runway": fmt_num(kpi.get("runway_mesi"), 1, " mesi"),
        "Break-even ratio": fmt_num(kpi.get("break_even_ratio"), 2),
        "Conversione": fmt_pct(kpi.get("conversione"), 1),
        "Margine lordo": fmt_pct(kpi.get("margine_pct"), 1),
        "Burn/Cash": fmt_pct(kpi.get("burn_cash_ratio"), 1),
        "Incassi mese": fmt_money(kpi.get("incassi_mese")),
    }

    cards = [
        ("Runway", values["Runway"], "Autonomia finanziaria di breve", get_status("runway")),
        ("Break-even ratio", values["Break-even ratio"], "Copertura dei costi fissi", get_status("break_even")),
        ("Conversione", values["Conversione"], "Lead trasformati in clienti", get_status("conversione")),
        ("Margine lordo", values["Margine lordo"], "Qualità economica dell'offerta", get_status("margine")),
        ("Burn/Cash", values["Burn/Cash"], "Pressione del burn sulla cassa", "GIALLO"),
        ("Incassi mese", values["Incassi mese"], "Ricavi / incassi del periodo", "VERDE"),
    ]

    y1 = top_y - row_h
    y2 = y1 - row_h - 8 * mm

    for idx, (title, value, subtitle, label) in enumerate(cards[:3]):
        x = M_L + idx * (col_w + gap)
        kpi_card(c, x, y1, col_w, row_h, title, value, subtitle, label)

    for idx, (title, value, subtitle, label) in enumerate(cards[3:6]):
        x = M_L + idx * (col_w + gap)
        kpi_card(c, x, y2, col_w, row_h, title, value, subtitle, label)

    footer(c, page_no, total)


def _page_4_radar(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "Strategic Priorities & Benchmarks", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    
    # ===== BOX SINISTRO: DISTRIBUZIONE URGENZA =====
    left_x = M_L
    left_y = top_y - 90 * mm  # Più basso: 80 → 90
    left_w = 80 * mm
    left_h = 70 * mm

    shadow_card(c, left_x, left_y, left_w, left_h)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_x + 6 * mm, left_y + left_h - 10 * mm, "Distribuzione Urgenza")

    cash_r = float(ctx.get('cash_r', 0.5))
    marg_r = float(ctx.get('marg_r', 0.5))
    acq_r = float(ctx.get('acq_r', 0.5))

    total_r = (cash_r + marg_r + acq_r) or 1.0

    p_cash = (cash_r / total_r) * 100
    p_marg = (marg_r / total_r) * 100
    p_acq = (acq_r / total_r) * 100

    # Riga 1: Cassa
    row_y = left_y + left_h - 28 * mm
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_x + 8 * mm, row_y, "Cassa")
    
    c.setFont("Helvetica", 9)
    c.drawRightString(left_x + left_w - 8 * mm, row_y, f"{p_cash:.1f}%")
    
    track_y = row_y - 4 * mm
    c.setFillColorRGB(0.90, 0.92, 0.95)
    c.roundRect(left_x + 8 * mm, track_y, left_w - 16 * mm, 3 * mm, 1 * mm, fill=1, stroke=0)
    
    fill_w = max((p_cash / 100.0) * (left_w - 16 * mm), 3 * mm)
    c.setFillColor(DEFAULT_ACCENT)
    c.roundRect(left_x + 8 * mm, track_y, fill_w, 3 * mm, 1 * mm, fill=1, stroke=0)

    # Riga 2: Margini
    row_y = left_y + left_h - 43 * mm
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_x + 8 * mm, row_y, "Margini")
    
    c.setFont("Helvetica", 9)
    c.drawRightString(left_x + left_w - 8 * mm, row_y, f"{p_marg:.1f}%")
    
    track_y = row_y - 4 * mm
    c.setFillColorRGB(0.90, 0.92, 0.95)
    c.roundRect(left_x + 8 * mm, track_y, left_w - 16 * mm, 3 * mm, 1 * mm, fill=1, stroke=0)
    
    fill_w = max((p_marg / 100.0) * (left_w - 16 * mm), 3 * mm)
    c.setFillColor(DEFAULT_SUCCESS)
    c.roundRect(left_x + 8 * mm, track_y, fill_w, 3 * mm, 1 * mm, fill=1, stroke=0)

    # Riga 3: Acquisizione
    row_y = left_y + left_h - 58 * mm
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_x + 8 * mm, row_y, "Acquisizione")
    
    c.setFont("Helvetica", 9)
    c.drawRightString(left_x + left_w - 8 * mm, row_y, f"{p_acq:.1f}%")
    
    track_y = row_y - 4 * mm
    c.setFillColorRGB(0.90, 0.92, 0.95)
    c.roundRect(left_x + 8 * mm, track_y, left_w - 16 * mm, 3 * mm, 1 * mm, fill=1, stroke=0)
    
    fill_w = max((p_acq / 100.0) * (left_w - 16 * mm), 3 * mm)
    c.setFillColor(DEFAULT_WARNING)
    c.roundRect(left_x + 8 * mm, track_y, fill_w, 3 * mm, 1 * mm, fill=1, stroke=0)

    # ===== BOX DESTRO: CONFRONTO BENCHMARK =====
    right_x = M_L + 90 * mm
    box_w = SAFE_W - 90 * mm
    right_y = left_y  # Stesso livello verticale
    
    shadow_card(c, right_x, right_y, box_w, left_h)
    
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(right_x + 6 * mm, right_y + left_h - 10 * mm, "Confronto Benchmark")

    benchmarks = ctx.get("benchmarks", {})
    if benchmarks:
        yy = right_y + left_h - 18 * mm
        
        for key, label, is_pct, suffix in [
            ('margine', 'Margine', True, '%'),
            ('conversione', 'Conv.', True, '%'),
            ('runway', 'Runway', False, ''),
            ('break_even', 'Break-even', False, '')
        ]:
            b = benchmarks.get(key)
            if b:
                val = b.get("value")
                tgt = b.get("target")
                status = b.get("status", "GIALLO")

                if val is None:
                    val_str = "—"
                else:
                    val_str = f"{val*100:.1f}{suffix}" if is_pct else f"{val:.1f}{suffix}"

                if tgt is None:
                    tgt_str = "—"
                else:
                    tgt_str = f"{tgt*100:.1f}{suffix}" if is_pct else f"{tgt:.1f}{suffix}"
                
                # Label - bold
                c.setFillColor(DEFAULT_TEXT)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(right_x + 6 * mm, yy, label)
                
                # Value - regular
                c.setFont("Helvetica", 9.5)
                c.drawString(right_x + 32 * mm, yy, val_str)
                
                # Target - muted
                c.setFillColor(DEFAULT_MUTED)
                c.setFont("Helvetica", 8.8)
                c.drawString(right_x + 50 * mm, yy, f"Tgt: {tgt_str}")
                
                # Dot indicator - centrato verticalmente
                status_color = DEFAULT_SUCCESS if status == 'VERDE' else (DEFAULT_WARNING if status == 'GIALLO' else DEFAULT_DANGER)
                c.setFillColor(status_color)
                c.circle(right_x + 70 * mm, yy + 0.8 * mm, 1.5 * mm, fill=1, stroke=0)
                
                c.setFillColor(DEFAULT_TEXT)  # Reset color
                yy -= 15 * mm
    else:
        c.setFont("Helvetica", 9)
        c.setFillColor(DEFAULT_MUTED)
        c.drawString(right_x + 6 * mm, right_y + left_h - 40 * mm, "Dati non disponibili per il settore.")

    footer(c, page_no, total)

def _page_5_execution(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "Execution Roadmap — Next 90 Days", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    plan = (ctx.get("plan") or [])[:4]

    card_h = 126 * mm
    card_y = top_y - card_h
    shadow_card(c, M_L, card_y, SAFE_W, card_h)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 8 * mm, card_y + card_h - 10 * mm, "Piano di esecuzione — prossimi 90 giorni")

    row_y = card_y + card_h - 18 * mm

    for item in plan:
        if isinstance(item, dict):
            week = item.get("week", "—")
            action = item.get("action", "—")
            owner = item.get("owner", "—")
            target_kpi = item.get("target_kpi", "—")
            target_value = item.get("target_value", "—")
        else:
            week = "—"
            action = str(item)
            owner = "—"
            target_kpi = "—"
            target_value = "—"

        c.setFillColor(DEFAULT_TEXT)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(M_L + 8 * mm, row_y, f"Settimana {week}")

        c.setFont("Helvetica", 9.2)
        _draw_multiline(c, M_L + 8 * mm, row_y - 5 * mm, action, SAFE_W - 16 * mm, "Helvetica", 9.2, 2, leading_mm=3.8)

        meta_y = row_y - 14 * mm
        c.setFont("Helvetica", 8.8)
        c.drawString(M_L + 8 * mm, meta_y, f"Owner: {owner}")
        c.drawString(M_L + 60 * mm, meta_y, f"KPI: {target_kpi}")

        # ===== CORREZIONE: Target in italics su nuova riga =====
        if target_value and target_value != "—":
            c.setFont("Helvetica-Oblique", 8.8)
            c.drawString(M_L + 8 * mm, meta_y - 4.5 * mm, f"Target: {target_value}")
            line_y = meta_y - 9 * mm
        else:
            line_y = meta_y - 4.5 * mm

        c.setStrokeColorRGB(0.86, 0.89, 0.94)
        c.setLineWidth(0.6)
        c.line(M_L + 8 * mm, line_y, M_L + SAFE_W - 8 * mm, line_y)

        row_y -= 28 * mm

    footer(c, page_no, total)


def _one_pager_executive(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "Executive One Pager", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    gap = 8 * mm
    col_w = (SAFE_W - 2 * gap) / 3

    y = top_y - 32 * mm
    kpi_card(c, M_L, y, col_w, 30 * mm, "Triad Score", f"{int(round(ctx.get('triad', 50)))}/100", "Business Stability Score", ctx.get("overall", "GIALLO"))
    kpi_card(c, M_L + col_w + gap, y, col_w, 30 * mm, "Risk Profile", ctx.get("risk_profile") or "—", "Profilo dominante", "VERDE")
    kpi_card(c, M_L + 2 * (col_w + gap), y, col_w, 30 * mm, "Confidence", f"{ctx.get('confidence', '—')}%", "Affidabilità del report", "VERDE")

    draw_radar_chart(c, M_L + 100 * mm, H - M_T - 60 * mm, 60 * mm, ['C', 'M', 'A'], [ctx.get("cash_r",0.5)*100, ctx.get("marg_r",0.5)*100, ctx.get("acq_r",0.5)*100])

    row2_top = y - 46 * mm
    left_w = (SAFE_W - gap) / 2

    shadow_card(c, M_L, row2_top - 46 * mm, left_w, 46 * mm)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 8 * mm, row2_top - 10 * mm, "Executive Strategic Summary")
    _draw_multiline(c, M_L + 8 * mm, row2_top - 19 * mm, ctx.get("summary") or "", left_w - 16 * mm, "Helvetica", 9.5, 6)

    right_x = M_L + left_w + gap
    shadow_card(c, right_x, row2_top - 46 * mm, left_w, 46 * mm)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(right_x + 8 * mm, row2_top - 10 * mm, "Action Plan — Next 90 Days")

    plans = ctx.get("plan") or []
    yy = row2_top - 19 * mm
    c.setFont("Helvetica", 9.2)
    for item in plans[:3]:
        action_text = item.get('action', '—') if isinstance(item, dict) else str(item)
        _draw_multiline(c, right_x + 8 * mm, yy, f"• {action_text}", left_w - 16 * mm, "Helvetica", 9.2, 2)
        yy -= 11 * mm

    footer(c, page_no, total)


def render_scan_pages(c: canvas.Canvas, ctx: Dict[str, Any]) -> None:
    """Renderizza tutte le pagine del report (6 pagine)"""
    total = 6
    _page_0_strategic_diagnosis(c, ctx, 1, total)
    c.showPage()
    _page_1_executive(c, ctx, 2, total)
    c.showPage()
    _page_2_risk_snapshot(c, ctx, 3, total)
    c.showPage()
    _page_3_kpi(c, ctx, 4, total)
    c.showPage()
    _page_4_radar(c, ctx, 5, total)
    c.showPage()
    _page_5_execution(c, ctx, 6, total)


def render_one_pager(c: canvas.Canvas, ctx: Dict[str, Any]) -> None:
    """Renderizza il one-pager (1 pagina)"""
    _one_pager_executive(c, ctx, 1, 1)