from __future__ import annotations

from typing import Any, Dict, Optional

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .config import *

# alias per usare i nomi con _
from .primitives import (
    page_bg as _page_bg,
    watermark as _watermark,
    header as _header,
    footer as _footer,
    shadow_card as _shadow_card,
    triad_progress as _triad_progress,
    risk_card as _risk_card,
    kpi_card as _kpi_card,
    draw_radar as _draw_radar,
)

from .utils import badge_color, fmt_num, fmt_pct01, wrap as _wrap

SCHEMA_VERSION = '1.2'
# =========================================================
# KPI value formatting helpers
# =========================================================


# =========================================================
# Small helpers (layout)
# =========================================================
def _draw_chip(c: canvas.Canvas, x: float, y: float, label: str, fg: colors.Color) -> tuple[float, float]:
    """Small rounded label chip. VERDE/OK/STABILE must remain green."""
    pad_x = 3.2 * mm
    pad_y = 2.0 * mm
    r = 3.0 * mm

    lab = (label or "").strip().upper()
    bg = colors.HexColor("#64748b")  # default gray

    if lab in ("VERDE", "GREEN", "OK", "GOOD", "STABILE"):
        bg = colors.HexColor("#28a55f")
    elif lab in ("CRITICO", "ROSSO", "RED"):
        bg = colors.HexColor("#d64545")
    elif lab in ("ATTENZIONE", "GIALLO", "YELLOW"):
        bg = colors.HexColor("#f1c644")
    elif lab in ("STIMA", "ESTIMATED"):
        bg = colors.HexColor("#7c3aed")

    c.saveState()
    c.setFont("Helvetica-Bold", 8.5)
    w = c.stringWidth(label, "Helvetica-Bold", 8.5) + 2 * pad_x
    h = 8 * mm
    c.setFillColor(bg)
    c.roundRect(x, y, w, h, r, fill=1, stroke=0)
    c.setFillColor(fg)
    c.drawString(x + pad_x, y + pad_y, label)
    c.restoreState()
    return w, h


def _draw_defs_box(c, x, y, w, h, defs_list):
    """Compact glossary box.

    v1.2 rule: always show the 6 core KPI definitions (if available), otherwise
    fallback to a safe synthetic line, and then add extras only if there is space.
    """
    _shadow_card(c, x, y, w, h)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(x + 8 * mm, y + h - 10 * mm, "Definizioni & formule")

    c.setFont("Helvetica", 9.5)
    c.setFillColor(DEFAULT_MUTED)

    yy = y + h - 18 * mm

    # Build a name->line map (dedupe)
    defs = []
    for d in (defs_list or []):
        try:
            name = str(d.get("name", "")).strip()
            formula = str(d.get("formula", "")).strip()
            unit = str(d.get("unit", "")).strip()
        except Exception:
            continue
        if not name or not formula:
            continue
        line = f"• {name}: {formula}" + (f" [{unit}]" if unit else "")
        defs.append((name.lower(), line))

    line_by_key: Dict[str, str] = {}
    for k, line in defs:
        if k not in line_by_key:
            line_by_key[k] = line

    # Core definitions (must appear in this order)
    core_keys = [
        "runway",
        "net cash flow",
        "break-even coverage",
        "break-even ricavi",
        "conversione",
        "margine lordo",
    ]

    # Helper: find a line whose key contains a token
    def _find_line(token: str) -> Optional[str]:
        token = (token or "").lower()
        for k, line in line_by_key.items():
            if token in k:
                return line
        return None

    lines: list[str] = []

    # 1) Add core lines (with safe synthetic fallbacks when missing)
    for token in core_keys:
        found = _find_line(token)
        if found and found not in lines:
            lines.append(found)
            continue

        # Synthetic fallbacks (only for the two that have been requested explicitly)
        if token == "conversione":
            lines.append("• Conversione: Clienti / Lead (lead = contatti qualificati) [%]")
        elif token == "margine lordo":
            lines.append("• Margine lordo %: (Ricavi − Variabili) / Ricavi [%]")
        else:
            # If a core item is missing from payload, be honest but still informative
            pretty = token.title()
            lines.append(f"• {pretty}: metrica non disponibile nel payload (v1)")

    # 2) Add extra definitions only if there is space (deduped)
    for k, line in defs:
        if line in lines:
            continue
        lines.append(line)
        if len(lines) >= 8:
            break

    # Render tight (v1.2): 1 line per bullet to guarantee core items fit
    c.setFont("Helvetica", 9.0)
    line_h = 4.6 * mm
    max_w = w - 16 * mm

    for ln in lines[:8]:
        wlns = _wrap(c, ln, max_w, size=9.0)
        if not wlns:
            continue

        # Force single-line rendering: truncate with ellipsis if needed
        text = wlns[0]
        if len(wlns) > 1:
            # naive ellipsis: progressively trim until it fits
            ell = "…"
            base = wlns[0]
            while base and (c.stringWidth(base + ell, "Helvetica", 9.0) > max_w):
                base = base[:-1]
            text = (base + ell) if base else (wlns[0][: max(0, int(len(wlns[0]) * 0.85))] + ell)

        c.drawString(x + 8 * mm, yy, text)
        yy -= line_h

        if yy < y + 9 * mm:
            break

