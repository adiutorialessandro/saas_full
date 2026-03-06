from __future__ import annotations

from datetime import datetime
from math import cos, sin, pi
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# =========================================================
# Layout (A4 Landscape ottimizzato) — SINGLE SOURCE OF TRUTH
# =========================================================
PAGE_SIZE = landscape(A4)
W, H = PAGE_SIZE

# Margini "board-pack"
M_L = 18 * mm
M_R = 18 * mm
M_T = 16 * mm
M_B = 16 * mm

SAFE_W = W - M_L - M_R
SAFE_H = H - M_T - M_B

HEADER_H = 24 * mm
FOOTER_Y = 10 * mm

# =========================================================
# Branding (white-label ready)
# =========================================================
DEFAULT_PRIMARY = colors.HexColor("#0b1220")  # header / dark
DEFAULT_ACCENT = colors.HexColor("#3b82f6")   # accent / charts
DEFAULT_BG = colors.HexColor("#f3f4f6")       # page background
DEFAULT_CARD = colors.white
DEFAULT_STROKE = colors.HexColor("#e5e7eb")
DEFAULT_TEXT = colors.HexColor("#111827")
DEFAULT_MUTED = colors.HexColor("#6b7280")

# Benchmarks “risk” 0..1 (0 = good, 1 = critical) — baseline interna v1
SECTOR_BENCHMARKS: Dict[str, List[float]] = {
    "SaaS": [0.35, 0.40, 0.45],
    "Ecommerce": [0.30, 0.35, 0.50],
    "Agency": [0.40, 0.45, 0.55],
    "Servizi": [0.40, 0.45, 0.55],
    "Default": [0.35, 0.40, 0.45],
}


# =========================================================
# Utils
# =========================================================
def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _clamp01(x: Any, default: Optional[float] = 0.0) -> Optional[float]:
    try:
        if x is None:
            return default
        if isinstance(x, str):
            s = x.strip().replace("%", "").replace(",", ".")
            v = float(s)
        else:
            v = float(x)

        while v > 1.0:
            v = v / 100.0

        return max(0.0, min(1.0, v))
    except Exception:
        return default


def _fmt_pct01(x: Any) -> str:
    v = _clamp01(x, default=None)
    if v is None:
        return "—"
    return f"{v * 100.0:.2f}%"


def _fmt_num(x: Any, decimals: int = 2) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.{decimals}f}"
    except Exception:
        return "—"


def _fmt_eur(x: Any, decimals: int = 0) -> str:
    if x is None:
        return "—"
    try:
        v = float(x)
        fmt = f"{{:,.{decimals}f}} €"
        return fmt.format(v).replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def _risk_bucket(score01: float) -> str:
    if score01 >= 0.66:
        return "CRITICO"
    if score01 >= 0.33:
        return "ATTENZIONE"
    return "STABILE"


def _badge_color(label: str):
    s = (label or "").upper()
    return {
        "CRITICO": colors.HexColor("#d64545"),
        "ATTENZIONE": colors.HexColor("#f1c644"),
        "STABILE": colors.HexColor("#28a55f"),
        "ROSSO": colors.HexColor("#d64545"),
        "GIALLO": colors.HexColor("#f1c644"),
        "VERDE": colors.HexColor("#28a55f"),
    }.get(s, colors.HexColor("#64748b"))


def _triad_index(risks: Dict[str, Any]) -> int:
    # Triad Index = media resilienza (1-risk) dei 3 pilastri (v1 calibrazione)
    vals = [
        1.0 - (_clamp01(risks.get("cash"), 0.5) or 0.5),
        1.0 - (_clamp01(risks.get("margini"), 0.5) or 0.5),
        1.0 - (_clamp01(risks.get("acq"), 0.5) or 0.5),
    ]
    return int((sum(vals) / 3.0) * 100.0)


def _dominant_risk(risks: Dict[str, Any]) -> str:
    m = {
        "CASSA": _clamp01(risks.get("cash"), 0.0) or 0.0,
        "MARGINI": _clamp01(risks.get("margini"), 0.0) or 0.0,
        "ACQUISIZIONE": _clamp01(risks.get("acq"), 0.0) or 0.0,
    }
    return max(m.items(), key=lambda kv: kv[1])[0]


def _wrap(
    c: canvas.Canvas,
    text: str,
    max_w: float,
    font: str = "Helvetica",
    size: float = 10,
) -> List[str]:
    c.setFont(font, size)
    words = (text or "").split()
    if not words:
        return []
    lines: List[str] = []
    cur: List[str] = []
    for w in words:
        trial = " ".join(cur + [w])
        if c.stringWidth(trial, font, size) <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


# =========================================================
# Helper: Ellipsize a string to fit width (single line)
# =========================================================
def _ellipsize(
    c: canvas.Canvas,
    text: str,
    max_w: float,
    font: str = "Helvetica",
    size: float = 10,
) -> str:
    """Return a single-line string that fits in max_w by adding an ellipsis if needed."""
    s = (text or "").strip()
    if not s:
        return ""

    c.setFont(font, size)
    if c.stringWidth(s, font, size) <= max_w:
        return s

    ell = "…"
    lo, hi = 0, len(s)
    best = ""
    while lo <= hi:
        mid = (lo + hi) // 2
        cand = s[:mid].rstrip() + ell
        if c.stringWidth(cand, font, size) <= max_w:
            best = cand
            lo = mid + 1
        else:
            hi = mid - 1

    return best if best else ell


def _draw_multiline(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    lines: List[str],
    line_h: float,
    max_lines: int,
):
    yy = y_top
    for i, ln in enumerate(lines[:max_lines]):
        c.drawString(x, yy, ln)
        yy -= line_h


# =========================================================
# Drawing primitives (board-ready)
# =========================================================
def _page_bg(c: canvas.Canvas, bg=DEFAULT_BG):
    c.setFillColor(bg)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def _watermark(c: canvas.Canvas, text: str = "CONFIDENTIAL"):
    c.saveState()
    c.setFillColor(colors.HexColor("#eef2f7"))
    c.setFont("Helvetica-Bold", 42)
    c.translate(W / 2.0, H / 2.0)
    c.rotate(30)
    c.drawCentredString(0, 0, text)
    c.restoreState()


