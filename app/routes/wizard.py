import json
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict

from flask import Blueprint, render_template, redirect, url_for, session, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..forms import OnboardingForm, EssentialDataForm, QuizForm
from ..models.scan import Scan
from ..tenant import ensure_current_org_id

bp = Blueprint("wizard", __name__, url_prefix="/wizard")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ================================
# INPUT STRUCT
# ================================
class Inputs:
    def __init__(
        self,
        settore: str,
        modello: str,
        mese_riferimento: str,
        quiz_risk: List[float],
        cassa_attuale: Optional[float] = None,
        burn_mensile: Optional[float] = None,
        incassi_mese: Optional[float] = None,
        costi_fissi_mese: Optional[float] = None,
        margine_lordo_pct: Optional[float] = None,
        leads_mese: Optional[float] = None,
        clienti_mese: Optional[float] = None,
    ):
        self.settore = settore
        self.modello = modello
        self.mese_riferimento = mese_riferimento
        self.quiz_risk = quiz_risk
        self.cassa_attuale = cassa_attuale
        self.burn_mensile = burn_mensile
        self.incassi_mese = incassi_mese
        self.costi_fissi_mese = costi_fissi_mese
        self.margine_lordo_pct = margine_lordo_pct
        self.leads_mese = leads_mese
        self.clienti_mese = clienti_mese