def _draw_quality_box(c: canvas.Canvas, x: float, y: float, w: float, h: float, dq: Dict[str, Any]) -> None:
    dq = dq or {}
    badge = (dq.get("badge") or "—")
    comp = dq.get("completeness_score")
    if comp is None:
        comp = dq.get("completeness")

    notes = list(dq.get("notes") or [])
    flags = list(dq.get("coherence_flags") or [])

    # v1.1 safety: detect estimated values if backend didn't set the flag
    has_estimates = dq.get("has_estimates")
    if has_estimates is None:
        txt = " ".join([str(x).lower() for x in (notes + flags)])
        if "stima" in txt or "estimate" in txt or "stimato" in txt:
            has_estimates = True
        else:
            has_estimates = False
    dq["has_estimates"] = has_estimates

    # Card
    c.saveState()
    c.setFillColor(colors.white)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.restoreState()

    # Header row: title left, chip right (fills the box better)
    title_x = x + 8 * mm
    title_y = y + h - 10 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(DEFAULT_TEXT)
    c.drawString(title_x, title_y, "Qualità dati")

    # Compute chip size (do NOT draw twice)
    chip_label = str(badge).strip().upper() if badge is not None else "—"
    chip_pad_x = 3.2 * mm
    chip_r = 3.0 * mm
    chip_font = 8.5
    chip_w = c.stringWidth(chip_label, "Helvetica-Bold", chip_font) + 2 * chip_pad_x
    chip_h = 8 * mm

    # Place chip aligned to the right, on the same header row
    chip_x = x + w - 8 * mm - chip_w
    chip_y = y + h - 18 * mm
    c.saveState()
    c.setFont("Helvetica-Bold", chip_font)
    c.setFillColor(badge_color(chip_label))
    c.roundRect(chip_x, chip_y, chip_w, chip_h, chip_r, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawString(chip_x + chip_pad_x, chip_y + 2.0 * mm, chip_label)
    c.restoreState()

    c.setFont("Helvetica", 9.5)
    c.setFillColor(DEFAULT_MUTED)

    # Content starts closer to header (less empty space)
    yy = y + h - 26 * mm

    # Completeness line
    if comp is not None:
        try:
            c.drawString(title_x, yy, f"Completezza: {int(comp)}%")
        except Exception:
            c.drawString(title_x, yy, "Completezza: —")
        yy -= 5.2 * mm

    # Recency line (v1.2)
    rec = dq.get("recency_flag")
    if rec is None:
        rec = dq.get("recency")
    if rec:
        c.drawString(title_x, yy, f"Recenza: {str(rec)}")
        yy -= 5.2 * mm

    # Estimate note + visual chip
    try:
        if dq.get("has_estimates") is True:
            chip_w, chip_h = _draw_chip(
                c,
                title_x,
                yy - 1.5 * mm,
                "STIMA",
                colors.white,
            )
            c.setFillColor(DEFAULT_MUTED)
            c.setFont("Helvetica", 9.5)
            c.drawString(title_x + chip_w + 4, yy, "Valori stimati presenti nel report.")
            yy -= 6.0 * mm
    except Exception:
        pass

    # Default copy when nothing else to say
    if not notes and not flags:
        # Copy default più "pieno" per evitare vuoti visivi
        if comp is not None:
            try:
                if int(comp) >= 95:
                    notes = ["Dati completi. Nessuna anomalia rilevata.", "Confidenza alta (v1)."]
                else:
                    notes = ["Dati parziali. Aggiungi campi opzionali per aumentare confidenza."]
            except Exception:
                notes = ["Dati minimi OK (MVP). Completa i campi opzionali per aumentare confidenza."]
        else:
            notes = ["Dati minimi OK (MVP). Completa i campi opzionali per aumentare confidenza."]

    for t in (notes + flags)[:3]:
        for wln in _wrap(c, f"• {t}", w - 16 * mm, size=9.5)[:2]:
            c.drawString(title_x, yy, wln)
            yy -= 5.2 * mm
        if yy < y + 10 * mm:
            break


def _draw_drivers_box(c: canvas.Canvas, x: float, y: float, w: float, title: str, items):
    """
    Driver box (MVP)
    - chiamata standard: _draw_drivers_box(c, x, y, w, title, items)
    - items: list[str] oppure dict con chiavi cash/margins/acquisition (fallback)
    """
    h = 56 * mm
    pad = 10 * mm

    # Normalizza items
    if isinstance(items, dict):
        lst = (items.get("cash") or []) + (items.get("margins") or []) + (items.get("acquisition") or [])
        items = lst[:3] if lst else ["Driver non disponibili (MVP)."]
    if not isinstance(items, (list, tuple)):
        items = [str(items)]
    items = [str(t) for t in items if t is not None]
    if not items:
        items = ["Driver non disponibili (MVP)."]

    _shadow_card(c, x, y, w, h)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(x + pad, y + h - 12*mm, title)

    c.setFont("Helvetica", 9.5)
    c.setFillColor(DEFAULT_MUTED)

    yy = y + h - 22*mm
    max_lines = 6  # evita overflow
    used = 0
    for t in items[:3]:
        # max 2 righe per bullet
        for wln in _wrap(c, f"• {t}", w - 2*pad, size=9.5)[:2]:
            c.drawString(x + pad, yy, wln)
            yy -= 5.2*mm
            used += 1
            if used >= max_lines or yy < y + 10*mm:
                break
        if used >= max_lines or yy < y + 10*mm:
            break


def _draw_benchmark_meta(c, x, y, w, bm):
    bm = bm or {}
    enabled = bool(bm.get("enabled", False))
    c.setFont("Helvetica", 9.5)
    c.setFillColor(DEFAULT_MUTED)

    if not enabled:
        c.drawString(x, y, "Benchmark: baseline provvisoria (in calibrazione v1).")
        return

    src = str(bm.get("source","—"))
    n = bm.get("sample_n")
    sec = str(bm.get("sector_definition","—"))
    note = str(bm.get("note","")).strip()

    c.drawString(x, y, f"Fonte: {src}")
    c.drawString(x, y - 5.2*mm, (f"Campione: n={n}" if n is not None else "Campione: —"))
    c.drawString(x, y - 10.4*mm, f"Settore: {sec}")
    if note:
        c.drawString(x, y - 15.6*mm, note[:110])


def _kpi_text_runway(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.1f} mesi"
    except Exception:
        return "—"


def _kpi_text_ratio(v: Any) -> str:
    # e.g. break-even coverage ratio
    if v is None:
        return "—"
    return fmt_num(v, 2)


def _kpi_text_pct(v: Any) -> str:
    # accepts either 0..1 or 0..100 style inputs
    if v is None:
        return "—"
    return fmt_pct01(v)


def _draw_image_contain(c: canvas.Canvas, img_path: Optional[str], x: float, y: float, w: float, h: float) -> bool:
    if not img_path:
        return False
    try:
        img = ImageReader(img_path)
        iw, ih = img.getSize()
        if not iw or not ih:
            return False

        scale = min(w / float(iw), h / float(ih))
        dw = iw * scale
        dh = ih * scale
        dx = x + (w - dw) / 2.0
        dy = y + (h - dh) / 2.0
        c.drawImage(img, dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
        return True
    except Exception:
        return False

# =========================================================
# PAGE 1 — EXECUTIVE
# =========================================================
def _page_1_executive(
    c: canvas.Canvas,
    ctx: Dict[str, Any],
    page_no: int,
    total: int,
    right_label: Optional[str] = None,
) -> None:

    _page_bg(c)
    _watermark(c, ctx["watermark_text"])

    _header(
        c,
        "Executive Strategic Scan",
        f"{ctx['settore']} · {ctx['mese']}",
        ctx["overall"],
        primary=ctx["primary"],
        logo_path=ctx["logo_path"],
    )

    top_y = H - HEADER_H - 18 * mm

    left_w = SAFE_W * 0.42
    right_w = SAFE_W - left_w - 8 * mm

    # Left card: give more vertical room (ERS + Triad + note) — v1.1 layout
    card_h = 88 * mm
    card_y = top_y - card_h

    _shadow_card(c, M_L, card_y, left_w, card_h)

    y_top = card_y + card_h

    # IMPORTANT: reset colors after header/watermark (header sets white text)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(M_L + 10 * mm, y_top - 16 * mm, f"Triad Index™  {ctx['triad']}/100")

    # Confidence line (kept close to title)
    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 10)
    c.drawString(
        M_L + 10 * mm,
        y_top - 24.5 * mm,
        f"Confidence score (v1): {ctx.get('confidence','—')}% · calibrazione"
    )

    # Executive Resilience Score (v1)
    # (sintesi difendibile: combina Triad + Confidence + rischio cassa + marginalità + conversione)
    ers = ctx.get("ers")
    if ers is not None:
        try:
            ers_txt = f"{float(ers):.1f}" if isinstance(ers, (int, float)) else str(ers)
        except Exception:
            ers_txt = str(ers)

        c.setFillColor(DEFAULT_TEXT)
        c.setFont("Helvetica-Bold", 10.5)
        # ERS title: keep it high to leave vertical room for bars below
        c.drawString(
            M_L + 10 * mm,
            y_top - 32.0 * mm,
            f"ERS (v1): {ers_txt}/100",
        )
        # Executive Resilience visual bar (fragile → scalabile)
    ers_val = ctx.get("ers")
    if isinstance(ers_val, (int, float)):
        bar_x = M_L + 10 * mm
        bar_y = y_top - 48 * mm
        bar_w = left_w - 20 * mm
        bar_h = 3.2 * mm

        # scale labels (ABOVE the ERS bar to avoid collisions with Triad progress)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(DEFAULT_MUTED)
        lbl_y = bar_y + bar_h + 2.6 * mm
        c.drawString(bar_x, lbl_y, "FRAGILE")
        c.drawCentredString(bar_x + bar_w / 2, lbl_y, "STABILE")
        c.drawRightString(bar_x + bar_w, lbl_y, "SCALABILE")

        # background
        c.setFillColor(colors.HexColor("#e5e7eb"))
        c.roundRect(bar_x, bar_y, bar_w, bar_h, 1.5 * mm, fill=1, stroke=0)

        # marker position
        pos = max(0.0, min(1.0, float(ers_val) / 100.0))
        marker_x = bar_x + pos * bar_w

        # marker
        c.setFillColor(colors.HexColor("#111827"))
        c.circle(marker_x, bar_y + bar_h / 2, 1.8 * mm, fill=1, stroke=0)
        
    # Triad progress bar — positioned clearly above the explanatory note
    c.setFillColor(DEFAULT_TEXT)
    _triad_progress(
        c,
        M_L + 10 * mm,
        card_y + 20 * mm,
        left_w - 20 * mm,
        ctx["triad"],
        accent=ctx["accent"],
    )

    # Small definition note (2 lines, no overflow)
    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 8.0)
    note_x = M_L + 10 * mm
    note_y = card_y + 10.0 * mm
    note_lines = [
        "Triad Index v1 — media pesata di Cassa, Margini, Acquisizione.",
        "(pesi equal-weight 1/3 ciascuno · metrica in calibrazione).",
    ]
    for i, ln in enumerate(note_lines):
        c.drawString(note_x, note_y - i * 3.6 * mm, ln)

    c.setFillColor(DEFAULT_TEXT)

    # insight
    _shadow_card(c, M_L + left_w + 10 * mm, card_y, right_w, card_h)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(M_L + left_w + 20 * mm, top_y - 12 * mm, "Executive insight")

    # Render insight text to fill the card area cleanly (auto-fit)
    insight_x = M_L + left_w + 20 * mm
    insight_w = right_w - 20 * mm

    # Tune typography for a denser, board-ready layout
    font_name = "Helvetica"
    font_size = 10.6
    line_h = 5.2 * mm

    c.setFillColor(DEFAULT_TEXT)
    c.setFont(font_name, font_size)

    raw = (ctx.get("hero", "") or "").strip()
    lines = _wrap(c, raw, insight_w, size=font_size)

    # Available vertical space inside the insight card
    # Title is at (top_y - 12mm). Start text a bit below; stop above the card bottom padding.
    yy = top_y - 26 * mm
    y_min = card_y + 12 * mm

    for ln in lines:
        if yy < y_min:
            break
        c.drawString(insight_x, yy, ln)
        yy -= line_h

    # If still too short, add a subtle filler line (keeps the box visually balanced)
    if yy > y_min + 14 * mm and raw:
        c.setFillColor(DEFAULT_MUTED)
        c.setFont(font_name, 9.2)
        c.drawString(insight_x, y_min + 6 * mm, "Nota: insight generato da KPI + quiz (v1).")
        c.setFillColor(DEFAULT_TEXT)
        c.setFont(font_name, font_size)

    _footer(c, page_no, total, right_label=right_label)


