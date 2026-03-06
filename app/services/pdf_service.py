from pathlib import Path
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _badge_color(overall: str):
    o = (overall or "").strip().upper()
    if o == "VERDE":
        return colors.HexColor("#22c55e")
    if o == "GIALLO":
        return colors.HexColor("#f59e0b")
    return colors.HexColor("#ef4444")


def render_scan_pdf(out_path: Path, scan_id: int, report: Dict[str, Any], meta: Dict[str, Any]) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    triade = report.get("triade", {}) if isinstance(report, dict) else {}
    state = triade.get("state", {}) or {}
    overall = state.get("overall", "—")
    decisions = triade.get("decisions", {}) or {}
    action_plan = triade.get("action_plan", []) or []
    quiz = (triade.get("quiz", {}) or {}).get("norm", []) or []

    c = canvas.Canvas(str(out_path), pagesize=A4)
    w, h = A4

    # Header bar
    c.setFillColor(colors.HexColor("#0b1220"))
    c.rect(0, h-34*mm, w, 34*mm, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(16*mm, h-20*mm, "Saas_full — Triade Scan")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#b7c3e6"))
    c.drawString(16*mm, h-27*mm, f"Scan #{scan_id}  |  {meta.get('mese_riferimento','—')}  |  {meta.get('settore','—')}  |  {meta.get('modello','—')}")

    # Badge overall
    bc = _badge_color(str(overall))
    c.setFillColor(bc)
    c.roundRect(16*mm, h-48*mm, 55*mm, 10*mm, 4*mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(18*mm, h-41*mm, f"STATO: {str(overall).upper()}")

    # Meta card
    y = h-60*mm
    c.setFillColor(colors.HexColor("#111b33"))
    c.setStrokeColor(colors.HexColor("#243458"))
    c.roundRect(16*mm, y-26*mm, w-32*mm, 26*mm, 6*mm, stroke=1, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y-10*mm, f"Creato: {meta.get('created_at','—')}")
    c.drawString(20*mm, y-18*mm, f"Settore: {meta.get('settore','—')}   |   Modello: {meta.get('modello','—')}   |   Mese: {meta.get('mese_riferimento','—')}")

    # Decisions 3 columns
    y2 = y-42*mm
    box_w = (w-32*mm-8*mm) / 3
    titles = [("Cassa", decisions.get("cash","—")), ("Margini", decisions.get("margini","—")), ("Acquisizione", decisions.get("acq","—"))]
    for i,(t,txt) in enumerate(titles):
        x = 16*mm + i*(box_w+4*mm)
        c.setFillColor(colors.HexColor("#0f1b33"))
        c.setStrokeColor(colors.HexColor("#243458"))
        c.roundRect(x, y2-30*mm, box_w, 30*mm, 6*mm, stroke=1, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x+4*mm, y2-10*mm, t)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#d6def6"))
        _draw_wrapped(c, txt, x+4*mm, y2-16*mm, box_w-8*mm, 10, max_lines=4)

    # Action plan
    y3 = y2-44*mm
    c.setFillColor(colors.HexColor("#0f1b33"))
    c.setStrokeColor(colors.HexColor("#243458"))
    c.roundRect(16*mm, y3-52*mm, w-32*mm, 52*mm, 6*mm, stroke=1, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, y3-10*mm, "Action plan")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#d6def6"))
    yy = y3-18*mm
    if action_plan:
        for idx, a in enumerate(action_plan[:7], start=1):
            c.drawString(22*mm, yy, f"{idx}. {a}")
            yy -= 6*mm
            if yy < 20*mm:
                break
    else:
        c.drawString(22*mm, yy, "—")

    # Quiz mini-bar (last)
    y4 = 22*mm
    c.setFillColor(colors.HexColor("#b7c3e6"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(16*mm, y4+18*mm, "Rischio (quiz) — barra per domanda (alto→basso)")

    if quiz:
        bar_x = 16*mm
        bar_y = y4+10*mm
        bar_h = 4*mm
        gap = 1.5*mm
        n = min(len(quiz), 10)
        bar_w = (w-32*mm - gap*(n-1)) / n
        for i in range(n):
            v = float(quiz[i])
            # v in [0..1] (qui "risk norm": 1=alto rischio)
            col = colors.HexColor("#ef4444") if v > 0.66 else (colors.HexColor("#f59e0b") if v > 0.33 else colors.HexColor("#22c55e"))
            c.setFillColor(col)
            c.roundRect(bar_x + i*(bar_w+gap), bar_y, bar_w, bar_h, 1.2*mm, stroke=0, fill=1)

    c.showPage()
    c.save()


def _draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float, font_size: int, max_lines: int = 5):
    text = (text or "—").strip()
    c.setFont("Helvetica", font_size)
    words = text.split()
    line = ""
    lines = []
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, "Helvetica", font_size) <= width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)

    lines = lines[:max_lines]
    yy = y
    for ln in lines:
        c.drawString(x, yy, ln)
        yy -= (font_size + 2)
