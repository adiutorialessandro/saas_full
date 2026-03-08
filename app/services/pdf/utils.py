from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from reportlab.pdfbase.pdfmetrics import stringWidth


def clamp01(value: Any, default: Optional[float] = 0.0) -> Optional[float]:
    try:
        if value is None:
            return default
        v = float(value)
        if v < 0:
            return 0.0
        if v > 1:
            return 1.0
        return v
    except Exception:
        return default


def now_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def fmt_pct(value: Any, digits: int = 1) -> str:
    v = safe_float(value, None)
    if v is None:
        return "—"
    if v > 1:
        return f"{v:.{digits}f}%"
    return f"{v * 100:.{digits}f}%"


def fmt_num(value: Any, digits: int = 1, suffix: str = "") -> str:
    v = safe_float(value, None)
    if v is None:
        return "—"
    return f"{v:.{digits}f}{suffix}"


def fmt_money(value: Any, digits: int = 0) -> str:
    v = safe_float(value, None)
    if v is None:
        return "—"
    return f"€ {v:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def risk_label(value: Any) -> str:
    v = clamp01(value, 0.5) or 0.5
    if v >= 0.66:
        return "ROSSO"
    if v >= 0.33:
        return "GIALLO"
    return "VERDE"


def risk_pct(value: Any) -> int:
    v = clamp01(value, 0.5) or 0.5
    return int(round(v * 100))


def wrap_text(text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    if not text:
        return []
    words = str(text).split()
    lines: List[str] = []
    current = ""

    for word in words:
        test = word if not current else f"{current} {word}"
        if stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def truncate_lines(lines: List[str], max_lines: int) -> List[str]:
    if len(lines) <= max_lines:
        return lines
    out = lines[:max_lines]
    if out:
        out[-1] = out[-1].rstrip(" .") + "…"
    return out


def dominant_risk(risks: dict) -> str:
    cash = clamp01((risks or {}).get("cash"), 0.5) or 0.5
    margini = clamp01((risks or {}).get("margini"), 0.5) or 0.5
    acq = clamp01((risks or {}).get("acq"), 0.5) or 0.5

    top = max(
        [
            ("CASSA", cash),
            ("MARGINI", margini),
            ("ACQUISIZIONE", acq),
        ],
        key=lambda x: x[1],
    )[0]
    return top