def _header(
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
    c.setFont("Helvetica-Bold", 17)
    c.drawString(M_L, H - 14.5 * mm, title)

    c.setFillColor(colors.HexColor("#cbd5e1"))
    c.setFont("Helvetica", 10)
    for i, ln in enumerate((subtitle or "").split("\n")[:2]):
        c.drawString(M_L, H - (21.5 * mm + i * 5 * mm), ln)

    if logo_path:
        try:
            c.drawImage(
                str(logo_path),
                W - M_R - 22 * mm,
                H - 20 * mm,
                width=18 * mm,
                height=18 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    pill_w = 50 * mm
    pill_h = 10 * mm
    bx = W - M_R - pill_w
    by = H - 20.5 * mm

    col = _badge_color(badge)
    c.setFillColor(col)
    c.roundRect(bx, by, pill_w, pill_h, 7, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(bx + 6 * mm, by + 2.7 * mm, (badge or "—").upper())


def _footer(c: canvas.Canvas, page: int, total: int, right_label: Optional[str] = None):
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#9ca3af"))
    c.drawString(M_L, FOOTER_Y, "Programma Alessio SaaS – Board-ready Report")
    if right_label:
        c.drawRightString(W - M_R, FOOTER_Y, right_label)
    else:
        c.drawRightString(W - M_R, FOOTER_Y, f"Pagina {page}/{total}")


def _shadow_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, r: float = 14):
    c.setFillColor(colors.HexColor("#eef2f7"))
    c.setStrokeColor(colors.transparent)
    c.roundRect(x + 1.4, y - 1.4, w, h, r, fill=1, stroke=0)

    c.setFillColor(DEFAULT_CARD)
    c.setStrokeColor(DEFAULT_STROKE)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def _bar(c: canvas.Canvas, x: float, y: float, w: float, h: float, score01: float, col):
    score01 = max(0.0, min(1.0, float(score01)))
    r = min(h / 2.0, 7)

    # Track
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

    # Partial: left rounded + square right edge
    body_x = x + r
    body_w = max(0.0, fill_w - r)
    if body_w > 0:
        c.rect(body_x, y, body_w, h, fill=1, stroke=0)
    c.circle(x + r, y + h / 2.0, r, stroke=0, fill=1)



def _risk_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    score01: float,
    desc: str,
):
    """Risk card with collision-proof layout.

    Guarantees:
    - title + badge always visible
    - value never overlaps description
    - description never overlaps bar
    - description is single-line (ellipsized) to avoid overflow
    """
    score01 = _clamp01(score01, 0.5) or 0.0
    label = _risk_bucket(score01)
    col = _badge_color(label)

    pad = 8 * mm
    _shadow_card(c, x, y, w, h, 16)

    # Top row: title + badge
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + pad, y + h - 11 * mm, title)

    bw, bh = 30 * mm, 9 * mm
    bx = x + w - pad - bw
    by = y + h - 12 * mm
    c.setFillColor(col)
    c.roundRect(bx, by, bw, bh, 7, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9.0)
    c.drawCentredString(bx + bw / 2, by + 2.7 * mm, label)

    # Bottom layout
    bar_h = 5.2 * mm
    bar_y = y + 3.0 * mm

    desc_font = "Helvetica"
    desc_size = 10
    desc_y = bar_y + bar_h + 3.2 * mm

    value_font = "Helvetica-Bold"
    value_size = 22
    value_y = desc_y + 7.0 * mm

    # Ensure we don't collide with the top row
    min_top_clear = y + h - 18 * mm
    if value_y > min_top_clear:
        shift = value_y - min_top_clear
        value_y -= shift
        desc_y -= shift
        # Keep bar anchored; only move it slightly if needed
        bar_y = max(y + 2.0 * mm, bar_y - min(shift, 1.0 * mm))

    # Value
    c.setFillColor(DEFAULT_TEXT)
    c.setFont(value_font, value_size)
    c.drawString(x + pad, value_y, f"{score01 * 100:.1f}%")

    # Description (single line, ellipsized)
    c.setFillColor(DEFAULT_MUTED)
    c.setFont(desc_font, desc_size)
    avail_w = w - 2 * pad
    desc_fit = _ellipsize(c, desc or "", avail_w, font=desc_font, size=desc_size)
    if desc_fit:
        c.drawString(x + pad, desc_y, desc_fit)

    # Bar
    _bar(c, x + pad, bar_y, w - 2 * pad, bar_h, score01, col)


def _kpi_card(
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
    _shadow_card(c, x, y, w, h, 16)
    pad = 10 * mm

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + pad, y + h - 10 * mm, title)

    c.setFont("Helvetica-Bold", 22)
    c.drawString(x + pad, y + h - 23 * mm, value)

    c.setFont("Helvetica", 10)
    c.setFillColor(DEFAULT_MUTED)
    c.drawString(x + pad, y + 8.0 * mm, subtitle)

    if target:
        c.setFont("Helvetica", 9.5)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawRightString(x + w - pad, y + 8.0 * mm, target)


def _triad_bar(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    score: int,
    accent=DEFAULT_ACCENT,
):
    if isinstance(accent, str):
        accent = colors.HexColor(accent)

    _shadow_card(c, x, y, w, 24 * mm, 16)
    pad = 10 * mm

    track_h = 6.5 * mm
    track_y = y + 6.0 * mm
    track_w = w - 2 * pad

    c.setFillColor(colors.HexColor("#eef2f7"))
    c.roundRect(x + pad, track_y, track_w, track_h, 7, fill=1, stroke=0)

    s = max(0, min(100, int(score)))
    c.setFillColor(accent)
    c.roundRect(x + pad, track_y, track_w * (s / 100.0), track_h, 7, fill=1, stroke=0)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 14.5)
    c.drawString(x + pad, y + 16 * mm, f"Triad Index™  {score}/100")


# =========================================================
# Helper: Bare progress bar (no card), for Triad mini version
# =========================================================
def _triad_progress(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    score: int,
    accent=DEFAULT_ACCENT,
):
    """Bare progress bar (no card), used inside other cards to avoid nested-card duplication."""
    if isinstance(accent, str):
        accent = colors.HexColor(accent)

    pad = 0
    track_h = 6.5 * mm
    track_w = w - 2 * pad

    c.setFillColor(colors.HexColor("#eef2f7"))
    c.roundRect(x + pad, y, track_w, track_h, 7, fill=1, stroke=0)

    s = max(0, min(100, int(score)))
    c.setFillColor(accent)
    c.roundRect(x + pad, y, track_w * (s / 100.0), track_h, 7, fill=1, stroke=0)


