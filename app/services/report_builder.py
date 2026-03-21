from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.models.benchmark import SectorBenchmark
from app.services.scoring_engine import business_stability_score

# --- IMPORTAZIONI DEI NUOVI MOTORI AVANZATI ---
try:
    from app.services.ai_service import generate_ai_memo
except ImportError:
    def generate_ai_memo(*args, **kwargs): return ""

try:
    from app.services.analysis.financial import calculate_financial_projections
except ImportError:
    def calculate_financial_projections(*args, **kwargs): return {}

try:
    from app.services.analysis.strategy_orchestrator import run_advanced_diagnostics
except ImportError:
    def run_advanced_diagnostics(*args, **kwargs): return {}

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
    quiz_responses: Optional[Dict[str, Any]] = None

def build_report(inp: Inputs, bench: Optional[SectorBenchmark] = None) -> Dict[str, Any]:
    # 1. CALCOLO KPI DI BASE
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

    # 2. TARGET BENCHMARK
    b_margin_good = (bench.margine_lordo_target / 100) if bench and getattr(bench, 'margine_lordo_target', None) is not None else 0.55
    b_margin_bad = b_margin_good * 0.5 

    b_conv_good = (bench.conversione_target / 100) if bench and getattr(bench, 'conversione_target', None) is not None and bench.conversione_target > 0 else 0.12
    b_conv_bad = b_conv_good * 0.4

    b_be_good = bench.break_even_sano if bench and getattr(bench, 'break_even_sano', None) is not None else 1.2
    b_be_bad = 0.95

    b_runway_good = bench.runway_minima if bench and getattr(bench, 'runway_minima', None) is not None else 9
    b_runway_bad = 2

    # 3. PREPARAZIONE KPI_DICT
    kpi_dict = {
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
    }

    # 4. BUSINESS STABILITY SCORE E RESILIENZA
    stability = business_stability_score(kpi_dict)
    stability_score = stability.get("score", 50)
    stability_status = stability.get("status", "Unknown")

    if stability_status == "Critical":
        executive_summary = "Struttura esposta a rischio elevato. Priorità su liquidità e stabilizzazione."
    elif stability_status == "Risk":
        executive_summary = "Basi presenti ma non consolidate. Priorità: rafforzare disciplina operativa."
    elif stability_status == "Attention":
        executive_summary = "Struttura discreta ma con aree operative da migliorare."
    else:
        executive_summary = "Business solido. Priorità: consolidare il modello e scalare."

    # 5. POSIZIONAMENTO COMPETITIVO (Competitor Analysis)
    competitors_analysis = []
    if margine_pct is not None:
        if margine_pct >= b_margin_good:
            competitors_analysis.append({"title": "Marginalità Leader", "icon": "🏆", "text": "Ottimo lavoro! Trattieni più valore su ogni vendita rispetto alla media.", "color": "#10b981"})
        elif margine_pct >= b_margin_bad:
            competitors_analysis.append({"title": "Marginalità in Media", "icon": "⚖️", "text": "I tuoi margini sono in linea con i concorrenti.", "color": "#f59e0b"})
        else:
            competitors_analysis.append({"title": "Svantaggio sui Margini", "icon": "⚠️", "text": "Stai sostenendo costi troppo alti rispetto al mercato.", "color": "#ef4444"})

    if runway_mesi is not None:
        if runway_mesi >= b_runway_good:
            competitors_analysis.append({"title": "Cassa Superiore", "icon": "🛡️", "text": "Riserva di liquidità maggiore degli standard.", "color": "#10b981"})
        else:
            competitors_analysis.append({"title": "Rischio Liquidità", "icon": "🚨", "text": "Autonomia finanziaria inferiore alla concorrenza.", "color": "#ef4444"})

    # 6. ESECUZIONE DEI MOTORI AVANZATI
    
    # A. OpenAI Strategic Memo
    ai_memo = generate_ai_memo(
        state={"overall": stability_status, "overall_score": stability_score, "summary": executive_summary},
        kpi=kpi_dict,
        meta={"settore": inp.settore}
    )

    # B. Motore Finanziario (Stress Test, Simulatori, EBITDA Gap)
    fin_projections = calculate_financial_projections(kpi_dict, b_margin_good)

    # C. Motore McKinsey (MECE, OHI, Value Chain, 3 Horizons)
    advanced_strategy = run_advanced_diagnostics(
        kpi_data=kpi_dict,
        quiz_responses=inp.quiz_responses or {},
        benchmarks={"margine": b_margin_good, "conversione": b_conv_good, "runway": b_runway_good, "break_even": b_be_good},
        business_score_data=stability
    )

    # 7. COSTRUZIONE DEL PAYLOAD FINALE (Triade)
    return {
        "triade": {
            "meta": {
                "settore": inp.settore, "modello": inp.modello,
                "mese_riferimento": inp.mese_riferimento, "created_at": utc_now_iso()
            },
            "state": {
                "overall": stability_status,
                "overall_score": stability_score,
                "summary": executive_summary,
                "business_stability": stability,
                "competitive_positioning": competitors_analysis,
                "ai_memo": ai_memo,  # Memo OpenAI
            },
            "kpi": kpi_dict,
            "financial_projections": fin_projections,  # Stress Test & What-If
            "advanced_strategy": advanced_strategy,    # Frameworks McKinsey
            "action_plan": ["Monitorare il cashflow settimanalmente", "Difendere la marginalità", "Standardizzare l'acquisizione"]
        },
        "benchmark_results": {}
    }
