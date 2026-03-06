import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# -----------------------------
# Formatting helpers
# -----------------------------
def _euro(x):
    try:
        if x is None:
            return "—"
        v = float(x)
        return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def _pct100(x):
    try:
        if x is None:
            return "—"
        return f"{float(x) * 100:.2f}%"
    except Exception:
        return "—"


def _fmt_dt(x):
    if isinstance(x, datetime):
        return x.strftime("%Y-%m-%d %H:%M")
    if not x:
        return "—"
    return str(x).replace("T", " ").replace("Z", "")


def _overall_style(overall: str):
    o = (overall or "").upper()
    if o == "ROSSO":
        return colors.HexColor("#D64545"), colors.white
    if o == "GIALLO":
        return colors.HexColor("#F2C94C"), colors.black
    return colors.HexColor("#27AE60"), colors.white


def _status_color(score01: float):
    # score01: 0..1 (0=ok, 1=critico)
    if score01 >= 0.67:
        return "ROSSO", colors.HexColor("#D64545")
    if score01 >= 0.34:
        return "GIALLO", colors.HexColor("#F2C94C")
    return "VERDE", colors.HexColor("#27AE60")


# -----------------------------
# PDF UI primitives
# -----------------------------
def _pill(c: canvas.Canvas, x, y, w, h, fill, text, text_color=colors.white, r=8):
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, r, stroke=0, fill=1)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 10, y + (h - 10) / 2, text)


def _card(c: canvas.Canvas, x, y, w, h, title, value, subtitle):
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#E6E8EC"))
    c.roundRect(x, y, w, h, 10, stroke=1, fill=1)

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 12, y + h - 16, title)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(x + 12, y + h - 40, value)

    c.setFillColor(colors.HexColor("#6B7280"))
    c.setFont("Helvetica", 9)
    c.drawString(x + 12, y + 12, subtitle)


def _section_title(c: canvas.Canvas, x, y, text):
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, text)


def _row(c: canvas.Canvas, x, y, label, value, colw=70 * mm):
    c.setFillColor(colors.HexColor("#374151"))
    c.setFont("Helvetica", 9)
    c.drawString(x, y, label)

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(x + colw, y, value)


def _risk_bar(c: canvas.Canvas, x, y, w, h, score01: float):
    # Background
    c.setFillColor(colors.HexColor("#EEF2F7"))
    c.roundRect(x, y, w, h, 6, stroke=0, fill=1)

    # Fill
    s = 0.0 if score01 is None else float(score01)
    if s < 0:
        s = 0.0
    if s > 1:
        s = 1.0

    _, col = _status_color(s)
    fill_w = w * s

    c.setFillColor(col)
    c.roundRect(x, y, max(2, fill_w), h, 6, stroke=0, fill=1)

    # Outline
    c.setStrokeColor(colors.HexColor("#D1D5DB"))
    c.roundRect(x, y, w, h, 6, stroke=1, fill=0)


def _wrap_lines(text: str, max_chars: int):
    if not text:
        return []
    words = str(text).split()
    lines, cur = [], []
    n = 0
    for w in words:
        if n + len(w) + (1 if cur else 0) > max_chars:
            lines.append(" ".join(cur))
            cur = [w]
            n = len(w)
        else:
            cur.append(w)
            n += len(w) + (1 if cur else 0)
    if cur:
        lines.append(" ".join(cur))
    return lines


