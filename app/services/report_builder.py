from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
# Importiamo il modello per la tipizzazione
from app.models.benchmark import SectorBenchmark

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

@dataclass
class Inputs:
    settore: str
    modello: str
    mese_riferimento: str
    quiz_risk: List[float]

    cassa_attuale: Optional[float] = None
    burn_mensile: Optional[float] = None

    incassi_mese: Optional[float] = None
    costi_fissi_mese: Optional[float] = None

    margine_lordo_pct: Optional[float] = None

    leads_mese: Optional[float] = None
    clienti_mese: Optional[float] = None


def build_report(inp: Inputs, bench: Optional[SectorBenchmark] = None) -> Dict[str, Any]:
    """
    Costruisce il report integrando i benchmark di settore se disponibili.
    Se 'bench' è None, ricade su valori medi standard.
    """

    # =========================
    # KPI CALCOLATI
    # =========================
    runway_mesi = None
    if inp.cassa_attuale and inp.burn_mensile and inp.burn_mensile > 0:
        runway_mesi = inp.cassa_attuale / inp.burn_mensile

    margine_pct = None
    if inp.margine_lordo_pct is not None:
        margine_pct = inp.margine_lordo_pct / 100

    conversione = None
    if inp.leads_mese and inp.clienti_mese and inp.leads_mese > 0:
        conversione = inp.clienti_mese / inp.leads_mese

    break_even_ratio = None
    if inp.incassi_mese and inp.costi_fissi_mese and margine_pct and margine_pct > 0:
        be_ricavi = inp.costi_fissi_mese / margine_pct
        break_even_ratio = inp.incassi_mese / be_ricavi

    burn_cash_ratio = None
    if inp.burn_mensile and inp.cassa_attuale and inp.cassa_attuale > 0:
        burn_cash_ratio = inp.burn_mensile / inp.cassa_attuale

    # =========================
    # DEFINIZIONE SOGLIE (BENCHMARK)
    # =========================
    # Se abbiamo il bench dal DB, usiamo i suoi valori, altrimenti fallback su medie standard
    b_margin_good = (bench.margine_lordo_target / 100) if bench else 0.55
    b_margin_bad = b_margin_good * 0.5  # Diventa critico se è sotto la metà del target di settore

    b_conv_good = (bench.conversione_target / 100) if (bench and bench.conversione_target > 0) else 0.12
    b_conv_bad = b_conv_good * 0.4

    b_be_good = bench.break_even_sano if bench else 1.2
    b_be_bad = 0.95

    b_runway_good = bench.runway_minima if bench else 9
    b_runway_bad = 2

    # =========================
    # NORMALIZZAZIONE KPI
    # =========================
    def norm(value, good, bad, higher=True):
        if value is None:
            return None
        v = float(value)
        if higher:
            if v >= good: return 0
            if v <= bad: return 1
            return (good - v) / (good - bad)
        else:
            if v <= good: return 0
            if v >= bad: return 1
            return (v - good) / (bad - good)

    r_runway = norm(runway_mesi, b_runway_good, b_runway_bad, True)
    r_margin = norm(margine_pct, b_margin_good, b_margin_bad, True)
    r_conv = norm(conversione, b_conv_good, b_conv_bad, True)
    r_be = norm(break_even_ratio, b_be_good, b_be_bad, True)
    r_burn = norm(burn_cash_ratio, 0.12, 0.25, False)

    # =========================
    # QUIZ
    # =========================
    quiz = inp.quiz_risk or [0.6] * 10
    quiz = [max(0, min(1, float(q))) for q in quiz]
    quiz_avg = sum(quiz) / len(quiz)

    def combine(primary):
        if primary is None:
            return quiz_avg
        return primary * 0.65 + quiz_avg * 0.35

    # =========================
    # RISCHI PER AREA
    # =========================
    risk_cash = combine(r_runway)
    if r_burn:
        risk_cash = max(risk_cash, r_burn * 0.8)

    if r_margin is not None and r_be is not None:
        marg_mix = (r_margin * 0.6) + (r_be * 0.4)
    else:
        marg_mix = r_margin or r_be or quiz_avg

    risk_margini = combine(marg_mix)
    risk_acq = combine(r_conv)

    # =========================
    # TRIAD INDEX & PENALTY
    # =========================
    base_risk = (risk_cash * 0.45 + risk_margini * 0.30 + risk_acq * 0.25)
    
    penalty = 0
    if runway_mesi and runway_mesi < b_runway_bad: penalty += 0.12
    if break_even_ratio and break_even_ratio < b_be_bad: penalty += 0.08
    if margine_pct and margine_pct < b_margin_bad: penalty += 0.06
    if conversione and b_conv_bad > 0 and conversione < b_conv_bad: penalty += 0.05

    overall_risk = min(1, base_risk + penalty)
    triad_index = round((1 - overall_risk) * 100, 2)

    # =========================
    # COLORI E MATURITY
    # =========================
    if triad_index >= 70:
        overall = "VERDE"
        maturity_label = "Maturità: Avanzata"
    elif triad_index >= 45:
        overall = "GIALLO"
        maturity_label = "Maturità: Intermedia"
    else:
        overall = "ROSSO"
        maturity_label = "Maturità: Fragile"

    maturity_score = triad_index

    # =========================
    # CONFIDENCE
    # =========================
    kpi_count = sum([
        runway_mesi is not None,
        margine_pct is not None,
        conversione is not None,
        break_even_ratio is not None
    ])
    confidence = round((kpi_count / 4) * 100)

    # =========================
    # EXECUTIVE SUMMARY
    # =========================
    if overall == "ROSSO":
        executive_summary = (
            "Il Business Scan evidenzia una struttura esposta a rischio elevato. "
            "Le priorità devono concentrarsi su liquidità, sostenibilità economica "
            "e stabilizzazione del motore commerciale."
        )
    elif overall == "GIALLO":
        executive_summary = (
            "Il quadro mostra basi presenti ma ancora non pienamente consolidate. "
            "La priorità è rafforzare prevedibilità e disciplina operativa."
        )
    else:
        executive_summary = (
            "Il business appare ordinato e relativamente solido. "
            "La priorità ora è consolidare il modello e aumentare scalabilità."
        )

    # =========================
    # ACTION PLAN
    # =========================
    action_plan = [
        "Monitorare il cashflow settimanalmente",
        "Definire KPI chiari per vendite e conversioni",
        "Standardizzare il funnel commerciale",
        "Proteggere margini e politiche di prezzo",
        "Ridurre dispersione operativa",
        "Ottimizzare tempi di incasso",
        "Monitorare break-even mensile",
        "Strutturare pipeline vendite",
        "Rafforzare controllo finanziario"
    ]

    # =========================
    # OUTPUT JSON
    # =========================
    return {
        "triade": {
            "meta": {
                "settore": inp.settore,
                "modello": inp.modello,
                "mese_riferimento": inp.mese_riferimento,
                "created_at": utc_now_iso(),
                # Dati del benchmark usati per il confronto nel frontend
                "benchmark_settore": {
                    "settore_riferimento": bench.sector_name if bench else "Media Standard",
                    "margine_target": b_margin_good,
                    "conversione_target": b_conv_good,
                    "runway_target": b_runway_good,
                    "be_target": b_be_good
                }
            },
            "state": {
                "overall": overall,
                "overall_score": triad_index,
                "confidence": confidence,
                "summary": executive_summary,
                "maturity_score": maturity_score,
                "maturity_label": maturity_label
            },
            "risks": {
                "cash": round(risk_cash, 4),
                "margini": round(risk_margini, 4),
                "acq": round(risk_acq, 4)
            },
            "kpi": {
                "runway_mesi": runway_mesi,
                "margine_pct": margine_pct,
                "conversione": conversione,
                "break_even_ratio": break_even_ratio,
                "burn_cash_ratio": burn_cash_ratio
            },
            "action_plan": action_plan
        }
    }