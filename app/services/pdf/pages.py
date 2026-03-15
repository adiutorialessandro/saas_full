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
    lines = truncate_lines(wrap_text(text, font_name, font_size, width), max_lines)
    c.setFont(font_name, font_size)
    for i, line in enumerate(lines):
        c.drawString(x, y - i * leading_mm * mm, line)


def _section_divider(c: canvas.Canvas, y: float) -> None:
    c.setStrokeColorRGB(0.86, 0.89, 0.94)
    c.setLineWidth(0.8)
    c.line(M_L, y, M_L + SAFE_W, y)


def _get_color_by_status(status: str) -> tuple:
    status_upper = str(status).upper() if status else "GIALLO"
    if status_upper == "VERDE": return (39, 174, 96)
    if status_upper == "GIALLO": return (240, 165, 0)
    if status_upper == "ROSSO": return (197, 34, 31)
    if status_upper == "GOLD": return (212, 175, 55)
    return (136, 136, 136)


def _get_border_color_by_status(status: str) -> tuple:
    status_upper = str(status).upper() if status else "GIALLO"
    if status_upper == "VERDE": return (107, 142, 111)
    if status_upper == "GIALLO": return (163, 141, 107)
    if status_upper == "ROSSO": return (139, 107, 107)
    if status_upper == "GOLD": return (180, 150, 60)
    return (136, 136, 136)


def _draw_rounded_border_box(c: canvas.Canvas, x: float, y: float, width: float, height: float, border_left_color_rgb: tuple, border_top_color_rgb: tuple, radius: float = 8 * mm) -> None:
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#efefef"))
    c.setLineWidth(0.5)
    c.roundRect(x, y - height, width, height, radius=radius, fill=1, stroke=1)
    
    left_border_w = 12 * mm
    c.setFillColor(colors.Color(border_left_color_rgb[0]/255, border_left_color_rgb[1]/255, border_left_color_rgb[2]/255))
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
    
    c.setFillColor(colors.Color(border_top_color_rgb[0]/255, border_top_color_rgb[1]/255, border_top_color_rgb[2]/255))
    c.roundRect(x, y - 6*mm, width, 6*mm, radius=4*mm, fill=1, stroke=0)


def _health_label_from_triad(triad: Any) -> str:
    try: score = float(triad)
    except: score = 50.0
    if score >= 70: return "Healthy"
    if score >= 45: return "Watchlist"
    return "Critical"