def _draw_radar(
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

    # Company polygon (resilience)
    pts: List[Tuple[float, float]] = []
    for i in range(n):
        resilience = 1.0 - (_clamp01(values[i], 0.5) or 0.5)
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

    # Benchmark contour
    pts_b: List[Tuple[float, float]] = []
    for i in range(n):
        resilience_b = 1.0 - (_clamp01(benchmark[i], 0.45) or 0.45)
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

    # Labels
    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica", 10)
    label_offset = 16
    for i in range(n):
        lx = cx + (r + label_offset) * cos(i * ang)
        ly = cy + (r + label_offset) * sin(i * ang)
        c.drawCentredString(lx, ly, labels[i])


# =========================================================
# Narrative helpers
# =========================================================
def _hero_insight(vm: Dict[str, Any]) -> str:
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    dom = _dominant_risk(risks)
    runway = kpi.get("runway_mesi")
    be = kpi.get("break_even_ratio")
    conv = kpi.get("conversione")

    bits: List[str] = [f"Vincolo primario: {dom}."]

    if runway is not None:
        try:
            r = float(runway)
            bits.append(f"Runway: {r:.1f} mesi.")
            if r < 6:
                bits.append("Sotto soglia di sicurezza (6 mesi).")
        except Exception:
            pass

    if be is not None:
        try:
            b = float(be)
            bits.append(f"Break-even coverage: {b:.2f}.")
            if b < 1.10:
                bits.append("Margine di sicurezza limitato.")
        except Exception:
            pass

    if conv is not None:
        try:
            ccv = float(conv)
            if ccv > 1:
                ccv = ccv / 100.0
            bits.append(f"Conversione: {ccv*100:.1f}%.")
        except Exception:
            pass

    bits.append("Implicazione: vulnerabilità a shock di liquidità nel breve periodo.")
    bits.append("Decisione: proteggere la cassa e congelare espansione fino a runway ≥ 6 mesi.")
    return " ".join(bits)


def _confidence_score(vm: Dict[str, Any]) -> int:
    required = [
        ("risks", "cash"),
        ("risks", "margini"),
        ("risks", "acq"),
        ("kpi", "runway_mesi"),
        ("kpi", "break_even_ratio"),
        ("kpi", "conversione"),
    ]
    missing = 0
    for root, key in required:
        obj = vm.get(root) or {}
        if obj.get(key) is None:
            missing += 1
    total = len(required)
    return max(0, int((1.0 - (missing / float(total))) * 100.0))


def _data_quality(vm: Dict[str, Any], scan_meta: Dict[str, Any]) -> Dict[str, Any]:
    """MVP: completezza + recenza + flags coerenza."""
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}
    notes: List[str] = []
    flags: List[str] = []

    required = [
        ("risks.cash", risks.get("cash")),
        ("risks.margini", risks.get("margini")),
        ("risks.acq", risks.get("acq")),
        ("kpi.runway_mesi", kpi.get("runway_mesi")),
        ("kpi.break_even_ratio", kpi.get("break_even_ratio")),
        ("kpi.conversione", kpi.get("conversione")),
    ]
    present = sum(1 for _, v in required if v is not None)
    completeness = int((present / float(len(required))) * 100.0)

    # Recency flag: if mese_riferimento missing => NOT OK
    rec = bool(scan_meta.get("mese_riferimento"))
    recency_flag = "OK" if rec else "NON OK"

    # Coerenza minima (MVP)
    conv = kpi.get("conversione")
    try:
        if conv is not None:
            cv = float(conv)
            if cv > 1:
                cv = cv / 100.0
            if cv < 0 or cv > 1:
                flags.append("Conversione fuori range (0..100%).")
    except Exception:
        flags.append("Conversione non numerica.")

    marg = kpi.get("margine_pct")
    try:
        if marg is not None:
            mv = float(marg)
            if mv > 1:
                mv = mv / 100.0
            if mv < -0.1 or mv > 0.95:
                flags.append("Margine lordo % anomalo.")
    except Exception:
        flags.append("Margine % non numerico.")

    # Stime (supporta payload con flags)
    estimated_notes: List[str] = []
    for key in ("dso_is_estimated", "incassi_is_estimated", "runway_is_estimated"):
        if vm.get(key) is True:
            reason = vm.get(key.replace("_is_estimated", "_estimation_reason")) or "Valore stimato."
            estimated_notes.append(f"{key.replace('_is_estimated','').upper()}: STIMA ({reason})")

    if estimated_notes:
        notes.extend(estimated_notes)

    # Badge
    if completeness >= 85 and rec and not flags:
        badge = "VERDE"
        label = "ALTA"
    elif completeness >= 60 and rec:
        badge = "GIALLO"
        label = "MEDIA"
    else:
        badge = "ROSSO"
        label = "BASSA"

    return {
        "badge": badge,
        "label": label,
        "completeness": completeness,
        "recency": recency_flag,
        "coherence_flags": flags,
        "notes": notes,
    }


def _definitions_payload(vm: Dict[str, Any]) -> List[Dict[str, str]]:
    # Preferisci definizioni dal payload, altrimenti default (MVP)
    defs = vm.get("definitions")
    if isinstance(defs, list) and defs:
        out: List[Dict[str, str]] = []
        for d in defs:
            if isinstance(d, dict):
                out.append({
                    "name": str(d.get("name", "")).strip(),
                    "definition": str(d.get("definition", "")).strip(),
                    "formula": str(d.get("formula", "")).strip(),
                    "unit": str(d.get("unit", "")).strip(),
                })
        if out:
            return out

    return [
        {"name": "Runway (mesi)", "definition": "Autonomia di cassa stimata.", "formula": "Cassa / Burn mensile (ultimo mese o media).", "unit": "mesi"},
        {"name": "Net Cash Flow", "definition": "Flusso di cassa netto periodo.", "formula": "Incassi − (Variabili + Fissi + Marketing + Rate).", "unit": "€"},
        {"name": "Break-even coverage", "definition": "Copertura costi fissi.", "formula": "Margine di contribuzione / Costi fissi (≥1.05 = copertura).", "unit": "ratio"},
        {"name": "Break-even ricavi", "definition": "Ricavi necessari a coprire i fissi.", "formula": "Costi fissi / % contribuzione (se disponibile).", "unit": "€/mese"},
        {"name": "Conversione", "definition": "Efficienza Lead→Clienti.", "formula": "Clienti / Lead (Lead = contatto qualificato nel periodo).", "unit": "%"},
        {"name": "Margine lordo %", "definition": "Margine prima dei fissi.", "formula": "(Ricavi − Variabili) / Ricavi.", "unit": "%"},
        {"name": "Triad Index™", "definition": "Indice sintetico (v1 calibrazione).", "formula": "Media resilienza 3 pilastri (1−risk).", "unit": "0–100"},
        {"name": "Rischio %", "definition": "Criticità per pilastro.", "formula": "Trasformazione risk 0..1 in % (0=ok, 100=critico).", "unit": "%"},
    ]