# =========================================================
# PAGE 2 — RISK SNAPSHOT
# =========================================================
def _page_2_risk_snapshot(
    c: canvas.Canvas,
    ctx: Dict[str, Any],
    page_no: int,
    total: int,
    right_label: Optional[str] = None,
) -> None:

    _page_bg(c)
    _watermark(c, ctx["watermark_text"])

    _header(
        c,
        "Risk Snapshot",
        f"{ctx['settore']} · {ctx['mese']}",
        ctx["overall"],
        primary=ctx["primary"],
        logo_path=ctx["logo_path"],
    )

    top_y = H - HEADER_H - 18 * mm

    # v1.1 – spiegazione sintetica della metrica di rischio (per difendibilità del report)
    c.saveState()
    c.setFont("Helvetica", 9.2)
    c.setFillColor(DEFAULT_MUTED)
    risk_legend = "Rischio %: trasformazione del punteggio di criticità (0–100). 0% = nessun rischio · 100% = massima criticità (metrica v1 in calibrazione)."
    for i, ln in enumerate(_wrap(c, risk_legend, SAFE_W - 20 * mm, size=9.2)[:2]):
        c.drawString(M_L + 10 * mm, top_y - 6 * mm - i * 4.8 * mm, ln)
    c.restoreState()

    # Spostiamo leggermente verso il basso il blocco delle card per evitare sovrapposizioni
    top_y = top_y - 10 * mm

    # Premium chart card (if available)
    chart_h = 42 * mm
    chart_y = top_y - chart_h
    if ctx.get("risk_bar_chart"):
        _shadow_card(c, M_L, chart_y, SAFE_W, chart_h)
        c.setFillColor(DEFAULT_TEXT)
        c.setFont("Helvetica-Bold", 11.5)
        c.drawString(M_L + 8 * mm, chart_y + chart_h - 10 * mm, "Business Risk Profile")
        drawn = _draw_image_contain(c, ctx.get("risk_bar_chart"), M_L + 8 * mm, chart_y + 5 * mm, SAFE_W - 16 * mm, chart_h - 16 * mm)
        if not drawn:
            c.setFillColor(DEFAULT_MUTED)
            c.setFont("Helvetica", 9.5)
            c.drawString(M_L + 8 * mm, chart_y + 16 * mm, "Grafico rischio non disponibile.")
        top_y = chart_y - 8 * mm

    gap = 10 * mm
    col_w = (SAFE_W - 2 * gap) / 3

    card_h = 62 * mm
    y = top_y - card_h

    _risk_card(
        c,
        M_L,
        y,
        col_w,
        card_h,
        "Rischio Cassa",
        ctx["cash_r"],
        "",
    )

    _risk_card(
        c,
        M_L + col_w + gap,
        y,
        col_w,
        card_h,
        "Rischio Margini",
        ctx["marg_r"],
        "",
    )

    _risk_card(
        c,
        M_L + 2 * (col_w + gap),
        y,
        col_w,
        card_h,
        "Rischio Acquisizione",
        ctx["acq_r"],
        "",
    )

    # --- Top driver (perché) ---
    drivers_h = 25 * mm
    drivers_y = y - drivers_h - 14 * mm
    drv = ctx.get("drivers") or {}    
    items = (drv.get("cash") or []) + (drv.get("margins") or []) + (drv.get("acquisition") or [])
    items = items[:3] if items else ["Driver non disponibili (MVP)."]
    _draw_drivers_box(c, M_L, drivers_y, SAFE_W, "Top driver – Sintesi", items)

    # Nota metrica rischio (v1.1): esplicita cosa significa la %
    c.saveState()
    c.setFont("Helvetica", 9.2)
    c.setFillColor(DEFAULT_MUTED)
    note = "Rischio %: trasformazione del punteggio di criticità (0–100). 0% = nessun rischio, 100% = massima criticità (v1, in calibrazione)."
    for i, ln in enumerate(_wrap(c, note, SAFE_W - 20 * mm, size=9.2)[:2]):
        c.drawString(M_L + 10 * mm, drivers_y - (6.5 * mm) - i * 4.8 * mm, ln)
    c.restoreState()

    _footer(c, page_no, total, right_label=right_label)