# ================================
# ENGINE
# ================================
def build_report(inp: Inputs) -> dict:
    """
    Motore B (cash-centric) + report per UI/PDF.
    - risks: 0..1 (0=OK, 1=critico)
    - overall_score: 0..100 (più alto = più rischio)
    - confidence: 0..100 (KPI reali presenti)
    - indicators: 6 KPI normalizzati (score01 + value_str + label)
    """

    # ----------------------------
    # KPI raw
    # ----------------------------
    runway_mesi = None
    if (inp.cassa_attuale is not None) and (inp.burn_mensile is not None) and inp.burn_mensile > 0:
        runway_mesi = inp.cassa_attuale / inp.burn_mensile

    margine_pct = None
    if inp.margine_lordo_pct is not None:
        margine_pct = inp.margine_lordo_pct / 100.0  # 0..1

    conversione = None
    if (inp.leads_mese is not None) and (inp.clienti_mese is not None) and inp.leads_mese > 0:
        conversione = inp.clienti_mese / inp.leads_mese  # 0..1

    break_even_ratio = None
    if (inp.incassi_mese is not None) and (inp.costi_fissi_mese is not None) and (margine_pct is not None) and margine_pct > 0:
        be_ricavi = inp.costi_fissi_mese / margine_pct
        if be_ricavi and be_ricavi > 0:
            break_even_ratio = inp.incassi_mese / be_ricavi

    # burn/cash ratio (mesi “inversi”): burn / cassa -> più è alto peggio è
    burn_cash_ratio = None
    if (inp.burn_mensile is not None) and (inp.cassa_attuale is not None) and inp.cassa_attuale > 0:
        burn_cash_ratio = inp.burn_mensile / inp.cassa_attuale

    # ----------------------------
    # Helpers
    # ----------------------------
    def clamp01(x: Optional[float]) -> Optional[float]:
        if x is None:
            return None
        try:
            v = float(x)
        except Exception:
            return None
        return max(0.0, min(1.0, v))

    def label_from_score01(s: float) -> str:
        # s: rischio 0..1
        if s >= 0.66:
            return "ROSSO"
        if s >= 0.33:
            return "GIALLO"
        return "VERDE"

    # normalize value -> risk 0..1 with thresholds
    # higher_is_better=True means risk increases when value decreases under thresholds
    def norm(value: Optional[float], good: float, bad: float, higher_is_better: bool = True) -> Optional[float]:
        if value is None:
            return None
        v = float(value)

        if higher_is_better:
            # v >= good => 0 risk ; v <= bad => 1 risk
            if v >= good:
                return 0.0
            if v <= bad:
                return 1.0
            return (good - v) / (good - bad)
        else:
            # v <= good => 0 risk ; v >= bad => 1 risk
            if v <= good:
                return 0.0
            if v >= bad:
                return 1.0
            return (v - good) / (bad - good)

    def fmt_eur(x: Any) -> str:
        if x is None:
            return "—"
        try:
            v = float(x)
            return f"{v:,.0f} €".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "—"

    def fmt_pct01(x: Any) -> str:
        if x is None:
            return "—"
        try:
            return f"{float(x) * 100:.2f}%"
        except Exception:
            return "—"

    def fmt_num(x: Any, suffix: str = "") -> str:
        if x is None:
            return "—"
        try:
            return f"{float(x):.2f}{suffix}"
        except Exception:
            return "—"

    # ----------------------------
    # Triade risks (macro) = KPI + quiz anti-autoinganno
    # ----------------------------
    r_runway = norm(runway_mesi, good=6, bad=2, higher_is_better=True)
    r_margine = norm(margine_pct, good=0.55, bad=0.25, higher_is_better=True)
    r_conv = norm(conversione, good=0.10, bad=0.03, higher_is_better=True)
    r_be = norm(break_even_ratio, good=1.15, bad=0.90, higher_is_better=True)

    quiz = [float(x) for x in (inp.quiz_risk or [])] or [0.6] * 10
    quiz_avg = sum(quiz) / len(quiz)

    def combine(primary: Optional[float]) -> float:
        # KPI prevale, quiz “sporca” al 60% per evitare falsi verdi
        if primary is None:
            return float(quiz_avg)
        return max(float(primary), float(quiz_avg) * 0.6)

    risk_cash = clamp01(combine(r_runway)) or 0.6
    marg_mix = None
    if (r_margine is not None) and (r_be is not None):
        marg_mix = (r_margine + r_be) / 2.0
    else:
        marg_mix = r_margine if r_margine is not None else r_be
    risk_margini = clamp01(combine(marg_mix)) or 0.6
    risk_acq = clamp01(combine(r_conv)) or 0.6

    # Score cash-centric (più alto = più rischio)
    w_cash, w_marg, w_acq = 0.40, 0.35, 0.25
    overall = (risk_cash * w_cash) + (risk_margini * w_marg) + (risk_acq * w_acq)
    overall_score = round(overall * 100.0, 2)

    # Confidence: quante KPI macro sono presenti
    kpi_count = sum(x is not None for x in [runway_mesi, margine_pct, conversione, break_even_ratio])
    confidence = round((kpi_count / 4.0) * 100.0, 0)

    def conf_label(v: float) -> str:
        if v >= 75:
            return "ALTA"
        if v >= 40:
            return "MEDIA"
        return "BASSA"

    overall_label = label_from_score01(overall)

    decisions = {
        "cash": "Ridurre incertezza sugli incassi e stimare runway in modo realistico.",
        "margini": "Proteggere margine lordo e verificare copertura costi fissi (break-even).",
        "acq": "Migliorare conversione e ridurre tempi di rientro (payback) prima di scalare.",
    }

    # ----------------------------
    # 6 INDICATORI (KPI normalizzati) — OPZIONE (2)
    # score01 sempre = rischio 0..1
    # ----------------------------
    # soglie “manageriali” (tuning facile)
    s_runway = norm(runway_mesi, good=6, bad=3, higher_is_better=True)            # <3 rosso
    s_dso = None  # non lo hai in input: lo lasciamo come mancante
    s_conv = norm(conversione, good=0.10, bad=0.05, higher_is_better=True)        # <5% rosso
    s_margin = norm(margine_pct, good=0.40, bad=0.30, higher_is_better=True)      # <30% rosso
    s_be = norm(break_even_ratio, good=1.15, bad=1.00, higher_is_better=True)     # <1.0 rosso
    s_bcr = norm(burn_cash_ratio, good=0.12, bad=0.25, higher_is_better=False)    # più alto peggio (burn/cash)

    indicators: List[Dict[str, Any]] = [
        {
            "key": "runway",
            "title": "Runway",
            "desc": "Autonomia in mesi (più è alto, meglio).",
            "score01": clamp01(s_runway),
            "label": label_from_score01(clamp01(s_runway) or 0.5),
            "value_str": fmt_num(runway_mesi, " mesi") if runway_mesi is not None else "—",
        },
        {
            "key": "dso",
            "title": "DSO",
            "desc": "Giorni medi di incasso (più basso, meglio).",
            "score01": None,
            "label": "GIALLO",
            "value_str": "—",
        },
        {
            "key": "conversione",
            "title": "Conversione",
            "desc": "Lead → clienti (più alto, meglio).",
            "score01": clamp01(s_conv),
            "label": label_from_score01(clamp01(s_conv) or 0.5),
            "value_str": fmt_pct01(conversione),
        },
        {
            "key": "margine",
            "title": "Margine lordo",
            "desc": "Margine lordo % (più alto, meglio).",
            "score01": clamp01(s_margin),
            "label": label_from_score01(clamp01(s_margin) or 0.5),
            "value_str": fmt_pct01(margine_pct),
        },
        {
            "key": "break_even",
            "title": "Break-even ratio",
            "desc": "Incassi / ricavi di pareggio (più alto, meglio).",
            "score01": clamp01(s_be),
            "label": label_from_score01(clamp01(s_be) or 0.5),
            "value_str": fmt_num(break_even_ratio),
        },
        {
            "key": "burn_cash",
            "title": "Burn/Cash",
            "desc": "Burn mensile / cassa (più basso, meglio).",
            "score01": clamp01(s_bcr),
            "label": label_from_score01(clamp01(s_bcr) or 0.5),
            "value_str": (fmt_pct01(burn_cash_ratio) if burn_cash_ratio is not None else "—"),
        },
    ]

    # ----------------------------
    # Alerts (coerenti con KPI)
    # ----------------------------
    alerts = []

    if runway_mesi is None:
        alerts.append({"level": "GIALLO", "text": "Runway non disponibile: inserisci cassa attuale e burn mensile per stimare i mesi di autonomia."})
    else:
        if runway_mesi < 2:
            alerts.append({"level": "ROSSO", "text": f"Runway stimata {runway_mesi:.1f} mesi: rischio liquidità alto. Riduci uscite e accelera incassi."})
        elif runway_mesi < 4:
            alerts.append({"level": "GIALLO", "text": f"Runway stimata {runway_mesi:.1f} mesi: margine di sicurezza limitato. Cashflow settimanale consigliato."})

    if conversione is not None:
        if conversione < 0.05:
            alerts.append({"level": "ROSSO", "text": f"Conversione bassa ({conversione*100:.2f}%): rivedi offerta, target e follow-up."})
        elif conversione < 0.10:
            alerts.append({"level": "GIALLO", "text": f"Conversione media ({conversione*100:.2f}%): ottimizza messaggi, pipeline e prossimi step."})

    if margine_pct is not None:
        if margine_pct < 0.30:
            alerts.append({"level": "ROSSO", "text": f"Margine lordo basso ({margine_pct*100:.2f}%): rischio erosione. Rivedi prezzi/costi."})
        elif margine_pct < 0.40:
            alerts.append({"level": "GIALLO", "text": f"Margine lordo da stabilizzare ({margine_pct*100:.2f}%): monitora sconti e costi."})

    if break_even_ratio is not None:
        if break_even_ratio < 1.00:
            alerts.append({"level": "ROSSO", "text": f"Sotto break-even (ratio {break_even_ratio:.2f}): ricavi non coprono costi fissi."})
        elif break_even_ratio < 1.10:
            alerts.append({"level": "GIALLO", "text": f"Vicino al break-even (ratio {break_even_ratio:.2f}): piccole variazioni possono creare deficit."})

    # ----------------------------
    # Action plan (in base ai rischi macro)
    # ----------------------------
    def bucket(r: float) -> str:
        if r >= 0.66:
            return "ROSSO"
        if r >= 0.33:
            return "GIALLO"
        return "VERDE"

    ap: List[str] = []

    # CASH
    c = bucket(risk_cash)
    if c == "ROSSO":
        ap += [
            "Imposta un cashflow settimanale (entrate/uscite previste) e aggiorna ogni 7 giorni.",
            "Taglia subito le uscite non essenziali e definisci una soglia minima di cassa da non superare.",
            "Standardizza i solleciti pagamenti: scadenziario + promemoria + escalation (DSO sotto controllo).",
        ]
    elif c == "GIALLO":
        ap += [
            "Pianifica il cashflow 4 settimane avanti (entrate/uscite previste) e verifica ogni settimana gli scostamenti.",
            "Riduci i ritardi di incasso: regole su scadenze, acconti e solleciti con tempi chiari.",
        ]
    else:
        ap += ["Mantieni il cashflow sotto controllo con una revisione rapida settimanale (15 minuti)."]

    # MARGINI
    m = bucket(risk_margini)
    if m == "ROSSO":
        ap += [
            "Blocca sconti non autorizzati: definisci regole minime di prezzo e margine.",
            "Rivedi i costi fissi: elimina voci non critiche e negozia fornitori/servizi.",
            "Calcola il break-even: ricavi minimi mensili per coprire costi fissi con il tuo margine lordo.",
        ]
    elif m == "GIALLO":
        ap += [
            "Rivedi mensilmente margini per cliente/prodotto: isola ciò che rende davvero.",
            "Verifica copertura costi fissi: se sei vicino al pareggio, agisci su prezzi, mix o costi.",
        ]
    else:
        ap += ["Proteggi i margini: monitora costi e prezzi ogni mese, evitando erosioni invisibili."]

    # ACQUISIZIONE
    a = bucket(risk_acq)
    if a == "ROSSO":
        ap += [
            "Definisci un funnel semplice (lead → call → proposta → chiusura) e misura conversione e tempi.",
            "Imposta follow-up obbligatorio: ogni lead deve avere un ‘next step’ con data e responsabilità.",
            "Rendi l’offerta più chiara e ripetibile: meno eccezioni, più pacchetti standard e comparabili.",
        ]
    elif a == "GIALLO":
        ap += [
            "Ottimizza conversione lavorando su messaggi, proposta e tempi di risposta.",
            "Riduci dispersione: pipeline corta, next step sempre, follow-up standard.",
        ]
    else:
        ap += ["Mantieni il funnel in ordine: misurazione mensile di lead, conversione e valore medio."]

    return {
        "triade": {
            "meta": {
                "settore": inp.settore,
                "modello": inp.modello,
                "mese_riferimento": inp.mese_riferimento,
                "created_at": utc_now_iso(),
            },
            "state": {
                "overall": overall_label,
                "overall_score": overall_score,
                "confidence": confidence,
                "confidenza": conf_label(confidence),
            },
            "risks": {
                "cash": round(risk_cash, 4),
                "margini": round(risk_margini, 4),
                "acq": round(risk_acq, 4),
            },
            "kpi": {
                "cassa_attuale": inp.cassa_attuale,
                "burn_mensile": inp.burn_mensile,
                "incassi_mese": inp.incassi_mese,
                "costi_fissi_mese": inp.costi_fissi_mese,
                "runway_mesi": runway_mesi,
                "margine_pct": margine_pct,
                "conversione": conversione,
                "break_even_ratio": break_even_ratio,
                "burn_cash_ratio": burn_cash_ratio,
            },
            "quiz": {"norm": [float(x) for x in quiz]},
            "indicators": indicators,
            "decisions": decisions,
            "action_plan": ap[:9],
            "alerts": alerts[:8],
        }
    }


