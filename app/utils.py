from datetime import datetime

def euro(x):
    try:
        if x is None:
            return "—"
        return f"{float(x):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"

def pct(x):
    try:
        if x is None:
            return "—"
        return f"{float(x) * 100:.1f}%"
    except Exception:
        return "—"

def fmt_month(m):
    return str(m) if m else "—"

def fmt_dt(s):
    if not s:
        return "—"
    if isinstance(s, datetime):
        return s.strftime("%Y-%m-%d %H:%M:%S")
    return str(s).replace("T", " ").replace("Z", "")