# =========================================================
# PAGE 3 — KPI
# =========================================================

def _page_3_kpi(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int, right_label: Optional[str] = None) -> None:
    _page_bg(c)
    _watermark(c, ctx["watermark_text"])
    _header(c, "KPI", f"{ctx['settore']} · {ctx['mese']}", ctx["overall"], primary=ctx["primary"], logo_path=ctx["logo_path"])

    # v1.2 – show STIMA indicator if report contains estimated values
    try:
        dq = ctx.get("dq") or {}
        if dq.get("has_estimates"):
            chip_x = M_L + SAFE_W - 28 * mm
            chip_y = H - HEADER_H - 12 * mm
            _draw_chip(c, chip_x, chip_y, "STIMA", colors.white)
    except Exception:
        pass

    top_y = H - HEADER_H - 18 * mm

    kw = (SAFE_W - 10 * mm) / 2
    # Slightly shorter KPI cards for a denser, board-ready page
    kh = 34 * mm
    y = top_y - kh

    # Subtitles make the cards feel “filled” and clarify targets (v1.2)
    _kpi_card(
        c, M_L, y, kw, kh,
        "Runway (mesi)",
        _kpi_text_runway(ctx.get("runway")),
        "Soglia: ≥ 6 mesi"
    )
    _kpi_card(
        c, M_L + kw + 10 * mm, y, kw, kh,
        "Break-even (coverage)",
        _kpi_text_ratio(ctx.get("be")),
        "Target: ≥ 1.10 (buffer)"
    )

    y2 = y - kh - 8 * mm
    _kpi_card(
        c, M_L, y2, kw, kh,
        "Conversione",
        _kpi_text_pct(ctx.get("conv")),
        "Target: ≥ 10%"
    )
    _kpi_card(
        c, M_L + kw + 10 * mm, y2, kw, kh,
        "Margine lordo",
        _kpi_text_pct(ctx.get("marg")),
        "Target: ≥ 50%"
    )

    # Bring the lower boxes up a bit and give them more room
    box_top = y2 - 8 * mm
    box_h = 64 * mm
    box_y = box_top - box_h
    left_w = (SAFE_W - 10 * mm) / 2

    _draw_defs_box(c, M_L, box_y, left_w, box_h, ctx.get("defs"))
    _draw_quality_box(c, M_L + left_w + 10 * mm, box_y, left_w, box_h, ctx.get("dq"))


    _footer(c, page_no, total, right_label=right_label)