# ==========================================
# PAGE 1: DIAGNOSI STRATEGICA & EFFETTO WOW
# ==========================================
def _page_0_strategic_diagnosis(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "Strategic Diagnosis & Daily Focus", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    overall_status = ctx.get("overall", "GIALLO")
    top_y = H - M_T - 18 * mm
    gap = 10 * mm
    col_w = (SAFE_W - gap) / 2
    card_h = 100 * mm

    # --- BOX SINISTRO: IL NUMERO MAGICO (GOLD) ---
    magic_data = ctx.get("magic_number", {})
    border_left_gold = _get_border_color_by_status("GOLD")
    border_top_gold = _get_color_by_status("GOLD")
    
    _draw_rounded_border_box(c, M_L, top_y, col_w, card_h, border_left_gold, border_top_gold)
    
    c_x = M_L + 10 * mm
    c_w = col_w - 20 * mm
    
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(c_x, top_y - 15 * mm, "🎯 Il tuo Numero Magico di Domani")
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(DEFAULT_MUTED)
    _draw_multiline(c, c_x, top_y - 28 * mm, "Non guardare il mese, guarda la singola poltrona.", c_w, "Helvetica-Bold", 10, 2)
    
    # Blocco Azione
    block_y = top_y - 42 * mm
    c.setFillColor(colors.HexColor("#FFF8E7")) 
    c.setStrokeColor(colors.HexColor("#FDE68A"))
    c.setLineWidth(0.5)
    c.roundRect(c_x, block_y - 25*mm, c_w, 25*mm, radius=4*mm, fill=1, stroke=1)
    
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#B45309")) 
    c.drawString(c_x + 5*mm, block_y - 6*mm, "AZIONE QUOTIDIANA OBIETTIVO")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(DEFAULT_TEXT)
    _draw_multiline(c, c_x + 5*mm, block_y - 13*mm, magic_data.get("azione", "Nessuna azione calcolata."), c_w - 10*mm, "Helvetica", 10, 3)

    # Blocco Impatto
    imp_y = block_y - 35 * mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#999999"))
    c.drawString(c_x, imp_y, "IMPATTO SUL SALONE:")
    c.setFont("Helvetica", 9)
    c.setFillColor(DEFAULT_TEXT)
    _draw_multiline(c, c_x, imp_y - 5*mm, magic_data.get("impatto", "Calcolo non disponibile."), c_w, "Helvetica-Bold", 9, 3)

    # --- BOX DESTRO: DIAGNOSI GENERALE E STAGIONALITÀ ---
    border_left_rgb = _get_border_color_by_status(overall_status)
    border_top_rgb = _get_color_by_status(overall_status)
    right_x = M_L + col_w + gap
    
    _draw_rounded_border_box(c, right_x, top_y, col_w, card_h, border_left_rgb, border_top_rgb)
    
    c_xr = right_x + 10 * mm
    c_wr = col_w - 20 * mm
    
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(c_xr, top_y - 15 * mm, "👔 Status & Stagionalità")
    
    # Badge Status
    status_badge_x_r = right_x + col_w - 35 * mm
    c.setFillColor(colors.Color(border_top_rgb[0]/255, border_top_rgb[1]/255, border_top_rgb[2]/255))
    c.roundRect(status_badge_x_r, top_y - 20 * mm, 30 * mm, 8 * mm, radius=2 * mm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.white)
    c.drawCentredString(status_badge_x_r + 15 * mm, top_y - 16.5 * mm, overall_status.upper())
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(DEFAULT_TEXT)
    c.drawString(c_xr, top_y - 28 * mm, "Fotografia Imprenditoriale")
    
    c.setFont("Helvetica", 8.5)
    _draw_multiline(c, c_xr, top_y - 34 * mm, ctx.get("hero_summary", ctx.get("summary", "")), c_wr, "Helvetica", 8.5, 4, leading_mm=3.8)
    
    # Blocco Stagionale
    seas_y = top_y - 55 * mm
    c.setFillColor(colors.HexColor("#F0F4FF"))
    c.setStrokeColor(colors.HexColor("#DDE4F0"))
    c.setLineWidth(0.3)
    c.roundRect(c_xr, seas_y - 20*mm, c_wr, 20*mm, radius=4*mm, fill=1, stroke=1)
    
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#3B82F6"))
    c.drawString(c_xr + 3*mm, seas_y - 5*mm, "FOCUS STAGIONALE (INTELLIGENZA ARTIFICIALE)")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(DEFAULT_TEXT)
    _draw_multiline(c, c_xr + 3*mm, seas_y - 11*mm, ctx.get("seasonal_tip", "Nessun consiglio stagionale."), c_wr - 6*mm, "Helvetica", 9, 3)

    # --- ROW 2: PRODUTTIVITÀ STAFF E MIX SERVIZI ---
    row2_y = top_y - card_h - 10 * mm
    card_h2 = 50 * mm
    
    # Staff Data
    staff_data = ctx.get("staff_data", {})
    st_stat = staff_data.get("status", "GIALLO")
    
    _draw_rounded_border_box(c, M_L, row2_y, col_w, card_h2, _get_border_color_by_status(st_stat), _get_color_by_status(st_stat))
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(M_L + 10*mm, row2_y - 15*mm, "👥 Produttività Oraria Staff")
    
    c.setFont("Helvetica", 10)
    c.drawString(M_L + 10*mm, row2_y - 25*mm, f"Resa Oraria: € {staff_data.get('resa', 0)}")
    c.drawString(M_L + 10*mm, row2_y - 32*mm, f"Costo Orario: € {staff_data.get('costo', 0)}")
    
    msg_staff = "VERDE - Margine sano sui dipendenti." if st_stat == "VERDE" else "ROSSO - I collaboratori lavorano con margine troppo basso."
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(_get_color_by_status(st_stat))
    _draw_multiline(c, M_L + 10*mm, row2_y - 42*mm, msg_staff, c_w - 5*mm, "Helvetica-Bold", 9, 2)
    
    # Tecnico vs Piega
    perc_tec = ctx.get("tecnico_perc", 0)
    tec_stat = "ROSSO" if perc_tec < 30 else "GIALLO" if perc_tec < 50 else "VERDE"
    
    _draw_rounded_border_box(c, right_x, row2_y, col_w, card_h2, _get_border_color_by_status(tec_stat), _get_color_by_status(tec_stat))
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(right_x + 10*mm, row2_y - 15*mm, "🎨 Mix Servizi (Alert Piegacificio)")
    
    c.setFont("Helvetica", 14)
    c.drawString(right_x + 10*mm, row2_y - 27*mm, f"{perc_tec}% Servizi Tecnici")
    
    msg_tec = "Sei un Salone Premium!" if tec_stat == "VERDE" else ("Attenzione: rischio Piegacificio!" if tec_stat == "ROSSO" else "Equilibrio buono, ma spingi i trattamenti.")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(_get_color_by_status(tec_stat))
    _draw_multiline(c, right_x + 10*mm, row2_y - 40*mm, msg_tec, c_wr - 5*mm, "Helvetica-Bold", 9, 2)

    footer(c, page_no, total)


# ==========================================
# PAGE 2: EXECUTIVE SUMMARY
# ==========================================
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

    shadow_card(c, right_x, card_y, right_w, card_h)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 13.6)
    c.drawString(right_x + 8 * mm, card_y + card_h - 11 * mm, "Lettura Sintetica")

    diagnosis_text = ctx.get("summary", "Dati sintetici non sufficienti per formulare un summary.")
    _draw_multiline(c, right_x + 8 * mm, card_y + card_h - 21 * mm, diagnosis_text, right_w - 16 * mm, "Helvetica", 10, 8)

    row2_y = card_y - 46 * mm
    row2_h = 36 * mm
    col_gap = 8 * mm
    col_w = (SAFE_W - 2 * col_gap) / 3

    decisions = ctx.get("decisions") or {}
    blocks = [
        ("Cassa & Finanza", decisions.get("cash") or "Mantieni sotto controllo incassi e spese settimanali."),
        ("Marginalità", decisions.get("margini") or "Focalizzati sull'aumento dello scontrino medio tecnico."),
        ("Acquisizione", decisions.get("acq") or "Migliora la fidelizzazione e le recensioni online."),
    ]

    for idx, (title, text) in enumerate(blocks):
        x = M_L + idx * (col_w + col_gap)
        shadow_card(c, x, row2_y, col_w, row2_h)
        c.setFillColor(DEFAULT_TEXT)
        c.setFont("Helvetica-Bold", 10.9)
        c.drawString(x + 6 * mm, row2_y + row2_h - 9 * mm, title)
        c.setFont("Helvetica", 9.0)
        _draw_multiline(c, x + 6 * mm, row2_y + row2_h - 17 * mm, text, col_w - 12 * mm, "Helvetica", 9.0, 3)

    footer(c, page_no, total)