# -----------------------------
# Alerts (automatic)
# -----------------------------
def build_alerts(triade: dict):
    alerts = []

    state = triade.get("state", {}) or {}
    kcash = triade.get("kpi_cash", {}) or {}
    km = triade.get("kpi_margini", {}) or {}
    kacq = triade.get("kpi_acq", {}) or {}

    runway = kcash.get("runway_mesi")
    if runway is None:
        alerts.append(("GIALLO", "Runway non disponibile: inserisci cassa attuale e burn mensile per stimare i mesi di autonomia."))
    else:
        try:
            r = float(runway)
            if r < 1:
                alerts.append(("ROSSO", "Runway < 1 mese: priorità assoluta su incassi, taglio uscite e piano cassa settimanale."))
            elif r < 3:
                alerts.append(("ROSSO", "Runway < 3 mesi: rischio liquidità elevato. Serve piano cassa + accelerazione incassi."))
            elif r < 6:
                alerts.append(("GIALLO", "Runway tra 3 e 6 mesi: ok ma va monitorata ogni settimana."))
        except Exception:
            pass

    dso = kcash.get("dso_giorni")
    if dso is None:
        alerts.append(("GIALLO", "DSO non disponibile: inserisci tempi medi di incasso per capire il rischio crediti."))
    else:
        try:
            d = int(dso)
            if d > 90:
                alerts.append(("ROSSO", "DSO > 90 giorni: incassi troppo lenti. Attiva solleciti e regole di pagamento (acconto/scadenze)."))
            elif d > 60:
                alerts.append(("GIALLO", "DSO > 60 giorni: possibile tensione di cassa. Migliora processo di incasso."))
        except Exception:
            pass

    mlp = km.get("margine_lordo_pct")
    if mlp is None:
        alerts.append(("GIALLO", "Margine % non disponibile: inserisci ricavi e costi variabili per stimare il margine lordo."))
    else:
        try:
            m = float(mlp)
            if m < 0.15:
                alerts.append(("ROSSO", "Margine lordo < 15%: rischio di lavorare senza coprire i costi fissi. Rivedi prezzi, sconti e mix offerta."))
            elif m < 0.30:
                alerts.append(("GIALLO", "Margine lordo < 30%: attenzione a sconti e costi variabili. Cerca efficienze e pricing migliore."))
        except Exception:
            pass

    conv = kacq.get("conversione")
    if conv is None:
        alerts.append(("GIALLO", "Conversione non disponibile: inserisci lead e clienti mese per misurare il funnel."))
    else:
        try:
            c = float(conv)
            if c < 0.05:
                alerts.append(("ROSSO", "Conversione < 5%: troppi lead non diventano clienti. Serve offerta più chiara + follow-up strutturato."))
            elif c < 0.10:
                alerts.append(("GIALLO", "Conversione < 10%: migliorabile. Lavora su qualifica lead e script di follow-up."))
        except Exception:
            pass

    payback = kacq.get("payback_cac_mesi")
    if payback is not None:
        try:
            p = float(payback)
            if p > 12:
                alerts.append(("ROSSO", "Payback CAC > 12 mesi: acquisizione troppo lenta a rientrare. Migliora margine o riduci CAC prima di scalare."))
            elif p > 6:
                alerts.append(("GIALLO", "Payback CAC > 6 mesi: ok, ma attenzione se la cassa è tesa."))
        except Exception:
            pass

    # Data quality/confidence
    conf = (state.get("confidenza") or "").upper()
    if conf == "BASSA":
        alerts.append(("GIALLO", "Confidenza bassa: mancano dati chiave. Completa i numeri per avere decisioni più affidabili."))

    # Keep order: red first, then yellow
    order = {"ROSSO": 0, "GIALLO": 1, "VERDE": 2}
    alerts.sort(key=lambda t: order.get(t[0], 9))
    return alerts[:10]