def _page_4_radar(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int, right_label: Optional[str] = None) -> None:
    _page_bg(c)
    _watermark(c, ctx["watermark_text"])
    _header(c, "Radar & Benchmark", f"{ctx['settore']} (Azienda vs Benchmark)", ctx["overall"], primary=ctx["primary"], logo_path=ctx["logo_path"])

    top_y = H - HEADER_H - 18 * mm

    card_h = 165 * mm
    card_y = top_y - card_h
    _shadow_card(c, M_L, card_y, SAFE_W, card_h)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(M_L + 10 * mm, top_y - 12 * mm, "Radar (resilienza: 1 - rischio)")

    # Radar area: keep higher to leave room for meta + drivers below
    cx = M_L + SAFE_W / 2.0
    cy = card_y + card_h * 0.70
    radar_r = min(SAFE_W, card_h) * 0.30

    bm = ctx.get("benchmark_meta") or ctx.get("bm") or {}
    bm_enabled = bool(bm.get("enabled", False))

    radar_drawn = False
    if ctx.get("triade_radar_chart"):
        radar_drawn = _draw_image_contain(
            c,
            ctx.get("triade_radar_chart"),
            cx - radar_r,
            cy - radar_r,
            radar_r * 2,
            radar_r * 2,
        )

    if not radar_drawn and bm_enabled:
        _draw_radar(
            c,
            cx,
            cy,
            radar_r,
            ["Cassa", "Margini", "Acquisizione"],
            [ctx["cash_r"], ctx["marg_r"], ctx["acq_r"]],
            ctx.get("benchmark"),
            accent=ctx["accent"],
        )
    elif not radar_drawn:
        # Benchmark OFF: show an explicit placeholder (no decorative radar)
        c.saveState()
        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(cx, cy + 6 * mm, "Benchmark disattivato")
        c.setFont("Helvetica", 10.5)
        c.drawCentredString(cx, cy - 2 * mm, "Baseline provvisoria in calibrazione (v1)")
        c.restoreState()

    # Drivers row: anchored low inside the card so the radar area stays clean
    drv = ctx.get("drivers") or {}
    col_w = (SAFE_W - 10 * mm) / 3.0
    drivers_h = 56 * mm
    y0 = card_y + 18 * mm

    _draw_drivers_box(c, M_L, y0, col_w, "Top driver – Cassa", drv.get("cash") or [])
    _draw_drivers_box(c, M_L + col_w + 5 * mm, y0, col_w, "Top driver – Margini", drv.get("margins") or [])
    _draw_drivers_box(c, M_L + 2 * (col_w + 5 * mm), y0, col_w, "Top driver – Acquisizione", drv.get("acquisition") or [])

    # Benchmark meta: placed above drivers (so it doesn't look "under" the page)
    meta_y = y0 + drivers_h + 10 * mm
    _draw_benchmark_meta(c, M_L + 10 * mm, meta_y, SAFE_W - 20 * mm, bm)

    _footer(c, page_no, total, right_label=right_label)