# ==========================================
# PAGE 3: RISK SNAPSHOT
# ==========================================
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
    vals = [max(ctx.get('cash_r', 0.5), 0.05) * 100, max(ctx.get('marg_r', 0.5), 0.05) * 100, max(ctx.get('acq_r', 0.5), 0.05) * 100]
    draw_radar_chart(c, M_L + 5 * mm, chart_y + 5 * mm, 70 * mm, labels, vals)

    shadow_card(c, M_L + 90 * mm, chart_y, SAFE_W - 90 * mm, 70 * mm)
    drv = ctx.get("drivers", {})
    items = (drv.get("cash") or []) + (drv.get("margins") or drv.get("margini") or [])
    bullet_block(c, M_L + 98 * mm, chart_y + 60 * mm, SAFE_W - 106 * mm, "Top Driver Strategici", items[:4] if items else ["Dati operativi insufficienti"])
    
    footer(c, page_no, total)


# ==========================================
# PAGE 4: KPI DASHBOARD
# ==========================================
def _page_3_kpi(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "KPI Dashboard", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)
    
    top_y = H - M_T - 18 * mm
    gap = 7 * mm
    col_w = (SAFE_W - 2 * gap) / 3
    row_h = 34 * mm
    kpi = ctx.get("kpi") or {}

    cards = [
        ("Runway", fmt_num(kpi.get("runway_mesi"), 1, " mesi"), "Autonomia finanziaria", "GIALLO"),
        ("Break-even ratio", fmt_num(kpi.get("break_even_ratio"), 2), "Copertura costi", "GIALLO"),
        ("Conversione", fmt_pct(kpi.get("conversione"), 1), "Lead trasformati", "GIALLO"),
        ("Margine lordo", fmt_pct(kpi.get("margine_pct"), 1), "Qualità economica", "GIALLO"),
        ("Burn/Cash", fmt_pct(kpi.get("burn_cash_ratio"), 1), "Pressione su cassa", "GIALLO"),
        ("Incassi mese", fmt_money(kpi.get("incassi_mese")), "Ricavi periodo", "VERDE"),
    ]
    y1, y2 = top_y - row_h, top_y - 2 * row_h - 8 * mm
    for i, (t, v, s, l) in enumerate(cards[:3]): kpi_card(c, M_L + i * (col_w + gap), y1, col_w, row_h, t, v, s, l)
    for i, (t, v, s, l) in enumerate(cards[3:6]): kpi_card(c, M_L + i * (col_w + gap), y2, col_w, row_h, t, v, s, l)
    
    footer(c, page_no, total)