def _drivers_engine(vm: Dict[str, Any], scan_meta: Dict[str, Any]) -> Dict[str, List[str]]:
    """Driver MVP rule-based: 3 bullet per area, agganciati a KPI/quiz se presenti."""
    kpi = vm.get("kpi") or {}
    quiz = vm.get("quiz") or {}
    drivers = vm.get("drivers")  # se già forniti dal modello dati, usali
    if isinstance(drivers, dict) and drivers:
        out: Dict[str, List[str]] = {}
        for key in ("cash", "margins", "acquisition"):
            v = drivers.get(key) or drivers.get(key.upper()) or []
            if isinstance(v, list):
                out[key] = [str(x) for x in v][:3]
        if out:
            return out

    out: Dict[str, List[str]] = {"cash": [], "margins": [], "acquisition": []}

    runway = kpi.get("runway_mesi")
    ncf = kpi.get("net_cash_flow")
    dso = kpi.get("dso_giorni") or quiz.get("dso_giorni")
    rate = kpi.get("rate_debito_pct") or quiz.get("rate_debito_pct")
    contrib = kpi.get("contribuzione_pct") or kpi.get("margine_pct")
    fixed_ratio = kpi.get("fissi_su_ricavi_pct") or quiz.get("fissi_su_ricavi_pct")
    payback = kpi.get("payback_cac_mesi") or quiz.get("payback_cac_mesi")
    conv = kpi.get("conversione")

    # CASH
    try:
        if runway is not None and float(runway) < 1.0:
            out["cash"].append("Burn > incassi → runway sotto 1 mese (runway).")
    except Exception:
        pass
    try:
        if ncf is not None and float(ncf) < 0:
            out["cash"].append("Net Cash Flow negativo → cash drain (NCF).")
    except Exception:
        pass
    try:
        if dso is not None and float(dso) >= 45:
            out["cash"].append("Incassi lenti (DSO) → capitale bloccato (DSO).")
    except Exception:
        pass
    try:
        if rate is not None:
            rv = float(rate)
            if rv > 1:
                rv = rv / 100.0
            if rv >= 0.20:
                out["cash"].append("Debito che morde → rate alte su contribuzione (Rate%).")
    except Exception:
        pass

    # MARGINS
    try:
        if contrib is not None:
            mv = float(contrib)
            if mv > 1:
                mv = mv / 100.0
            if mv <= 0.30:
                out["margins"].append("Contribuzione insufficiente → pricing/mix/costi variabili (Contrib%).")
    except Exception:
        pass
    try:
        if fixed_ratio is not None:
            fv = float(fixed_ratio)
            if fv > 1:
                fv = fv / 100.0
            if fv >= 0.35:
                out["margins"].append("Struttura pesante → fissi troppo alti sui ricavi (Fissi/Ricavi).")
    except Exception:
        pass
    if not out["margins"]:
        out["margins"].append("Pressione margini → controlli su sconti e costi (margine/BE).")

    # ACQUISITION
    try:
        if payback is not None and float(payback) > 6.0:
            out["acquisition"].append("CAC payback > 6 mesi → acquisizione non sostenibile (Payback).")
    except Exception:
        pass
    try:
        if conv is not None:
            cv = float(conv)
            if cv > 1:
                cv = cv / 100.0
            if cv < 0.05:
                out["acquisition"].append("Funnel/follow-up inefficiente → conversione bassa (Conv%).")
            elif cv < 0.10:
                out["acquisition"].append("Conversione media → ottimizza messaggi/pipeline/next step (Conv%).")
    except Exception:
        pass
    out["acquisition"].append("Tracking per stage assente → impossibile isolare colli di bottiglia (pipeline).")

    # Ensure exactly 3 bullets per section (pad)
    for k in out.keys():
        out[k] = out[k][:3]
        while len(out[k]) < 3:
            out[k].append("Driver da validare: completa dati per aumentare confidenza e precisione.")
    return out


def _benchmark_meta(vm: Dict[str, Any], settore: str) -> Dict[str, Any]:
    meta = vm.get("benchmark_meta")
    if isinstance(meta, dict) and meta:
        enabled = bool(meta.get("enabled", False))
        return {
            "enabled": enabled,
            "source": str(meta.get("source", "")).strip(),
            "sample_n": meta.get("sample_n"),
            "sector_definition": str(meta.get("sector_definition", "")).strip(),
            "note": str(meta.get("note", "")).strip(),
        }

    # Default: DISABLED (onesto)
    return {
        "enabled": False,
        "source": "",
        "sample_n": None,
        "sector_definition": "",
        "note": "Benchmark disattivato: baseline in calibrazione (v1). Suggerimento: abilita benchmark solo con fonte/campione/definizione settore.",
    }


def _plan_tasks(vm: Dict[str, Any], kpi: Dict[str, Any]) -> List[Dict[str, str]]:
    tasks = vm.get("plan_tasks")
    if isinstance(tasks, list) and tasks:
        out: List[Dict[str, str]] = []
        for t in tasks:
            if isinstance(t, dict):
                out.append({
                    "week": str(t.get("week", "")).strip(),
                    "action": str(t.get("action", "")).strip(),
                    "owner": str(t.get("owner", "")).strip(),
                    "target_kpi": str(t.get("target_kpi", "")).strip(),
                    "target_value": str(t.get("target_value", "")).strip(),
                    "why": str(t.get("why", "")).strip(),
                })
        if out:
            return out

    # MVP 4 weeks default
    return [
        {
            "week": "1",
            "action": "Imposta cashflow settimanale + scadenziario incassi/pagamenti; definisci soglie stop-spesa.",
            "owner": "CEO/Finance",
            "target_kpi": "Runway · NCF",
            "target_value": "Runway ≥ 6 mesi · NCF ≥ 0",
            "why": "Ridurre rischio liquidità e variabilità incassi.",
        },
        {
            "week": "2",
            "action": "Revisione listino + stop sconti non autorizzati + controllo costi variabili; aggiorna margini per servizio.",
            "owner": "CEO/Ops",
            "target_kpi": "BE coverage · Margine",
            "target_value": "BE ≥ 1.10 · Margine ↑",
            "why": "Aumentare contribuzione e stabilizzare break-even.",
        },
        {
            "week": "3",
            "action": "Standardizza pipeline: stage, criteri, next step obbligatorio; follow-up entro 48h; tracking conversioni per stage.",
            "owner": "Sales Lead",
            "target_kpi": "Conversione",
            "target_value": "≥ 10% (trend ↑)",
            "why": "Ridurre dispersione nel funnel e aumentare chiusure.",
        },
        {
            "week": "4",
            "action": "Audit incassi: DSO, solleciti strutturati, policy pagamenti; negozia termini e rate dove possibile.",
            "owner": "Finance/Ops",
            "target_kpi": "DSO · NCF",
            "target_value": "DSO ↓ · NCF ≥ 0",
            "why": "Liberare capitale e ridurre stress di cassa.",
        },
    ]


# =========================================================
# PUBLIC API (alias)
# =========================================================
# =========================================================
# PUBLIC API
# =========================================================
def generate_report(
    out_path: Union[str, Path],
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
    template: str = "saas_scan_v1",
) -> Path:
    """High-level report API.

    template:
      - "saas_scan_v1" (default): 5-page landscape board-pack scan

    Notes:
      - For fast iteration you can pass in vm:
          vm["render_only_page"] = 1..5
        or:
          vm["dev_page"] = 1..5
    """
    template = (template or "saas_scan_v1").strip().lower()
    if template in ("saas_scan_v1", "scan", "triade_scan"):
        return generate_scan_pdf_enterprise(out_path, scan_meta, vm)
    raise ValueError(f"Unknown template: {template}")


