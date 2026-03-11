from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.models.benchmark import SectorBenchmark
from app.services.scoring_engine import business_stability_score

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

@dataclass
class Inputs:
    settore: str
    modello: str
    mese_riferimento: str
    quiz_risk: List[float]

    dimensione: Optional[str] = None
    dipendenti: Optional[int] = None
    area_geografica: Optional[str] = None
    fatturato: Optional[str] = None
    tipologia_clienti: Optional[str] = None
    cassa_attuale: Optional[float] = None
    burn_mensile: Optional[float] = None
    incassi_mese: Optional[float] = None
    costi_fissi_mese: Optional[float] = None
    margine_lordo_pct: Optional[float] = None
    leads_mese: Optional[float] = None
    clienti_mese: Optional[float] = None

def build_report(inp: Inputs, bench: Optional[SectorBenchmark] = None) -> Dict[str, Any]:
    runway_mesi = None
    if inp.cassa_attuale is not None and inp.burn_mensile is not None and inp.burn_mensile > 0:
        runway_mesi = inp.cassa_attuale / inp.burn_mensile

    margine_pct = None
    if inp.margine_lordo_pct is not None:
        margine_pct = inp.margine_lordo_pct / 100

    conversione = None
    if inp.leads_mese is not None and inp.clienti_mese is not None and inp.leads_mese > 0:
        conversione = inp.clienti_mese / inp.leads_mese

    break_even_ratio = None
    if inp.incassi_mese is not None and inp.costi_fissi_mese is not None and margine_pct is not None and margine_pct > 0:
        if inp.costi_fissi_mese > 0:
            be_ricavi = inp.costi_fissi_mese / margine_pct
            break_even_ratio = inp.incassi_mese / be_ricavi
        else:
            break_even_ratio = 999.0

    burn_cash_ratio = None
    if inp.burn_mensile is not None and inp.cassa_attuale is not None and inp.cassa_attuale > 0:
        burn_cash_ratio = inp.burn_mensile / inp.cassa_attuale

    b_margin_good = (bench.margine_lordo_target / 100) if bench and getattr(bench, 'margine_lordo_target', None) is not None else 0.55
    b_margin_bad = b_margin_good * 0.5 

    b_conv_good = (bench.conversione_target / 100) if bench and getattr(bench, 'conversione_target', None) is not None and bench.conversione_target > 0 else 0.12
    b_conv_bad = b_conv_good * 0.4

    b_be_good = bench.break_even_sano if bench and getattr(bench, 'break_even_sano', None) is not None else 1.2
    b_be_bad = 0.95

    b_runway_good = bench.runway_minima if bench and getattr(bench, 'runway_minima', None) is not None else 9
    b_runway_bad = 2

    def norm(value, good, bad, higher=True):
        if value is None:
            return None

        v = float(value)

        # protect against division by zero
        if good == bad:
            return 0

        if higher:
            if v >= good:
                return 0
            if v <= bad:
                return 1
            return (good - v) / (good - bad)
        else:
            if v <= good:
                return 0
            if v >= bad:
                return 1
            return (v - good) / (bad - good)

    r_runway = norm(runway_mesi, b_runway_good, b_runway_bad, True)
    r_margin = norm(margine_pct, b_margin_good, b_margin_bad, True)
    r_conv = norm(conversione, b_conv_good, b_conv_bad, True)
    r_be = norm(break_even_ratio, b_be_good, b_be_bad, True)
    r_burn = norm(burn_cash_ratio, 0.12, 0.25, False)

    quiz = inp.quiz_risk or [0.6] * 10
    quiz = [max(0, min(1, float(q))) for q in quiz]
    quiz_avg = sum(quiz) / len(quiz)

    def combine(primary):
        if primary is None:
            return quiz_avg
        return primary * 0.65 + quiz_avg * 0.35

    risk_cash = combine(r_runway)
    if r_burn is not None:
        risk_cash = max(risk_cash, r_burn * 0.8)

    marg_mix = None
    if r_margin is not None and r_be is not None:
        marg_mix = (r_margin * 0.6) + (r_be * 0.4)
    else:
        marg_mix = r_margin if r_margin is not None else (r_be if r_be is not None else quiz_avg)

    risk_margini = combine(marg_mix)
    risk_acq = combine(r_conv)

    # =========================
    # CRITICAL KPI IDENTIFICATION
    # Identify top 3 areas with highest risk
    # =========================
    critical_candidates = [
        ("Cassa / Runway", risk_cash),
        ("Margini / Break-even", risk_margini),
        ("Acquisizione Clienti", risk_acq),
    ]

    critical_kpis = [
        {"area": name, "risk": round(value * 100, 1)}
        for name, value in sorted(
            critical_candidates,
            key=lambda x: (x[1] if x[1] is not None else 0),
            reverse=True
        )
    ][:3]

    base_risk = (risk_cash * 0.45 + risk_margini * 0.30 + risk_acq * 0.25)
    
    penalty = 0
    if runway_mesi is not None and runway_mesi < b_runway_bad:
        penalty += 0.12
    if break_even_ratio is not None and break_even_ratio < b_be_bad:
        penalty += 0.08
    if margine_pct is not None and margine_pct < b_margin_bad:
        penalty += 0.06
    if conversione is not None and b_conv_bad > 0 and conversione < b_conv_bad:
        penalty += 0.05

    overall_risk = min(1, base_risk + penalty)
    triad_index = round((1 - overall_risk) * 100, 2)

    # =========================
    # BUSINESS RESILIENCE INDEX
    # Combines liquidity, margins, sustainability and acquisition strength
    # =========================
    resilience_components = []

    if runway_mesi is not None:
        resilience_components.append(min(runway_mesi / b_runway_good, 1))

    if margine_pct is not None:
        resilience_components.append(min(margine_pct / b_margin_good, 1))

    if break_even_ratio is not None:
        resilience_components.append(min(break_even_ratio / b_be_good, 1))

    if conversione is not None and b_conv_good > 0:
        resilience_components.append(min(conversione / b_conv_good, 1))

    if resilience_components:
        resilience_index = round((sum(resilience_components) / len(resilience_components)) * 100, 2)
    else:
        resilience_index = None

    # qualitative interpretation of resilience
    if resilience_index is None:
        resilience_label = "Resilienza non calcolabile"
    elif resilience_index >= 75:
        resilience_label = "Resilienza elevata"
    elif resilience_index >= 50:
        resilience_label = "Resilienza moderata"
    else:
        resilience_label = "Resilienza fragile"

    if triad_index >= 70:
        maturity_label = "Maturità: Avanzata"
    elif triad_index >= 45:
        maturity_label = "Maturità: Intermedia"
    else:
        maturity_label = "Maturità: Fragile"

    kpi_count = sum([
        runway_mesi is not None,
        margine_pct is not None,
        conversione is not None,
        break_even_ratio is not None,
    ])
    confidence = round((kpi_count / 4) * 100) if kpi_count > 0 else 50

    kpi_dict = {
        "runway_mesi": runway_mesi,
        "margine_pct": margine_pct,
        "conversione": conversione,
        "break_even_ratio": break_even_ratio,
    }

    stability = business_stability_score(kpi_dict)
    stability_score = stability.get("score")
    stability_status = stability.get("status")

    # Summary aligned with the new Business Stability Score
    if stability_status == "Critical":
        executive_summary = "Struttura esposta a rischio elevato. Priorità su liquidità e stabilizzazione."
    elif stability_status == "Risk":
        executive_summary = "Basi presenti ma non consolidate. Priorità: rafforzare disciplina operativa."
    elif stability_status == "Attention":
        executive_summary = "Struttura discreta ma con aree operative da migliorare."
    else:
        executive_summary = "Business solido. Priorità: consolidare il modello e scalare."

    action_plan = [
        "Monitorare il cashflow settimanalmente", "Definire KPI chiari per vendite e conversioni",
        "Standardizzare il funnel commerciale", "Proteggere margini e politiche di prezzo", "Ridurre dispersione operativa",
        "Ottimizzare tempi di incasso", "Monitorare break-even mensile", "Strutturare pipeline vendite", "Rafforzare controllo finanziario"
    ]

    # =========================
    # POSIZIONAMENTO COMPETITIVO (Data Analysis & Strategy)
    # =========================
    competitors_analysis = []
    
    # Valutazione Margini
    if margine_pct is not None:
        if margine_pct >= b_margin_good:
            competitors_analysis.append({"title": "Marginalità Leader", "icon": "🏆", "text": "Ottimo lavoro! Trattieni più valore su ogni vendita rispetto alla media del settore. Hai un forte vantaggio sui prezzi.", "color": "#10b981"})
        elif margine_pct >= b_margin_bad:
            competitors_analysis.append({"title": "Marginalità in Media", "icon": "⚖️", "text": "I tuoi margini sono perfettamente in linea con le aziende concorrenti. C'è spazio per ottimizzare i costi diretti.", "color": "#f59e0b"})
        else:
            competitors_analysis.append({"title": "Svantaggio sui Margini", "icon": "⚠️", "text": "Attenzione: stai sostenendo costi troppo alti. I tuoi concorrenti stanno guadagnando di più a parità di fatturato.", "color": "#ef4444"})

    # Valutazione Cassa (Runway)
    if runway_mesi is not None:
        if runway_mesi >= b_runway_good:
            competitors_analysis.append({"title": "Cassa Superiore", "icon": "🛡️", "text": "Hai una riserva di liquidità maggiore rispetto agli standard di settore. Sei al sicuro dagli imprevisti di mercato.", "color": "#10b981"})
        elif runway_mesi >= b_runway_bad:
            competitors_analysis.append({"title": "Autonomia Standard", "icon": "🟡", "text": "La tua cassa è sufficiente per operare, ma inferiore alle aziende leader del tuo mercato.", "color": "#f59e0b"})
        else:
            competitors_analysis.append({"title": "Rischio Finanziario", "icon": "🚨", "text": "La tua autonomia finanziaria è pericolosamente inferiore alla concorrenza. Rischio elevato di crisi di liquidità.", "color": "#ef4444"})

    # Valutazione Commerciale (Conversione)
    if conversione is not None and b_conv_good > 0:
        if conversione >= b_conv_good:
            competitors_analysis.append({"title": "Vendite Performanti", "icon": "🎯", "text": "Il tuo motore commerciale è più efficiente della media: trasformi i contatti in clienti paganti con molta facilità.", "color": "#10b981"})
        else:
            competitors_analysis.append({"title": "Lentezza Commerciale", "icon": "📉", "text": "Il mercato chiude contratti più velocemente di te. Stai disperdendo troppe opportunità di vendita.", "color": "#ef4444"})

    if not competitors_analysis:
        competitors_analysis.append({"title": "Dati Insufficienti", "icon": "🔍", "text": "Inserisci i dati economici nel Wizard per scoprire come ti posizioni rispetto ai tuoi diretti concorrenti.", "color": "#64748b"})

    decisions = {
        "cash": (
            "Rafforzare il controllo di cassa, aumentare la visibilità sugli incassi attesi e proteggere la runway."
            if risk_cash >= 0.55
            else "La liquidità è sotto controllo: mantenere presidio settimanale su cassa, incassi e uscite prioritarie."
        ),
        "margini": (
            "Rivedere pricing, sconti, costi diretti e mix offerta per difendere la marginalità."
            if risk_margini >= 0.55
            else "La marginalità è relativamente difesa: consolidare pricing e disciplina economica."
        ),
        "acq": (
            "Standardizzare pipeline, criteri di qualifica e follow-up per rendere l'acquisizione più prevedibile."
            if risk_acq >= 0.55
            else "Il motore commerciale mostra basi discrete: lavorare su continuità e replicabilità della conversione."
        ),
    }

    # =========================
    # BENCHMARK GAP ANALYSIS
    # Always compute benchmarks using sector targets or fallback defaults
    # =========================

    def bench_status(value, target):
        if value is None:
            return None
        if value > target:
            return "above"
        if value < target:
            return "below"
        return "equal"

    benchmark_results = {
        "runway": {
            "value": runway_mesi,
            "target": b_runway_good,
            "gap": (runway_mesi - b_runway_good) if runway_mesi is not None else None,
            "status": bench_status(runway_mesi, b_runway_good),
        },
        "margine": {
            "value": margine_pct,
            "target": b_margin_good,
            "gap": (margine_pct - b_margin_good) if margine_pct is not None else None,
            "status": bench_status(margine_pct, b_margin_good),
        },
        "conversione": {
            "value": conversione,
            "target": b_conv_good,
            "gap": (conversione - b_conv_good) if conversione is not None else None,
            "status": bench_status(conversione, b_conv_good),
        },
        "break_even": {
            "value": break_even_ratio,
            "target": b_be_good,
            "gap": (break_even_ratio - b_be_good) if break_even_ratio is not None else None,
            "status": bench_status(break_even_ratio, b_be_good),
        },
    }

    return {
        "triade": {
            "meta": {
                "settore": inp.settore, "modello": inp.modello,
                "mese_riferimento": inp.mese_riferimento, "created_at": utc_now_iso(),
                "dimensione": inp.dimensione, "dipendenti": inp.dipendenti, "area_geografica": inp.area_geografica,
                "fatturato": inp.fatturato, "tipologia_clienti": inp.tipologia_clienti,
                "benchmark_settore": {
                    "settore_riferimento": bench.sector_name if bench else "Media Standard",
                    "margine_target": b_margin_good,
                    "conversione_target": b_conv_good,
                    "runway_target": b_runway_good,
                    "be_target": b_be_good,
                }
            },
            "state": {
                "overall": stability_status,
                "overall_score": stability_score,
                "confidence": confidence,
                "summary": executive_summary,
                "business_stability": stability,
                "maturity_score": triad_index,
                "maturity_label": maturity_label,
                "resilience_index": resilience_index,
                "resilience_label": resilience_label,
                "critical_kpis": critical_kpis,
                "competitive_positioning": competitors_analysis,
            },
            "risks": {
                "cash": round(risk_cash, 4),
                "margini": round(risk_margini, 4),
                "acq": round(risk_acq, 4),
            },
            "kpi": {
                "runway_mesi": runway_mesi, 
                "margine_pct": margine_pct, 
                "conversione": conversione, 
                "break_even_ratio": break_even_ratio, 
                "burn_cash_ratio": burn_cash_ratio,
                "incassi_mese": inp.incassi_mese,
                "costi_fissi_mese": inp.costi_fissi_mese,
                "cassa_attuale": inp.cassa_attuale,
                "burn_mensile": inp.burn_mensile,
                "leads_mese": inp.leads_mese,
                "clienti_mese": inp.clienti_mese
            },
            "decisions": decisions,
            "action_plan": action_plan
        },
        "benchmark_results": benchmark_results
    }