# ==========================================
# PAGE 5: STRATEGIC PRIORITIES & BENCHMARKS
# ==========================================
def _page_4_radar(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "Strategic Priorities & Benchmarks", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    
    # ===== BOX SINISTRO: DISTRIBUZIONE URGENZA =====
    left_x = M_L
    left_y = top_y - 90 * mm  
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
    right_y = left_y
    
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

                val_str = "—" if val is None else (f"{val*100:.1f}{suffix}" if is_pct else f"{val:.1f}{suffix}")
                tgt_str = "—" if tgt is None else (f"{tgt*100:.1f}{suffix}" if is_pct else f"{tgt:.1f}{suffix}")
                
                # Label
                c.setFillColor(DEFAULT_TEXT)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(right_x + 6 * mm, yy, label)
                
                # Value
                c.setFont("Helvetica", 9.5)
                c.drawString(right_x + 32 * mm, yy, val_str)
                
                # Target
                c.setFillColor(DEFAULT_MUTED)
                c.setFont("Helvetica", 8.8)
                c.drawString(right_x + 50 * mm, yy, f"Tgt: {tgt_str}")
                
                # Dot indicator
                status_color = DEFAULT_SUCCESS if status == 'VERDE' else (DEFAULT_WARNING if status == 'GIALLO' else DEFAULT_DANGER)
                c.setFillColor(status_color)
                c.circle(right_x + 70 * mm, yy + 0.8 * mm, 1.5 * mm, fill=1, stroke=0)
                
                c.setFillColor(DEFAULT_TEXT)
                yy -= 15 * mm
    else:
        c.setFont("Helvetica", 9)
        c.setFillColor(DEFAULT_MUTED)
        c.drawString(right_x + 6 * mm, right_y + left_h - 40 * mm, "Dati non disponibili per il settore.")

    footer(c, page_no, total)


# ==========================================
# PAGE 6: ROADMAP OPERATIVA (90 GIORNI)
# ==========================================
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
            owner = item.get("owner", "Team Salone")
            target_kpi = item.get("target_kpi", "—")
            target_value = item.get("target_value", "—")
        else:
            week = "1-4"
            action = str(item)
            owner = "Titolare"
            target_kpi = "Miglioramento"
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

        if target_value and target_value != "—":
            c.setFont("Helvetica-Oblique", 8.8)
            c.drawString(M_L + 8 * mm, meta_y - 4.5 * mm, f"Target: {target_value}")
            line_y = meta_y - 9 * mm
        else:
            line_y = meta_y - 4.5 * mm

        c.setStrokeColorRGB(0.86, 0.89, 0.94)
        c.setLineWidth(0.6)
        c.line(M_L + 8 * mm, line_y, M_L + SAFE_W - 8 * mm, line_y)

        row_y -= 26 * mm

    footer(c, page_no, total)


# ==========================================
# ONE-PAGER EXECUTIVE SUMMARY
# ==========================================
def _one_pager_executive(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(c, "Executive One Pager", f"{ctx.get('settore', '')} · {ctx.get('mese', '')}", ctx.get("overall", "GIALLO"))
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    gap = 8 * mm
    col_w = (SAFE_W - 2 * gap) / 3

    y = top_y - 32 * mm
    kpi_card(c, M_L, y, col_w, 30 * mm, "Triad Score", f"{int(round(ctx.get('triad', 50)))}/100", "Business Stability Score", ctx.get("overall", "GIALLO"))
    kpi_card(c, M_L + col_w + gap, y, col_w, 30 * mm, "Risk Profile", ctx.get("risk_profile") or "Operativo", "Profilo dominante", "VERDE")
    kpi_card(c, M_L + 2 * (col_w + gap), y, col_w, 30 * mm, "Confidence", f"{ctx.get('confidence', '—')}%", "Affidabilità del report", "VERDE")

    draw_radar_chart(c, M_L + 100 * mm, H - M_T - 60 * mm, 60 * mm, ['C', 'M', 'A'], [ctx.get("cash_r",0.5)*100, ctx.get("marg_r",0.5)*100, ctx.get("acq_r",0.5)*100])

    row2_top = y - 46 * mm
    left_w = (SAFE_W - gap) / 2

    shadow_card(c, M_L, row2_top - 46 * mm, left_w, 46 * mm)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 8 * mm, row2_top - 10 * mm, "Executive Strategic Summary")
    _draw_multiline(c, M_L + 8 * mm, row2_top - 19 * mm, ctx.get("summary") or "Dati in elaborazione...", left_w - 16 * mm, "Helvetica", 9.5, 6)

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


# ==========================================
# GESTORI DELLA STAMPA PDF
# ==========================================
def render_scan_pages(c: canvas.Canvas, ctx: Dict[str, Any]) -> None:
    """Renderizza tutte le 6 pagine del report standard"""
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
    """Renderizza il one-pager riassuntivo (1 pagina)"""
    _one_pager_executive(c, ctx, 1, 1)