def _page_5_execution(c: canvas.Canvas, ctx: Dict[str, Any], page_no: int, total: int, right_label: Optional[str] = None) -> None:
    _page_bg(c)
    _watermark(c, ctx["watermark_text"])
    _header(c, "Alerts & 90 Day Plan", f"{ctx['settore']} · {ctx['mese']}", ctx["overall"], primary=ctx["primary"], logo_path=ctx["logo_path"])

    top_y = H - HEADER_H - 18 * mm
    plan = (ctx.get("plan") or [])[:4]

    # Make the plan card slightly shorter and keep a clean bottom margin above the footer
    card_h = 138 * mm
    card_y = top_y - card_h - 4 * mm
    _shadow_card(c, M_L, card_y, SAFE_W, card_h)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 10*mm, card_y + card_h - 12*mm, "Piano 90 giorni (task-based, MVP 4 settimane)")
    x0 = M_L + 10*mm
    y = card_y + card_h - 26*mm
    col_week = 14 * mm
    col_owner = 28 * mm
    col_kpi = 40 * mm
    col_gap = 2.5 * mm
    col_why = 50 * mm
    col_action = SAFE_W - 20 * mm - col_week - col_owner - col_kpi - col_why - 3 * col_gap

    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(DEFAULT_MUTED)
    c.drawString(x0, y, "Week")
    c.drawString(x0 + col_week + col_gap, y, "Owner")
    c.drawString(x0 + col_week + col_owner + 2 * col_gap, y, "KPI target")
    c.drawString(x0 + col_week + col_owner + col_kpi + 3 * col_gap, y, "Azione")
    c.drawString(x0 + col_week + col_owner + col_kpi + col_action + 4 * col_gap, y, "Why")

    c.setStrokeColor(colors.HexColor("#e5e7eb"))
    c.setLineWidth(1)
    c.line(x0, y - 2.5*mm, x0 + SAFE_W - 20*mm, y - 2.5*mm)

    y -= 10*mm

    c.setFont("Helvetica", 10.0)
    c.setFillColor(DEFAULT_TEXT)

    for t in plan:
        week = str(t.get("week", "—")).strip()
        owner = str(t.get("owner", "—")).strip()
        kpi_t = str(t.get("target_kpi", "—")).strip()

        kpi_v_raw = t.get("target_value")

        # Clean/format target value
        kpi_v = ""
        if kpi_v_raw not in (None, "—", ""):
            if isinstance(kpi_v_raw, (int, float)):
                l = (kpi_t or "").lower()
                if "runway" in l:
                    kpi_v = f"≥ {float(kpi_v_raw):.1f} mesi"
                elif "conversion" in l or "marg" in l:
                    v = float(kpi_v_raw)
                    if 0 <= v <= 1:
                        v *= 100.0
                    kpi_v = f"≥ {v:.2f}%"
                else:
                    kpi_v = f"≥ {float(kpi_v_raw):.2f}"
            else:
                s_val = str(kpi_v_raw).strip()

                low = s_val.lower()
                if "(oggi" in low:
                    s_val = s_val[:low.find("(oggi")].rstrip()

                s_val = s_val.replace("Oggi", "").replace("oggi", "").strip()
                kpi_v = s_val

        def _today_value(label: str) -> str:
            l = (label or "").lower()
            if "runway" in l:
                return _kpi_text_runway(ctx.get("runway"))
            if "conversion" in l:
                return _kpi_text_pct(ctx.get("conv"))
            if "break" in l or "be" in l or "coverage" in l:
                return _kpi_text_ratio(ctx.get("be"))
            if "marg" in l:
                return _kpi_text_pct(ctx.get("marg"))
            if "confidence" in l:
                try:
                    return f"{int(ctx.get('confidence') or 0)}%"
                except Exception:
                    return "—"
            return "—"

        today = _today_value(kpi_t)

        kpi_main = (f"{kpi_t} {kpi_v}".strip() if kpi_v else (kpi_t or "—")).replace("  "," ")
        kpi_main = kpi_main.replace(">=", "≥").replace("<=", "≤")
        kpi = kpi_main
        show_today = today not in (None, "", "—")

        action = str(t.get("action", "—")).strip()
        why = str(t.get("why", "")).strip()

        row_y = y

        c.drawString(x0, row_y, week)
        ox = x0 + col_week + col_gap
        owner_line = _wrap(c, owner, col_owner - 1.0 * mm, size=10.0)
        c.drawString(ox, row_y, owner_line[0] if owner_line else "—")

        kx = x0 + col_week + col_owner + 2 * col_gap
        kpi_lines = _wrap(c, kpi, col_kpi, size=10.0)
        c.drawString(kx, row_y, kpi_lines[0] if kpi_lines else "—")

        line_offset = 0
        if len(kpi_lines) > 1:
            c.setFillColor(DEFAULT_MUTED)
            c.drawString(kx, row_y - 5.2 * mm, kpi_lines[1])            
            c.setFillColor(DEFAULT_TEXT)
            line_offset = 5.2 * mm

        # draw "oggi" always on a dedicated muted line
        if show_today:
            c.setFillColor(DEFAULT_MUTED)
            c.setFont("Helvetica", 9.5)
            c.drawString(kx, row_y - (5.2 * mm + line_offset), f"oggi {today}")            
            c.setFillColor(DEFAULT_TEXT)
            c.setFont("Helvetica", 10.0)  # restore main table font

        ax = x0 + col_week + col_owner + col_kpi + 3 * col_gap
        lines = _wrap(c, action, col_action, size=10.0)
        c.drawString(ax, row_y, lines[0] if lines else "—")
        if len(lines) > 1:
            c.setFillColor(DEFAULT_MUTED)
            c.drawString(ax, row_y - 5.2 * mm, lines[1])
            c.setFillColor(DEFAULT_TEXT)

        wx = x0 + col_week + col_owner + col_kpi + col_action + 4 * col_gap
        wlines = _wrap(c, why, col_why, size=10.0) if why else []
        c.setFillColor(DEFAULT_MUTED)
        c.drawString(wx, row_y, wlines[0] if wlines else "—")
        if len(wlines) > 1:
            c.drawString(wx, row_y - 5.2 * mm, wlines[1])        
        c.setFillColor(DEFAULT_TEXT)

        # keep row height stable if KPI or today line used extra space
        depth_kpi = 1 + (1 if len(kpi_lines) > 1 else 0) + (1 if show_today else 0)
        depth_action = 1 + (1 if len(lines) > 1 else 0)
        depth_why = 1 + (1 if len(wlines) > 1 else 0)
        depth = max(depth_kpi, depth_action, depth_why)

        y = row_y - 12 * mm - (depth - 1) * 5.2 * mm

    _footer(c, page_no, total, right_label=right_label)