# Backward compatible alias
def generate_scan_pdf(
    out_path: Union[str, Path],
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    return generate_report(out_path, scan_meta, vm, template="saas_scan_v1")


def _as_color(value: Any, default: colors.Color) -> colors.Color:
    if isinstance(value, colors.Color):
        return value
    if isinstance(value, str):
        try:
            return colors.HexColor(value)
        except Exception:
            return default
    return default


# =========================================================
# ENTERPRISE MODE (board-ready) — Landscape 5 pages
# =========================================================

DEFAULT_TOTAL_PAGES = 5

# =========================================================
# Context builder helper
# =========================================================
def _build_context(
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
    primary: colors.Color,
    accent: colors.Color,
    watermark_text: str,
    logo_path: Optional[Union[str, Path]],
) -> Dict[str, Any]:
    """Build a single rendering context dict.

    This isolates data-munging from drawing code and makes the file easier to split
    into modules later (layout/primitives/pages/engine).
    """
    risks = vm.get("risks") or {}
    state = vm.get("state") or {}
    kpi = vm.get("kpi") or {}

    settore = scan_meta.get("settore", "—")
    modello = scan_meta.get("modello", "—")
    mese = scan_meta.get("mese_riferimento", "—")
    created_at = scan_meta.get("created_at") or _now()
    scan_id = scan_meta.get("id", "—")

    overall = (state.get("overall") or state.get("stato") or "STABILE")
    overall = str(overall).upper()
    if overall in ("ROSSO", "GIALLO", "VERDE"):
        overall = {"ROSSO": "CRITICO", "GIALLO": "ATTENZIONE", "VERDE": "STABILE"}[overall]

    triad = _triad_index(risks)
    confidence = _confidence_score(vm)
    dq = _data_quality(vm, scan_meta)

    sector_key = settore if settore in SECTOR_BENCHMARKS else "Default"
    benchmark = SECTOR_BENCHMARKS.get(sector_key, SECTOR_BENCHMARKS["Default"])

    cash_r = _clamp01(risks.get("cash"), 0.5) or 0.5
    marg_r = _clamp01(risks.get("margini"), 0.5) or 0.5
    acq_r = _clamp01(risks.get("acq"), 0.5) or 0.5

    hero = _hero_insight(vm)

    # Added payloads (MVP)
    defs = _definitions_payload(vm)
    drivers = _drivers_engine(vm, scan_meta)
    bm = _benchmark_meta(vm, settore)
    plan = _plan_tasks(vm, kpi)

    runway = kpi.get("runway_mesi")
    be = kpi.get("break_even_ratio")
    conv = kpi.get("conversione")
    marg = kpi.get("margine_pct")
    ncf = kpi.get("net_cash_flow")
    be_rev = kpi.get("break_even_ricavi")

    return {
        "vm": vm,
        "scan_meta": scan_meta,
        "primary": primary,
        "accent": accent,
        "watermark_text": watermark_text,
        "logo_path": logo_path,
        "overall": overall,
        "settore": settore,
        "modello": modello,
        "mese": mese,
        "created_at": created_at,
        "scan_id": scan_id,
        "triad": triad,
        "confidence": confidence,
        "dq": dq,
        "benchmark": benchmark,
        "cash_r": cash_r,
        "marg_r": marg_r,
        "acq_r": acq_r,
        "hero": hero,
        "defs": defs,
        "drivers": drivers,
        "bm": bm,
        "plan": plan,
        "runway": runway,
        "be": be,
        "conv": conv,
        "marg": marg,
        "ncf": ncf,
        "be_rev": be_rev,
    }

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
        f"Settore: {ctx['settore']} · Modello: {ctx['modello']} · Mese: {ctx['mese']}\nCreato: {ctx['created_at']} · Scan #{ctx['scan_id']}",
        ctx["overall"],
        primary=ctx["primary"],
        logo_path=ctx["logo_path"],
    )

    top_y = H - HEADER_H - 12 * mm

    left_w = SAFE_W * 0.40
    right_w = SAFE_W - left_w - 10 * mm

    boxA_h = 56 * mm
    boxA_y = top_y - boxA_h
    _shadow_card(c, M_L, boxA_y, left_w, boxA_h, 16)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(M_L + 10 * mm, boxA_y + boxA_h - 16 * mm, f"Triad Index™  {ctx['triad']}/100")

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 10.5)
    c.drawString(M_L + 10 * mm, boxA_y + boxA_h - 28 * mm, "Media resilienza 3 pilastri (v1)")

    _triad_progress(c, M_L + 10 * mm, boxA_y + 20 * mm, left_w - 20 * mm, ctx["triad"], accent=ctx["accent"])

    dq = ctx["dq"]
    dq_badge = dq.get("badge", "GIALLO")
    dq_label = dq.get("label", "MEDIA")
    chip_col = _badge_color(dq_badge)

    chip_w, chip_h = 32 * mm, 8.5 * mm
    chip_x = M_L + left_w - 10 * mm - chip_w
    chip_y = boxA_y + 7.5 * mm

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 11)
    conf_text = f"Confidence: {ctx['confidence']}% · v1 (calibrazione)"
    conf_fit = _ellipsize(c, conf_text, (chip_x - (M_L + 10 * mm) - 3 * mm), font="Helvetica-Bold", size=11)
    c.drawString(M_L + 10 * mm, boxA_y + 10.2 * mm, conf_fit)

    c.setFillColor(chip_col)
    c.roundRect(chip_x, chip_y, chip_w, chip_h, 6, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString(chip_x + chip_w / 2, chip_y + 2.4 * mm, f"QUALITÀ {dq_label}")

    ins_h = 56 * mm
    ins_y = top_y - ins_h
    _shadow_card(c, M_L + left_w + 10 * mm, ins_y, right_w, ins_h, 16)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(M_L + left_w + 20 * mm, top_y - 12 * mm, "Executive insight")

    c.setFont("Helvetica", 11.5)
    c.setFillColor(DEFAULT_TEXT)
    lines = _wrap(c, ctx["hero"], right_w - 20 * mm, size=11.5)
    yy = top_y - 26 * mm
    for ln in lines[:5]:
        c.drawString(M_L + left_w + 20 * mm, yy, ln)
        yy -= 6.0 * mm

    gap = 10 * mm
    gloss_h = 66 * mm
    gloss_top = ins_y - gap
    gloss_y = gloss_top - gloss_h
    _shadow_card(c, M_L, gloss_y, SAFE_W, gloss_h, 16)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 10 * mm, gloss_top - 12 * mm, "Definizioni & formule")

    bullet_font = "Helvetica"
    bullet_size = 10.2
    c.setFont(bullet_font, bullet_size)
    c.setFillColor(DEFAULT_TEXT)

    col_gap = 10 * mm
    col_w = (SAFE_W - 20 * mm - col_gap) / 2.0
    x1 = M_L + 10 * mm
    x2 = x1 + col_w + col_gap
    y_start = gloss_top - 24 * mm
    line_h = 5.4 * mm

    items: List[str] = []
    for d in (ctx.get("defs") or [])[:8]:
        name = (d.get("name") or "").strip()
        formula = (d.get("formula") or "").strip()
        s = f"• {name} = {formula}"
        items.append(s)

    left_items = items[:4]
    right_items = items[4:8]

    yy1 = y_start
    for it in left_items:
        wlines = _wrap(c, it, col_w, font=bullet_font, size=bullet_size)
        _draw_multiline(c, x1, yy1, wlines, line_h, max_lines=2)
        yy1 -= line_h * (min(2, max(1, len(wlines)))) + 1.2 * mm

    yy2 = y_start
    for it in right_items:
        wlines = _wrap(c, it, col_w, font=bullet_font, size=bullet_size)
        _draw_multiline(c, x2, yy2, wlines, line_h, max_lines=2)
        yy2 -= line_h * (min(2, max(1, len(wlines)))) + 1.2 * mm

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.5)
    dq_line = f"Completezza: {dq.get('completeness', 0)}% · Recenza: {dq.get('recency', '—')}"
    if dq.get("coherence_flags"):
        dq_line += f" · Coerenza: {len(dq['coherence_flags'])} flag"
    c.drawString(M_L + 10 * mm, gloss_y + 8 * mm, dq_line)

    _footer(c, page_no, total, right_label=right_label)


