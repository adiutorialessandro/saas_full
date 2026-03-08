from __future__ import annotations

from typing import Any, Dict

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .config import DEFAULT_MUTED, DEFAULT_TEXT, H, M_L, M_T, SAFE_W
from .primitives import (
    bullet_block,
    footer,
    header,
    kpi_card,
    page_bg,
    risk_card,
    score_card,
    shadow_card,
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


def _health_label_from_triad(triad: Any) -> str:
    try:
        score = float(triad)
    except Exception:
        score = 50.0

    if score >= 70:
        return "Healthy"
    if score >= 45:
        return "Watchlist"
    return "Critical"


def _diagnosis_from_ctx(ctx: Dict[str, Any]) -> str:
    health = _health_label_from_triad(ctx.get("triad"))
    risk_profile = ctx.get("risk_profile") or "profilo non disponibile"
    maturity = ctx.get("maturity_label") or "maturità non disponibile"
    decisions = ctx.get("decisions") or {}

    if health == "Healthy":
        opening = "L’azienda mostra una struttura complessivamente solida."
    elif health == "Watchlist":
        opening = "L’azienda è operativa ma richiede attenzione attiva sulle priorità."
    else:
        opening = "L’azienda presenta una fragilità che richiede interventi ravvicinati."

    dominant = decisions.get("cash") or decisions.get("margini") or decisions.get("acq") or "Definire una priorità manageriale più netta."

    return (
        f"{opening} Il profilo di rischio attuale indica: {risk_profile}. "
        f"{maturity}. Priorità manageriale: {dominant}"
    )


def _page_1_executive(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(
        c,
        "Executive Strategic Summary",
        f"{ctx['settore']} · {ctx['modello']} · {ctx['mese']}",
        ctx["overall"],
    )
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    left_w = 84 * mm
    right_x = M_L + left_w + 10 * mm
    right_w = SAFE_W - left_w - 10 * mm

    card_h = 70 * mm
    card_y = top_y - card_h

    score_card(
        c,
        M_L,
        card_y,
        left_w,
        card_h,
        "Business Stability Score",
        f"{int(round(ctx['triad']))}/100",
        f"Confidence score: {ctx.get('confidence', '—')}%",
        ctx["triad"],
    )

    health_label = _health_label_from_triad(ctx.get("triad"))

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 9.4)
    c.drawString(M_L + 8 * mm, card_y + card_h - 44 * mm, f"Stato attuale: {health_label}")

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica-Bold", 8.4)
    c.drawString(M_L + 8 * mm, card_y + card_h - 36 * mm, "PROFILO DI LETTURA")

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.2)
    c.drawString(M_L + 8 * mm, card_y + 17 * mm, f"Profilo: {ctx.get('risk_profile') or '—'}")
    c.drawString(M_L + 8 * mm, card_y + 10 * mm, f"Maturità: {ctx.get('maturity_label') or '—'}")

    shadow_card(c, right_x, card_y, right_w, card_h)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 13.6)
    c.drawString(right_x + 8 * mm, card_y + card_h - 11 * mm, "Diagnosi strategica")

    _draw_multiline(
        c,
        right_x + 8 * mm,
        card_y + card_h - 21 * mm,
        _diagnosis_from_ctx(ctx),
        right_w - 16 * mm,
        "Helvetica",
        10,
        8,
    )

    row2_y = card_y - 46 * mm
    row2_h = 36 * mm
    col_gap = 8 * mm
    col_w = (SAFE_W - 2 * col_gap) / 3

    decisions = ctx.get("decisions") or {}

    blocks = [
        ("Priorità Cassa", decisions.get("cash") or "—"),
        ("Priorità Margini", decisions.get("margini") or "—"),
        ("Priorità Acquisizione", decisions.get("acq") or "—"),
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
    c.drawString(
        M_L + 6 * mm,
        note_y + 4.6 * mm,
        ctx.get("board_note") or "Documento sintetico a supporto delle decisioni prioritarie del management.",
    )

    footer(c, page_no, total)


def _page_2_risk_snapshot(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(
        c,
        "Business Risk Snapshot",
        f"{ctx['settore']} · {ctx['mese']}",
        ctx["overall"],
    )
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    gap = 8 * mm
    col_w = (SAFE_W - 2 * gap) / 3
    card_h = 48 * mm
    y = top_y - card_h

    risk_card(c, M_L, y, col_w, card_h, "Cassa", ctx["cash_r"], "Tenuta finanziaria e visibilità di breve.")
    risk_card(c, M_L + col_w + gap, y, col_w, card_h, "Margini", ctx["marg_r"], "Sostenibilità economica e protezione del margine.")
    risk_card(c, M_L + 2 * (col_w + gap), y, col_w, card_h, "Acquisizione", ctx["acq_r"], "Prevedibilità e continuità del motore commerciale.")

    drv_y = y - 54 * mm
    shadow_card(c, M_L, drv_y, SAFE_W, 46 * mm)

    items = (ctx.get("drivers", {}).get("cash") or []) + (ctx.get("drivers", {}).get("margins") or []) + (ctx.get("drivers", {}).get("acquisition") or [])
    items = items[:3] if items else ["Driver non disponibili con i dati attuali."]

    bullet_block(c, M_L + 8 * mm, drv_y + 35 * mm, SAFE_W - 16 * mm, "Top driver strategici", items)

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 8.9)
    c.drawString(
        M_L + 8 * mm,
        drv_y + 6 * mm,
        "Rischio %: trasformazione del punteggio di criticità (0–100). 0% = nessun rischio, 100% = massima criticità.",
    )

    footer(c, page_no, total)


def _page_3_kpi(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(
        c,
        "KPI Dashboard",
        f"{ctx['settore']} · {ctx['mese']}",
        ctx["overall"],
    )
    _section_divider(c, H - M_T - 13 * mm)

    kpi = ctx.get("kpi") or {}
    indicators = ctx.get("indicators") or []

    top_y = H - M_T - 18 * mm
    gap = 7 * mm
    col_w = (SAFE_W - 2 * gap) / 3
    row_h = 34 * mm

    values = {
        "Runway": fmt_num(kpi.get("runway_mesi"), 1, " mesi"),
        "Break-even ratio": fmt_num(kpi.get("break_even_ratio"), 2),
        "Conversione": fmt_pct(kpi.get("conversione"), 1),
        "Margine lordo": fmt_pct(kpi.get("margine_pct"), 1),
        "Burn/Cash": fmt_pct(kpi.get("burn_cash_ratio"), 1),
        "Incassi mese": fmt_money(kpi.get("incassi_mese")),
    }

    cards = [
        ("Runway", values["Runway"], "Autonomia finanziaria di breve", indicators[0]["label"] if len(indicators) > 0 else "GIALLO"),
        ("Break-even ratio", values["Break-even ratio"], "Copertura dei costi fissi", indicators[4]["label"] if len(indicators) > 4 else "GIALLO"),
        ("Conversione", values["Conversione"], "Lead trasformati in clienti", indicators[2]["label"] if len(indicators) > 2 else "GIALLO"),
        ("Margine lordo", values["Margine lordo"], "Qualità economica dell’offerta", indicators[3]["label"] if len(indicators) > 3 else "GIALLO"),
        ("Burn/Cash", values["Burn/Cash"], "Pressione del burn sulla cassa", indicators[5]["label"] if len(indicators) > 5 else "GIALLO"),
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
    header(
        c,
        "Strategic Priorities",
        f"{ctx['settore']} · {ctx['mese']}",
        ctx["overall"],
    )
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    left_w = 92 * mm
    gap = 8 * mm
    right_w = SAFE_W - left_w - gap

    left_y = top_y - 74 * mm
    shadow_card(c, M_L, left_y, left_w, 74 * mm)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 8 * mm, left_y + 65 * mm, "Direzione strategica prioritaria")

    decisions = ctx.get("decisions") or {}
    rows = [
        ("Cassa", decisions.get("cash") or "—"),
        ("Margini", decisions.get("margini") or "—"),
        ("Acquisizione", decisions.get("acq") or "—"),
    ]

    yy = left_y + 54 * mm
    for title, text in rows:
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(M_L + 8 * mm, yy, title)
        c.setFont("Helvetica", 9.3)
        _draw_multiline(c, M_L + 8 * mm, yy - 5 * mm, text, left_w - 16 * mm, "Helvetica", 9.3, 3)
        yy -= 21 * mm

    right_x = M_L + left_w + gap
    shadow_card(c, right_x, left_y, right_w, 74 * mm)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(right_x + 8 * mm, left_y + 65 * mm, "Benchmark e lettura comparativa")

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.4)
    _draw_multiline(
        c,
        right_x + 8 * mm,
        left_y + 54 * mm,
        (ctx.get("benchmark_meta") or {}).get("note") or "Benchmark non disponibile: baseline provvisoria interna.",
        right_w - 16 * mm,
        "Helvetica",
        9.4,
        4,
    )

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(right_x + 8 * mm, left_y + 29 * mm, "Indicazione sintetica")

    c.setFont("Helvetica", 9.4)
    _draw_multiline(
        c,
        right_x + 8 * mm,
        left_y + 23 * mm,
        ctx.get("summary") or "",
        right_w - 16 * mm,
        "Helvetica",
        9.4,
        5,
    )

    footer(c, page_no, total)


def _page_5_execution(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(
        c,
        "Execution Roadmap — Next 90 Days",
        f"{ctx['settore']} · {ctx['mese']}",
        ctx["overall"],
    )
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
        week = item.get("week", "—")
        action = item.get("action", "—")
        owner = item.get("owner", "—")
        target_kpi = item.get("target_kpi", "—")
        target_value = item.get("target_value", "—")

        # titolo settimana su riga dedicata
        c.setFillColor(DEFAULT_TEXT)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(M_L + 8 * mm, row_y, f"Settimana {week}")

        # azione su riga separata e più larga
        c.setFont("Helvetica", 9.4)
        _draw_multiline(
            c,
            M_L + 8 * mm,
            row_y - 7 * mm,
            action,
            SAFE_W - 16 * mm,
            "Helvetica",
            9.4,
            2,
        )

        # metadati distanziati su una riga successiva
        meta_y = row_y - 17 * mm
        c.setFont("Helvetica", 8.9)
        c.drawString(M_L + 8 * mm, meta_y, f"Owner: {owner}")
        c.drawString(M_L + 60 * mm, meta_y, f"KPI: {target_kpi}")
        c.drawRightString(M_L + SAFE_W - 8 * mm, meta_y, f"Target: {target_value}")

        # linea divisoria leggera
        c.setStrokeColorRGB(0.86, 0.89, 0.94)
        c.setLineWidth(0.6)
        c.line(M_L + 8 * mm, meta_y - 5 * mm, M_L + SAFE_W - 8 * mm, meta_y - 5 * mm)

        # spazio verticale calibrato per far rientrare 4 settimane nella card
        row_y -= 26 * mm

    footer(c, page_no, total)


def _one_pager_executive(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int) -> None:
    page_bg(c)
    header(
        c,
        "Executive One Pager",
        f"{ctx['settore']} · {ctx['mese']}",
        ctx["overall"],
    )
    _section_divider(c, H - M_T - 13 * mm)

    top_y = H - M_T - 18 * mm
    gap = 8 * mm
    col_w = (SAFE_W - 2 * gap) / 3

    y = top_y - 32 * mm
    kpi_card(c, M_L, y, col_w, 30 * mm, "Triad Score", f"{int(round(ctx['triad']))}/100", "Business Stability Score", ctx["overall"])
    kpi_card(c, M_L + col_w + gap, y, col_w, 30 * mm, "Risk Profile", ctx.get("risk_profile") or "—", "Profilo dominante", "VERDE")
    kpi_card(c, M_L + 2 * (col_w + gap), y, col_w, 30 * mm, "Confidence", f"{ctx.get('confidence', '—')}%", "Affidabilità del report", "VERDE")

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
        _draw_multiline(c, right_x + 8 * mm, yy, f"• {item.get('action', '—')}", left_w - 16 * mm, "Helvetica", 9.2, 2)
        yy -= 11 * mm

    footer(c, page_no, total)


def render_scan_pages(c: canvas.Canvas, ctx: Dict[str, Any]) -> None:
    total = 5
    _page_1_executive(c, ctx, 1, total)
    c.showPage()
    _page_2_risk_snapshot(c, ctx, 2, total)
    c.showPage()
    _page_3_kpi(c, ctx, 3, total)
    c.showPage()
    _page_4_radar(c, ctx, 4, total)
    c.showPage()
    _page_5_execution(c, ctx, 5, total)


def render_one_pager(c: canvas.Canvas, ctx: Dict[str, Any]) -> None:
    _one_pager_executive(c, ctx, 1, 1)