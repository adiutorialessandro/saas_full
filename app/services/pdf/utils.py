from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.pdfgen import canvas


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def clamp01(x: Any, default: Optional[float] = 0.0) -> Optional[float]:
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


def fmt_pct01(x: Any) -> str:
    v = clamp01(x, default=None)
    if v is None:
        return "—"
    return f"{v * 100.0:.2f}%"


def fmt_num(x: Any, decimals: int = 2) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.{decimals}f}"
    except Exception:
        return "—"


def fmt_eur(x: Any, decimals: int = 0) -> str:
    if x is None:
        return "—"
    try:
        v = float(x)
        fmt = f"{{:,.{decimals}f}} €"
        return fmt.format(v).replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def risk_bucket(score01: float) -> str:
    if score01 >= 0.66:
        return "CRITICO"
    if score01 >= 0.33:
        return "ATTENZIONE"
    return "STABILE"


def badge_color(label: str) -> colors.Color:
    s = (label or "").upper()
    return {
        "CRITICO": colors.HexColor("#d64545"),
        "ATTENZIONE": colors.HexColor("#f1c644"),
        "STABILE": colors.HexColor("#28a55f"),
        "ROSSO": colors.HexColor("#d64545"),
        "GIALLO": colors.HexColor("#f1c644"),
        "VERDE": colors.HexColor("#28a55f"),
    }.get(s, colors.HexColor("#64748b"))


def triad_index(risks: Dict[str, Any]) -> int:
    cash = clamp01(risks.get("cash"), 0.5) or 0.5
    marg = clamp01(risks.get("margini"), 0.5) or 0.5
    acq = clamp01(risks.get("acq"), 0.5) or 0.5
    vals = [1.0 - cash, 1.0 - marg, 1.0 - acq]
    return int((sum(vals) / 3.0) * 100.0)


def dominant_risk(risks: Dict[str, Any]) -> str:
    m = {
        "CASSA": clamp01(risks.get("cash"), 0.0) or 0.0,
        "MARGINI": clamp01(risks.get("margini"), 0.0) or 0.0,
        "ACQUISIZIONE": clamp01(risks.get("acq"), 0.0) or 0.0,
    }
    return max(m.items(), key=lambda kv: kv[1])[0]


def wrap(
    c: canvas.Canvas,
    text: str,
    max_w: float,
    font: str = "Helvetica",
    size: float = 10,
) -> List[str]:
    c.setFont(font, size)
    words = (text or "").split()
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


def ellipsize(
    c: canvas.Canvas,
    text: str,
    max_w: float,
    font: str = "Helvetica",
    size: float = 10,
) -> str:
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


def draw_multiline(
    c: canvas.Canvas,
    x: float,
    y: float,
    lines: List[str],
    line_h: float,
    max_lines: int = 2,
) -> int:
    used = 0
    for ln in lines[:max_lines]:
        c.drawString(x, y - used * line_h, ln)
        used += 1
    return used


# Helper for radar geometry
Point = Tuple[float, float]