def _page_2_risk_snapshot(
    c: canvas.Canvas,
    ctx: Dict[str, Any],
    page_no: int,
    total: int,
    right_label: Optional[str] = None,
) -> None:
    _page_bg(c)
    _watermark(c, ctx["watermark_text"])
    _header(c, "Risk Snapshot", f"{ctx['settore']} · {ctx['mese']}", ctx["overall"], primary=ctx["primary"], logo_path=ctx["logo_path"])

    top_y = H - HEADER_H - 12 * mm

    card_h = 52 * mm
    gap = 10 * mm
    col_w = (SAFE_W - 2 * gap) / 3.0

    y_cards = top_y - card_h
    _risk_card(c, M_L, y_cards, col_w, card_h, "Rischio Cassa", ctx["cash_r"], "Cashflow / runway / incassi")
    _risk_card(c, M_L + col_w + gap, y_cards, col_w, card_h, "Rischio Margini", ctx["marg_r"], "Margine & controllo costi")
    _risk_card(c, M_L + 2 * (col_w + gap), y_cards, col_w, card_h, "Rischio Acquisizione", ctx["acq_r"], "Funnel, conversione, follow-up")

    drv_top = y_cards - 10 * mm
    drv_h = 96 * mm
    drv_y = drv_top - drv_h
    _shadow_card(c, M_L, drv_y, SAFE_W, drv_h, 16)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 10 * mm, drv_top - 12 * mm, "Top driver (perché) — MVP")

    drv_col_gap = 10 * mm
    drv_col_w = (SAFE_W - 20 * mm - 2 * drv_col_gap) / 3.0
    dx1 = M_L + 10 * mm
    dx2 = dx1 + drv_col_w + drv_col_gap
    dx3 = dx2 + drv_col_w + drv_col_gap

    title_y = drv_top - 24 * mm
    c.setFont("Helvetica-Bold", 11.5)
    c.setFillColor(DEFAULT_TEXT)
    c.drawString(dx1, title_y, "Cassa")
    c.drawString(dx2, title_y, "Margini")
    c.drawString(dx3, title_y, "Acquisizione")

    bullet_font = "Helvetica"
    bullet_size = 10.5
    c.setFont(bullet_font, bullet_size)
    c.setFillColor(DEFAULT_TEXT)

    base_y = title_y - 10 * mm
    line_h = 5.6 * mm

    def _draw_driver_list(x: float, y_top_: float, items_: List[str]):
        yy_ = y_top_
        for b in items_[:3]:
            text = f"• {b}"
            wlines = _wrap(c, text, drv_col_w, font=bullet_font, size=bullet_size)
            _draw_multiline(c, x, yy_, wlines, line_h, max_lines=2)
            yy_ -= line_h * (min(2, max(1, len(wlines)))) + 2.0 * mm

    drivers = ctx.get("drivers") or {}
    _draw_driver_list(dx1, base_y, drivers.get("cash", []))
    _draw_driver_list(dx2, base_y, drivers.get("margins", []))
    _draw_driver_list(dx3, base_y, drivers.get("acquisition", []))

    _footer(c, page_no, total, right_label=right_label)


def _page_3_kpi(
    c: canvas.Canvas,
    ctx: Dict[str, Any],
    page_no: int,
    total: int,
    right_label: Optional[str] = None,
) -> None:
    _page_bg(c)
    _watermark(c, ctx["watermark_text"])
    _header(c, "KPI", f"{ctx['settore']} · {ctx['mese']}", ctx["overall"], primary=ctx["primary"], logo_path=ctx["logo_path"])

    top_y = H - HEADER_H - 12 * mm

    kw = (SAFE_W - 10 * mm) / 2.0
    kh = 44 * mm

    runway = ctx.get("runway")
    be = ctx.get("be")
    conv = ctx.get("conv")
    marg = ctx.get("marg")

    y = top_y - kh
    _kpi_card(
        c, M_L, y, kw, kh,
        "RUNWAY (MESI)",
        (f"{float(runway):.1f}" if runway is not None else "—"),
        "Cassa / burn mensile",
        target="Target: ≥ 6 mesi",
    )
    _kpi_card(
        c, M_L + kw + 10 * mm, y, kw, kh,
        "BREAK-EVEN COVERAGE",
        (_fmt_num(be, 2) if be is not None else "—"),
        "Margine contribuzione / costi fissi",
        target="Target: ≥ 1.10",
    )

    y2 = y - 10 * mm - kh
    _kpi_card(
        c, M_L, y2, kw, kh,
        "CONVERSIONE",
        (_fmt_pct01(conv) if conv is not None else "—"),
        "Clienti / lead",
        target="Target: ≥ 10%",
    )
    _kpi_card(
        c, M_L + kw + 10 * mm, y2, kw, kh,
        "MARGINE LORDO",
        (_fmt_pct01(marg) if marg is not None else "—"),
        "(Ricavi − variabili) / ricavi",
        target="Stabilizzare contribuzione",
    )

    strip_top = y2 - 12 * mm
    strip_h = 26 * mm
    strip_y = strip_top - strip_h
    _shadow_card(c, M_L, strip_y, SAFE_W, strip_h, 16)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(M_L + 10 * mm, strip_top - 10 * mm, "KPI aggiuntivi (se disponibili)")

    c.setFont("Helvetica", 10.5)
    c.setFillColor(DEFAULT_TEXT)
    left = f"Net Cash Flow: {_fmt_eur(ctx.get('ncf'), 0) if ctx.get('ncf') is not None else '—'}"
    right = f"Break-even ricavi: {_fmt_eur(ctx.get('be_rev'), 0) if ctx.get('be_rev') is not None else '—'}"
    c.drawString(M_L + 10 * mm, strip_y + 8.5 * mm, left)
    c.drawRightString(W - M_R - 10 * mm, strip_y + 8.5 * mm, right)

    note_top = strip_y - 10 * mm
    note_h = 58 * mm
    note_y = note_top - note_h
    _shadow_card(c, M_L, note_y, SAFE_W, note_h, 16)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 10 * mm, note_top - 12 * mm, "Nota decisionale (sequenza consigliata)")

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica", 11)
    note = (
        "1) Stabilizzare runway e break-even (cash discipline + margini). "
        "2) Controllare cashflow e variabilità incassi (NCF, DSO, scadenziario). "
        "3) Ottimizzare conversione e scala commerciale solo dopo stabilizzazione."
    )
    nlines = _wrap(c, note, SAFE_W - 20 * mm, size=11)
    yy = note_top - 28 * mm
    for ln in nlines[:5]:
        c.drawString(M_L + 10 * mm, yy, ln)
        yy -= 6.0 * mm

    _footer(c, page_no, total, right_label=right_label)