# ================================
# ROUTES (onboarding → data → quiz)
# ================================
@bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    ensure_current_org_id()

    form = OnboardingForm()
    if form.validate_on_submit():
        session["onboarding"] = {
            "settore": form.settore.data,
            "modello": form.modello.data,
            "mese_riferimento": form.mese_riferimento.data,
        }
        session.pop("data", None)
        return redirect(url_for("wizard.data"))

    return render_template("wizard_onboarding.html", form=form)


@bp.route("/data", methods=["GET", "POST"])
@login_required
def data():
    ensure_current_org_id()

    if "onboarding" not in session:
        return redirect(url_for("wizard.onboarding"))

    form = EssentialDataForm()
    if form.validate_on_submit():
        session["data"] = form.data
        return redirect(url_for("wizard.quiz"))

    return render_template("wizard_data.html", form=form)


@bp.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    org_id = ensure_current_org_id()

    if "onboarding" not in session:
        return redirect(url_for("wizard.onboarding"))

    form = QuizForm()
    if form.validate_on_submit():
        raw = [int(getattr(form, f"q{i}").data) for i in range(1, 11)]
        quiz_risk = [1.0 - ((v - 1.0) / 4.0) for v in raw]

        ob = session["onboarding"]
        data = session.get("data", {}) or {}

        inp = Inputs(
            settore=ob["settore"],
            modello=ob["modello"],
            mese_riferimento=ob["mese_riferimento"],
            quiz_risk=quiz_risk,
            cassa_attuale=data.get("cassa_attuale"),
            burn_mensile=data.get("burn_mensile"),
            incassi_mese=data.get("incassi_mese"),
            costi_fissi_mese=data.get("costi_fissi_mese"),
            margine_lordo_pct=data.get("margine_lordo_pct"),
            leads_mese=data.get("leads_mese"),
            clienti_mese=data.get("clienti_mese"),
        )

        report = build_report(inp)

        s = Scan(
            org_id=org_id,
            user_id=current_user.id,
            settore=ob["settore"],
            modello=ob["modello"],
            mese_riferimento=ob["mese_riferimento"],
            report_json=json.dumps(report, ensure_ascii=False),
            created_at=datetime.utcnow(),
        )

        db.session.add(s)
        db.session.commit()

        flash("Scan generato.")
        return redirect(url_for("scans.view_scan", scan_id=s.id))

    return render_template("quiz.html", form=form)