# -----------------------------
# Main PDF builder
# -----------------------------
def build_scan_pdf(out_path, scan, report_json_text: str):
    report = json.loads(report_json_text)
    triade = report.get("triade", {}) if isinstance(report, dict) else {}

    meta = triade.get("meta", {}) or {}
    state = triade.get("state", {}) or {}
    kcash = triade.get("kpi_cash", {}) or {}
    km = triade.get("kpi_margini", {}) or {}
    kacq = triade.get("kpi_acq", {}) or {}
    decisions = triade.get("decisions", {}) or {}
    action_plan = triade.get("action_plan", []) or []

    alerts = triade.get("alerts")
    if not isinstance(alerts, list):
        alerts = build_alerts(triade)

    settore = getattr(scan, "settore", meta.get("settore", "—"))
    modello = getattr(scan, "modello", meta.get("modello", "—"))
    mese = getattr(scan, "mese_riferimento", meta.get("mese_riferimento", "—"))
    created_str = _fmt_dt(getattr(scan, "created_at", None) or meta.get("created_at", "—"))

    overall = state.get("overall", "—")
    badge_fill, badge_txt = _overall_style(overall)

    # risk scores (0..1)
    risk_cash = state.get("risk_cash")
    risk_margini = state.get("risk_margini")
    risk_acq = state.get("risk_acq")
    overall_score = state.get("overall_score")

    # derived scores for indicators
    # if missing -> assume mid (0.5) and warn via alert already
    def _score_from_thresholds(value, good_max, warn_max):
        # return 0..1 score where lower is better
        if value is None:
            return 0.50
        try:
            v = float(value)
            if v <= good_max:
                return 0.20
            if v <= warn_max:
                return 0.55
            return 0.85
        except Exception:
            return 0.50

    runway = kcash.get("runway_mesi")
    # For runway, higher is better -> invert thresholds
    runway_score = 0.50
    if runway is not None:
        try:
            r = float(runway)
            if r >= 6:
                runway_score = 0.20
            elif r >= 3:
                runway_score = 0.55
            else:
                runway_score = 0.85
        except Exception:
            runway_score = 0.50

    dso = kcash.get("dso_giorni")
    dso_score = _score_from_thresholds(dso, good_max=45, warn_max=60)

    mlp = km.get("margine_lordo_pct")
    # higher is better -> invert
    margin_score = 0.50
    if mlp is not None:
        try:
            m = float(mlp)
            if m >= 0.40:
                margin_score = 0.20
            elif m >= 0.30:
                margin_score = 0.55
            else:
                margin_score = 0.85
        except Exception:
            margin_score = 0.50

    conv = kacq.get("conversione")
    # higher is better -> invert
    conv_score = 0.50
    if conv is not None:
        try:
            cv = float(conv)
            if cv >= 0.20:
                conv_score = 0.20
            elif cv >= 0.10:
                conv_score = 0.55
            else:
                conv_score = 0.85
        except Exception:
            conv_score = 0.50

    payback = kacq.get("payback_cac_mesi")
    payback_score = 0.50
    if payback is not None:
        try:
            p = float(payback)
            if p <= 6:
                payback_score = 0.20
            elif p <= 12:
                payback_score = 0.55
            else:
                payback_score = 0.85
        except Exception:
            payback_score = 0.50

    # -----------------------------
    # PAGE 1 (Executive)
    # -----------------------------
    c = canvas.Canvas(str(out_path), pagesize=A4)
    W, H = A4

    c.setFillColor(colors.HexColor("#0B1220"))
    c.rect(0, H - 45 * mm, W, 45 * mm, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(18 * mm, H - 20 * mm, "Programma Alessio – Scan Report")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#C7D2FE"))
    c.drawString(18 * mm, H - 28 * mm, f"Settore: {settore}  ·  Modello: {modello}  ·  Mese: {mese}")
    c.drawString(18 * mm, H - 34 * mm, f"Creato: {created_str}")

    _pill(c, W - 65 * mm, H - 31 * mm, 47 * mm, 12 * mm, badge_fill, f"STATO: {overall}", badge_txt)

    y_cards = H - 70 * mm
    x0 = 18 * mm
    gap = 6 * mm
    cw = (W - 2 * x0 - 2 * gap) / 3
    ch = 28 * mm

    _card(c, x0, y_cards, cw, ch, "Rischio Cassa", _pct100(risk_cash), "Liquidità: cashflow/DSO/runway")
    _card(c, x0 + cw + gap, y_cards, cw, ch, "Rischio Margini", _pct100(risk_margini), "Margine & controllo costi/sconti")
    _card(c, x0 + 2 * (cw + gap), y_cards, cw, ch, "Rischio Acquisizione", _pct100(risk_acq), "Funnel, conversione, follow-up")

    y_kpi = y_cards - 12 * mm
    _section_title(c, x0, y_kpi, "KPI principali")
    c.setStrokeColor(colors.HexColor("#E6E8EC"))
    c.line(x0, y_kpi - 3 * mm, W - x0, y_kpi - 3 * mm)

    y = y_kpi - 12 * mm
    colw = (W - 2 * x0 - 2 * gap) / 3

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x0, y, "Cassa")
    y1 = y - 8 * mm
    _row(c, x0, y1, "Cassa attuale", _euro(kcash.get("cassa_attuale")), colw)
    _row(c, x0, y1 - 6 * mm, "Burn mensile", _euro(kcash.get("burn_mensile")), colw)
    runway_str = f"{float(runway):.2f} mesi" if runway is not None else "—"
    _row(c, x0, y1 - 12 * mm, "Runway", runway_str, colw)
    dso_str = f"{int(dso)} giorni" if dso is not None else "—"
    _row(c, x0, y1 - 18 * mm, "DSO", dso_str, colw)

    xm = x0 + colw + gap
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xm, y, "Margini")
    y2 = y - 8 * mm
    _row(c, xm, y2, "Ricavi mese", _euro(km.get("ricavi_mese")), colw)
    _row(c, xm, y2 - 6 * mm, "Costi variabili", _euro(km.get("costi_variabili_mese")), colw)
    _row(c, xm, y2 - 12 * mm, "Margine lordo", _euro(km.get("margine_lordo")), colw)
    mlp_str = f"{float(mlp) * 100:.2f}%" if mlp is not None else "—"
    _row(c, xm, y2 - 18 * mm, "Margine %", mlp_str, colw)

    xb = x0 + 2 * (colw + gap)
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xb, y, "Acquisizione")
    y3 = y - 8 * mm
    _row(c, xb, y3, "Lead mese", str(kacq.get("lead_mese") or "—"), colw)
    _row(c, xb, y3 - 6 * mm, "Clienti mese", str(kacq.get("clienti_mese") or "—"), colw)
    conv_str = f"{float(conv) * 100:.2f}%" if conv is not None else "—"
    _row(c, xb, y3 - 12 * mm, "Conversione", conv_str, colw)
    _row(c, xb, y3 - 18 * mm, "CAC", _euro(kacq.get("cac")), colw)

    y_dec = y1 - 30 * mm
    _section_title(c, x0, y_dec, "Action plan (priorità)")
    c.setStrokeColor(colors.HexColor("#E6E8EC"))
    c.line(x0, y_dec - 3 * mm, W - x0, y_dec - 3 * mm)

    y_list = y_dec - 10 * mm
    c.setFont("Helvetica", 10)
    if not action_plan:
        c.setFillColor(colors.HexColor("#374151"))
        c.drawString(x0, y_list, "—")
    else:
        n = 1
        for a in action_plan[:6]:
            c.setFillColor(colors.HexColor("#111827"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x0, y_list, f"{n}.")
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.HexColor("#374151"))
            c.drawString(x0 + 8 * mm, y_list, str(a)[:145])
            y_list -= 7 * mm
            n += 1

    c.setFillColor(colors.HexColor("#9CA3AF"))
    c.setFont("Helvetica", 8)
    c.drawString(18 * mm, 12 * mm, "Generated by Programma Alessio SaaS")
    c.drawRightString(W - 18 * mm, 12 * mm, "Pagina 1/2")

    c.showPage()

    # -----------------------------
    # PAGE 2 (6 indicators + bars + alerts)
    # -----------------------------
    W, H = A4
    x0 = 18 * mm
    gap = 6 * mm

    # Header
    c.setFillColor(colors.HexColor("#111827"))
    c.rect(0, H - 22 * mm, W, 22 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x0, H - 14 * mm, "Indicatori & Alert (ultima pagina)")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#D1D5DB"))
    c.drawString(x0, H - 19 * mm, f"Scan #{getattr(scan,'id','—')}  ·  {settore}  ·  {mese}")

    # 6 indicators
    indicators = [
        ("Rischio Cassa (completo)", risk_cash if risk_cash is not None else 0.50, "Sintesi rischio cassa complessivo."),
        ("Rischio Margini (completo)", risk_margini if risk_margini is not None else 0.50, "Sintesi rischio margini complessivo."),
        ("Rischio Acquisizione (completo)", risk_acq if risk_acq is not None else 0.50, "Sintesi rischio acquisizione complessivo."),
        ("Autonomia (Runway)", runway_score, "Quanto sei coperto in mesi (più è alto, meglio è)."),
        ("Velocità incassi (DSO)", dso_score, "Quanto velocemente incassi (più basso è meglio)."),
        ("Efficienza acquisizione (Payback/CAC)", payback_score, "Quanto tempo serve per rientrare del costo cliente."),
    ]

    y = H - 34 * mm
    row_h = 17 * mm
    bar_w = 72 * mm
    bar_h = 6 * mm

    _section_title(c, x0, y + 5 * mm, "6 indicatori (percentuali + barre)")
    c.setStrokeColor(colors.HexColor("#E6E8EC"))
    c.line(x0, y + 2 * mm, W - x0, y + 2 * mm)
    y -= 8 * mm

    for name, score, desc in indicators:
        # container
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#E6E8EC"))
        c.roundRect(x0, y - row_h + 2 * mm, W - 2 * x0, row_h, 10, stroke=1, fill=1)

        status_txt, status_col = _status_color(float(score))
        pct_txt = f"{float(score) * 100:.2f}%"

        # left: label + desc
        c.setFillColor(colors.HexColor("#111827"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x0 + 10, y - 6 * mm, name)

        c.setFillColor(colors.HexColor("#6B7280"))
        c.setFont("Helvetica", 8.5)
        c.drawString(x0 + 10, y - 11 * mm, desc[:95])

        # middle: bar
        bx = W - x0 - bar_w - 55 * mm
        by = y - 12 * mm
        _risk_bar(c, bx, by, bar_w, bar_h, float(score))

        # right: badge + %
        bx2 = W - x0 - 48 * mm
        _pill(c, bx2, y - 13 * mm, 34 * mm, 10 * mm, status_col, status_txt, colors.white if status_txt != "GIALLO" else colors.black)
        c.setFillColor(colors.HexColor("#111827"))
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(W - x0 - 10, y - 6.5 * mm, pct_txt)

        y -= row_h + 4 * mm
        if y < 70 * mm:
            break

    # Alerts section
    y_alert = y - 4 * mm
    _section_title(c, x0, y_alert, "Alert automatici")
    c.setStrokeColor(colors.HexColor("#E6E8EC"))
    c.line(x0, y_alert - 3 * mm, W - x0, y_alert - 3 * mm)
    y_alert -= 10 * mm

    if not alerts:
        c.setFillColor(colors.HexColor("#374151"))
        c.setFont("Helvetica", 10)
        c.drawString(x0, y_alert, "Nessun alert rilevante.")
    else:
        for sev, msg in alerts[:8]:
            if y_alert < 20 * mm:
                break
            if sev == "ROSSO":
                col = colors.HexColor("#D64545")
            elif sev == "GIALLO":
                col = colors.HexColor("#F2C94C")
            else:
                col = colors.HexColor("#27AE60")

            # bullet
            c.setFillColor(col)
            c.circle(x0 + 2 * mm, y_alert + 2.2 * mm, 2.2 * mm, stroke=0, fill=1)

            # text (wrapped)
            c.setFillColor(colors.HexColor("#111827"))
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(x0 + 6 * mm, y_alert + 0.5 * mm, sev)

            c.setFillColor(colors.HexColor("#374151"))
            c.setFont("Helvetica", 9.5)
            lines = _wrap_lines(msg, 110)
            yy = y_alert
            for ln in lines[:3]:
                c.drawString(x0 + 18 * mm, yy + 0.5 * mm, ln)
                yy -= 5 * mm
            y_alert = yy - 3 * mm

    # Footer
    c.setFillColor(colors.HexColor("#9CA3AF"))
    c.setFont("Helvetica", 8)
    c.drawString(18 * mm, 12 * mm, "Generated by Programma Alessio SaaS")
    c.drawRightString(W - 18 * mm, 12 * mm, "Pagina 2/2")

    c.showPage()
    c.save()