def _page_4_radar(
    c: canvas.Canvas,
    ctx: Dict[str, Any],
    page_no: int,
    total: int,
    right_label: Optional[str] = None,
) -> None:
    _page_bg(c)
    _watermark(c, ctx["watermark_text"])
    _header(c, "Radar & Benchmark", f"{ctx['settore']}", ctx["overall"], primary=ctx["primary"], logo_path=ctx["logo_path"])

    top_y = H - HEADER_H - 12 * mm

    card_h = 170 * mm
    card_y = top_y - card_h
    _shadow_card(c, M_L, card_y, SAFE_W, card_h, 16)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(M_L + 10 * mm, top_y - 12 * mm, "Radar (Azienda vs Benchmark)")

    bm = ctx.get("bm") or {}
    if not bm.get("enabled", False):
        c.setFillColor(DEFAULT_MUTED)
        c.setFont("Helvetica", 11.5)
        msg = bm.get("note") or "Benchmark disattivato: baseline in calibrazione (v1)."
        lines = _wrap(c, msg, SAFE_W - 20 * mm, size=11.5)
        yy = top_y - 34 * mm
        for ln in lines[:6]:
            c.drawString(M_L + 10 * mm, yy, ln)
            yy -= 6.2 * mm
    else:
        cx = M_L + SAFE_W * 0.62
        cy = card_y + card_h / 2.0 - 6 * mm
        radar_r = min(SAFE_W, card_h) * 0.30

        _draw_radar(
            c,
            cx,
            cy,
            radar_r,
            ["Cassa", "Margini", "Acquisizione"],
            [ctx["cash_r"], ctx["marg_r"], ctx["acq_r"]],
            ctx["benchmark"],
            accent=ctx["accent"],
        )

        meta_x = M_L + 10 * mm
        meta_w = SAFE_W * 0.42
        meta_y = card_y + 18 * mm
        meta_h = card_h - 36 * mm
        _shadow_card(c, meta_x, meta_y, meta_w, meta_h, 14)

        c.setFillColor(DEFAULT_TEXT)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(meta_x + 8 * mm, meta_y + meta_h - 12 * mm, "Benchmark metadata")

        c.setFont("Helvetica", 10.5)
        c.setFillColor(DEFAULT_TEXT)
        src = bm.get("source") or "—"
        n = bm.get("sample_n")
        sect = bm.get("sector_definition") or "—"
        c.drawString(meta_x + 8 * mm, meta_y + meta_h - 26 * mm, f"Fonte: {src}")
        c.drawString(meta_x + 8 * mm, meta_y + meta_h - 38 * mm, f"Campione: n={n if n is not None else '—'}")
        c.drawString(meta_x + 8 * mm, meta_y + meta_h - 50 * mm, f"Settore: {sect}")

        note = bm.get("note") or ""
        if note:
            c.setFillColor(DEFAULT_MUTED)
            c.setFont("Helvetica", 10)
            lines = _wrap(c, note, meta_w - 16 * mm, size=10)
            yy = meta_y + meta_h - 66 * mm
            for ln in lines[:6]:
                c.drawString(meta_x + 8 * mm, yy, ln)
                yy -= 5.4 * mm

    _footer(c, page_no, total, right_label=right_label)