def _one_pager_executive(
    c: canvas.Canvas,
    ctx: Dict[str, Any],
    page_no: int,
    total: int,
    right_label: Optional[str] = None,
) -> None:

    _page_bg(c)
    _watermark(c, ctx["watermark_text"])

    _header(
        c,
        "Executive One-Pager",
        f"{ctx['settore']} · {ctx['mese']} · Scan #{ctx['scan_id']}",
        ctx["overall"],
        primary=ctx["primary"],
        logo_path=ctx["logo_path"],
    )

    top_y = H - HEADER_H - 18 * mm

    # Row 1: 3 cards (risk) + triad
    gap = 8 * mm
    col_w = (SAFE_W - 3 * gap) / 4
    card_h = 50 * mm
    y = top_y - card_h

    _risk_card(c, M_L, y, col_w, card_h, "Cassa", ctx["cash_r"], "")
    _risk_card(c, M_L + col_w + gap, y, col_w, card_h, "Margini", ctx["marg_r"], "")
    _risk_card(c, M_L + 2 * (col_w + gap), y, col_w, card_h, "Acquisizione", ctx["acq_r"], "")

    # Triad mini
    tri_x = M_L + 3 * (col_w + gap)
    _shadow_card(c, tri_x, y, col_w, card_h)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(tri_x + 8 * mm, y + card_h - 14 * mm, f"Triad {ctx['triad']}/100")

    radar_ok = _draw_image_contain(
        c,
        ctx.get("triade_radar_chart"),
        tri_x + 6 * mm,
        y + 12 * mm,
        col_w - 12 * mm,
        24 * mm,
    )
    if not radar_ok:
        _triad_progress(c, tri_x + 8 * mm, y + 18 * mm, col_w - 16 * mm, ctx["triad"], accent=ctx["accent"])

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.5)
    c.drawString(tri_x + 8 * mm, y + 6 * mm, f"Confidence {ctx['confidence']}% · v1")

    # Row 2: insight + 90 day plan
    row2_top = y - 10 * mm
    left_w = SAFE_W * 0.55
    right_w = SAFE_W - left_w - 10 * mm

    box_h = 92 * mm
    box_y = row2_top - box_h

    _shadow_card(c, M_L, box_y, left_w, box_h)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 10 * mm, row2_top - 12 * mm, "Executive insight")
    c.setFont("Helvetica", 10.8)
    lines = _wrap(c, ctx["hero"], left_w - 20 * mm, size=10.8)
    yy = row2_top - 26 * mm
    for ln in lines[:7]:
        c.drawString(M_L + 10 * mm, yy, ln)
        yy -= 5.6 * mm

    _shadow_card(c, M_L + left_w + 10 * mm, box_y, right_w, box_h)
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + left_w + 20 * mm, row2_top - 12 * mm, "90 Day Plan (MVP)")
    c.setFont("Helvetica", 10.5)

    yy = row2_top - 26 * mm
    for t in (ctx.get("plan") or [])[:4]:
        s = f"Settimana {t.get('week')}: {t.get('action')} (Owner: {t.get('owner')})"
        wlines = _wrap(c, s, right_w - 20 * mm, size=10.5)
        for ln in wlines[:2]:
            c.drawString(M_L + left_w + 20 * mm, yy, ln)
            yy -= 5.4 * mm
        yy -= 2.0 * mm
        if yy < box_y + 12 * mm:
            break

    _footer(c, page_no, total, right_label=right_label)
