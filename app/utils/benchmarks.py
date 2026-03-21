"""
SaaS Full – Dynamic Benchmark Utility
Recupera i benchmark dal database e valuta le performance dei KPI.
"""
import logging
from typing import Dict, Any, Optional
from app.models.benchmark import SectorBenchmark

logger = logging.getLogger(__name__)

# =========================================================
# UTILITIES DI NORMALIZZAZIONE
# =========================================================

def _extract_float(value: Any) -> float:
    """Estrae un numero in modo sicuro da stringhe sporche (es: '31.2 mesi' -> 31.2)"""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        cleaned = "".join(c for c in str(value) if c.isdigit() or c in ".-")
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0


# =========================================================
# KPI EVALUATION ENGINE
# =========================================================

def evaluate_kpi(value: float, target: float, higher_is_better: bool = True) -> str:
    """Valutazione standard a semaforo per un KPI rispetto al suo target."""
    if target == 0:
        return "GRIGIO"

    if higher_is_better:
        if value >= target: return "VERDE"
        if value >= target * 0.75: return "GIALLO"
        return "ROSSO"
    else:
        # Per metriche dove "meno è meglio" (es. Churn rate)
        if value <= target: return "VERDE"
        if value <= target * 1.25: return "GIALLO"
        return "ROSSO"

def evaluate_break_even(value: float) -> str:
    """Valutazione specifica per il break-even ratio aziendale."""
    if value >= 2.0: return "VERDE"
    if value >= 1.0: return "GIALLO"
    return "ROSSO"


# =========================================================
# CORE BENCHMARK ENGINE
# =========================================================

def get_benchmark_analysis(settore: str, kpi_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recupera i dati di settore dal Database e calcola i gap (distanza dal target).
    """
    if not settore:
        return {"status": "error", "message": "Settore non specificato"}

    settore_norm = settore.strip()

    # Mappa di sinonimi per intercettare varianti
    sector_map = {
        "saas": "SaaS / Tech", "tech": "SaaS / Tech", "software": "SaaS / Tech",
        "ristorazione": "Ho.Re.Ca.", "hotel": "Ho.Re.Ca.", "bar": "Ho.Re.Ca.",
        "medico": "Sanità / Studi medici", "studio medico": "Sanità / Studi medici",
    }
    
    # Normalizzazione settore
    for key, mapped in sector_map.items():
        if key in settore_norm.lower():
            settore_norm = mapped
            break

    # 1. Recupero dal Database (Dinamico)
    bench_db = SectorBenchmark.query.filter(SectorBenchmark.sector_name.ilike(f"%{settore_norm}%")).first()

    if bench_db:
        sector_name = bench_db.sector_name
        benchmark = {
            "margine_pct": (bench_db.margine_lordo_target or 55.0) / 100.0,
            "conversione": (bench_db.conversione_target or 10.0) / 100.0,
            "break_even_ratio": bench_db.break_even_sano or 1.2,
            "runway_mesi": bench_db.runway_minima or 6
        }
    else:
        # 2. Fallback Standard se il settore non è ancora mappato nel DB dall'Admin
        logger.warning(f"Nessun benchmark in DB per il settore '{settore_norm}'. Uso Media Standard.")
        sector_name = "Media Standard"
        benchmark = {
            "margine_pct": 0.40,
            "conversione": 0.08,
            "break_even_ratio": 1.15,
            "runway_mesi": 6
        }

    # 3. Calcolo GAP
    runway = _extract_float(kpi_data.get("runway_mesi"))
    margine = _extract_float(kpi_data.get("margine_pct"))
    conversione = _extract_float(kpi_data.get("conversione"))
    break_even = _extract_float(kpi_data.get("break_even_ratio"))

    results = {
        "runway": {
            "value": runway,
            "target": benchmark["runway_mesi"],
            "status": evaluate_kpi(runway, benchmark["runway_mesi"], True),
            "gap": runway - benchmark["runway_mesi"]
        },
        "margine": {
            "value": margine,
            "target": benchmark["margine_pct"],
            "status": evaluate_kpi(margine, benchmark["margine_pct"], True),
            "gap": margine - benchmark["margine_pct"]
        },
        "conversione": {
            "value": conversione,
            "target": benchmark["conversione"],
            "status": evaluate_kpi(conversione, benchmark["conversione"], True),
            "gap": conversione - benchmark["conversione"]
        },
        "break_even": {
            "value": break_even,
            "target": benchmark["break_even_ratio"],
            "status": evaluate_break_even(break_even),
            "gap": break_even - benchmark["break_even_ratio"]
        }
    }

    return {
        "status": "success",
        "sector_name": sector_name,
        "benchmark": benchmark,
        "results": results
    }