def _page_5_execution(
    c: canvas.Canvas,
    ctx: Dict[str, Any],
    page_no: int,
    total: int,
    right_label: Optional[str] = None,
) -> None:
    _page_bg(c)
    _watermark(c, ctx["watermark_text"])
    _header(c, "Execution", f"{ctx['settore']} · {ctx['mese']}", ctx["overall"], primary=ctx["primary"], logo_path=ctx["logo_path"])

    top_y = H - HEADER_H - 12 * mm

    vm = ctx.get("vm") or {}
    runway = ctx.get("runway")
    conv = ctx.get("conv")

    alerts = vm.get("alerts") or []
    if not alerts:
        alerts = []
        try:
            if runway is not None and float(runway) < 6:
                alerts.append({"level": "ATTENZIONE", "text": f"Runway {float(runway):.1f} mesi: margine di sicurezza limitato. Cashflow settimanale consigliato."})
        except Exception:
            pass
        try:
            if conv is not None:
                cv = float(conv)
                if cv > 1:
                    cv = cv / 100.0
                if cv < 0.10:
                    alerts.append({"level": "ATTENZIONE", "text": f"Conversione {cv*100:.2f}%: ottimizza messaggi, pipeline e prossimi step."})
        except Exception:
            pass
        if not alerts:
            alerts = [{"level": "ATTENZIONE", "text": "Completa i dati chiave per aumentare confidenza e precisione del report."}]

    left_w = SAFE_W * 0.44
    right_w = SAFE_W - left_w - 10 * mm

    alerts_h = 112 * mm
    alerts_y = top_y - alerts_h
    _shadow_card(c, M_L, alerts_y, left_w, alerts_h, 16)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M_L + 10 * mm, top_y - 12 * mm, "Alert automatici")

    yy = top_y - 28 * mm
    for a in alerts[:6]:
        lvl = str(a.get("level", "ATTENZIONE")).upper()
        if lvl in ("ROSSO", "GIALLO", "VERDE"):
            lvl = {"ROSSO": "CRITICO", "GIALLO": "ATTENZIONE", "VERDE": "STABILE"}[lvl]
        txt = str(a.get("text", ""))

        col = _badge_color(lvl)
        c.setFillColor(col)
        c.roundRect(M_L + 10 * mm, yy - 4.0 * mm, 34 * mm, 10 * mm, 7, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(M_L + 27 * mm, yy - 1.2 * mm, lvl[:12])

        c.setFillColor(DEFAULT_TEXT)
        c.setFont("Helvetica", 10.8)
        lines = _wrap(c, txt, left_w - 56 * mm, size=10.8)
        for i, ln in enumerate(lines[:3]):
            if i == 0:
                c.setFillColor(DEFAULT_TEXT)
            else:
                c.setFillColor(DEFAULT_MUTED)
            c.drawString(M_L + 50 * mm, yy - i * 5.6 * mm, ln)
        c.setFillColor(DEFAULT_TEXT)

        yy -= 16 * mm
        if yy < alerts_y + 14 * mm:
            break

    plan = ctx.get("plan") or []
    plan_h = 128 * mm
    plan_y = top_y - plan_h
    plan_x = M_L + left_w + 10 * mm
    _shadow_card(c, plan_x, plan_y, right_w, plan_h, 16)

    c.setFillColor(DEFAULT_TEXT)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(plan_x + 10 * mm, top_y - 12 * mm, "90 Day Plan (task-based) — MVP 4 settimane")

    pad = 10 * mm
    tx = plan_x + pad
    ty = top_y - 26 * mm

    inner_w = right_w - 2 * pad
    w_week = 10 * mm
    w_owner = 24 * mm
    w_kpi = 26 * mm
    w_target = 34 * mm
    w_action = inner_w - (w_week + w_owner + w_kpi + w_target + 6 * mm)

    c.setFont("Helvetica-Bold", 9.8)
    c.setFillColor(colors.HexColor("#334155"))

    ax_h = tx + w_week + 2 * mm
    ox_h = ax_h + w_action + 2 * mm
    kx_h = ox_h + w_owner + 2 * mm
    vx_h = kx_h + w_kpi + 2 * mm

    c.drawString(tx, ty, "SETT.")
    c.drawString(ax_h, ty, "AZIONE (incl. WHY)")
    c.drawString(ox_h, ty, "OWNER")
    c.drawString(kx_h, ty, "KPI")
    c.drawString(vx_h, ty, "TARGET")

    c.setStrokeColor(colors.HexColor("#e5e7eb"))
    c.setLineWidth(1)
    c.line(plan_x + 8 * mm, ty - 3.5 * mm, plan_x + right_w - 8 * mm, ty - 3.5 * mm)

    c.setFont("Helvetica", 9.6)
    c.setFillColor(DEFAULT_TEXT)

    row_y = ty - 10 * mm
    row_min_h = 18 * mm
    line_h = 4.8 * mm

    for t in plan[:4]:
        week = str(t.get("week", "")).strip() or "—"
        owner = str(t.get("owner", "")).strip() or "—"
        kpi_name = str(t.get("target_kpi", "")).strip() or "—"
        target_val = str(t.get("target_value", "")).strip() or "—"
        action = str(t.get("action", "")).strip()
        why = str(t.get("why", "")).strip()

        ax = tx + w_week + 2 * mm
        ox = ax + w_action + 2 * mm
        kx = ox + w_owner + 2 * mm
        vx = kx + w_kpi + 2 * mm

        action_lines = _wrap(c, action, w_action, size=9.6)
        why_lines = _wrap(c, f"Why: {why}", w_action, size=9.2) if why else []
        merged = action_lines[:4]
        if why_lines:
            merged.append(why_lines[0])
        merged = merged[:5]

        kpi_lines = _wrap(c, kpi_name, w_kpi, size=9.6) or ["—"]
        target_lines = _wrap(c, target_val, w_target, size=9.6) or ["—"]

        needed_h = max(
            row_min_h,
            (max(len(merged), len(kpi_lines), len(target_lines)) * line_h) + 6 * mm,
        )
        if row_y - needed_h < plan_y + 12 * mm:
            break

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(DEFAULT_TEXT)
        c.drawString(tx, row_y, week)

        c.setFont("Helvetica", 9.6)
        c.setFillColor(DEFAULT_TEXT)
        yy2 = row_y
        action_cut = min(4, len(action_lines))
        for i, ln in enumerate(merged):
            if why_lines and i >= action_cut:
                c.setFillColor(DEFAULT_MUTED)
                c.setFont("Helvetica", 9.2)
            else:
                c.setFillColor(DEFAULT_TEXT)
                c.setFont("Helvetica", 9.6)
            c.drawString(ax, yy2, ln)
            yy2 -= line_h

        c.setFillColor(DEFAULT_TEXT)
        c.setFont("Helvetica", 9.6)
        c.drawString(ox, row_y, _ellipsize(c, owner, w_owner, font="Helvetica", size=9.6))

        ky = row_y
        for ln in kpi_lines[:3]:
            c.drawString(kx, ky, ln)
            ky -= line_h

        vy = row_y
        for ln in target_lines[:3]:
            c.drawString(vx, vy, ln)
            vy -= line_h

        c.setStrokeColor(colors.HexColor("#f1f5f9"))
        c.setLineWidth(1)
        c.line(plan_x + 8 * mm, row_y - needed_h + 6 * mm, plan_x + right_w - 8 * mm, row_y - needed_h + 6 * mm)

        row_y -= needed_h

    c.setFillColor(DEFAULT_MUTED)
    c.setFont("Helvetica", 9.2)
    c.drawString(plan_x + 10 * mm, plan_y + 8 * mm, "Owner = ruolo responsabile · KPI target = metrica verificabile (trend/valore)")

    _footer(c, page_no, total, right_label=right_label)

def generate_scan_pdf_enterprise(
    out_path: Union[str, Path],
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)

    branding = vm.get("branding") or {}
    primary = _as_color(branding.get("primary"), DEFAULT_PRIMARY)
    accent = _as_color(branding.get("accent"), DEFAULT_ACCENT)
    watermark_text = str(branding.get("watermark", "CONFIDENTIAL") or "CONFIDENTIAL")
    logo_path = branding.get("logo_path")

    ctx: Dict[str, Any] = _build_context(scan_meta, vm, primary, accent, watermark_text, logo_path)

    # Dev/preview mode: render only one page for faster iteration
    render_only = vm.get("render_only_page") or vm.get("dev_page")
    total_pages = DEFAULT_TOTAL_PAGES

    page_fns = {
        1: _page_1_executive,
        2: _page_2_risk_snapshot,
        3: _page_3_kpi,
        4: _page_4_radar,
        5: _page_5_execution,
    }

    if isinstance(render_only, int) and 1 <= render_only <= total_pages:
        fn = page_fns[render_only]
        right = f"Estratto: pagina {render_only}/{total_pages}"
        fn(c, ctx, page_no=1, total=1, right_label=right)
        c.save()
        return out_path

    # Full report
    _page_1_executive(c, ctx, page_no=1, total=total_pages)
    c.showPage()

    _page_2_risk_snapshot(c, ctx, page_no=2, total=total_pages)
    c.showPage()

    _page_3_kpi(c, ctx, page_no=3, total=total_pages)
    c.showPage()

    _page_4_radar(c, ctx, page_no=4, total=total_pages)
    c.showPage()

    _page_5_execution(c, ctx, page_no=5, total=total_pages)
    c.save()
    return out_path
