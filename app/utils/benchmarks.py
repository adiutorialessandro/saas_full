"""
Benchmark definitions and KPI evaluation utilities
SaaS Full – Strategic Diagnostic Engine
"""

from typing import Dict, Any


# ---------------------------------------------------------
# BENCHMARK SETTORIALI
# ---------------------------------------------------------

BENCHMARKS = {

    "Consulenza B2B": {
        "margine_pct": 0.55,
        "conversione": 0.10,
        "break_even_ratio": 1.20,
        "runway_mesi": 6
    },

    "Retail": {
        "margine_pct": 0.30,
        "conversione": 0.04,
        "break_even_ratio": 1.10,
        "runway_mesi": 3
    },

    "Manifattura": {
        "margine_pct": 0.35,
        "conversione": 0.07,
        "break_even_ratio": 1.15,
        "runway_mesi": 4
    },

    "SaaS / Tech": {
        "margine_pct": 0.75,
        "conversione": 0.05,
        "break_even_ratio": 1.30,
        "runway_mesi": 12
    },

    "Ho.Re.Ca.": {
        "margine_pct": 0.25,
        "conversione": 0.15,
        "break_even_ratio": 1.10,
        "runway_mesi": 2
    },

    "Immobiliare": {
        "margine_pct": 0.40,
        "conversione": 0.08,
        "break_even_ratio": 1.20,
        "runway_mesi": 6
    },

    "Sanità / Studi medici": {
        "margine_pct": 0.50,
        "conversione": 0.20,
        "break_even_ratio": 1.20,
        "runway_mesi": 4
    }

}


# ---------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------

def _extract_float(value) -> float:
    """
    Estrae un numero da stringhe sporche
    es:
    "31.2 mesi" -> 31.2
    "44%" -> 44
    """

    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    try:

        cleaned = "".join(
            c for c in str(value)
            if c.isdigit() or c in ".-"
        )

        return float(cleaned) if cleaned else 0.0

    except Exception:
        return 0.0


# ---------------------------------------------------------
# KPI EVALUATION
# ---------------------------------------------------------

def evaluate_kpi(value: float, target: float) -> str:
    """
    Valutazione standard KPI
    """

    if target == 0:
        return "GRIGIO"

    if value >= target:
        return "VERDE"

    if value >= target * 0.75:
        return "GIALLO"

    return "ROSSO"


def evaluate_break_even(value: float) -> str:
    """
    Valutazione specifica break-even ratio
    """

    if value >= 2:
        return "VERDE"

    if value >= 1:
        return "GIALLO"

    return "ROSSO"


# ---------------------------------------------------------
# BENCHMARK ENGINE
# ---------------------------------------------------------

def get_benchmark_analysis(settore: str, kpi_data: Dict[str, Any]) -> Dict[str, Any]:

    if not settore:
        return {
            "status": "error",
            "message": "Settore non specificato"
        }

    settore_norm = settore.strip().lower()

    # normalizzazione nomi settore (evita mismatch tipo "saas", "tech", ecc.)
    SECTOR_MAP = {
        "saas": "SaaS / Tech",
        "tech": "SaaS / Tech",
        "software": "SaaS / Tech",
        "ristorazione": "Ho.Re.Ca.",
        "hotel": "Ho.Re.Ca.",
        "bar": "Ho.Re.Ca.",
        "medico": "Sanità / Studi medici",
        "studio medico": "Sanità / Studi medici",
    }

    # prova prima con la mappa sinonimi
    for key, mapped in SECTOR_MAP.items():
        if key in settore_norm:
            settore_norm = mapped.lower()
            break

    benchmark = None
    sector_name = None

    for k, v in BENCHMARKS.items():
        if k.lower() in settore_norm or settore_norm in k.lower():
            benchmark = v
            sector_name = k
            break

    if not benchmark:

        sector_name = "Media Standard"

        benchmark = {
            "margine_pct": 0.35,
            "conversione": 0.10,
            "break_even_ratio": 1.10,
            "runway_mesi": 4
        }

    results = {}

    # ---------------------------
    # RUNWAY
    # ---------------------------

    runway = _extract_float(kpi_data.get("runway_mesi"))
    target_runway = benchmark["runway_mesi"]

    results["runway"] = {
        "value": runway,
        "target": target_runway,
        "status": evaluate_kpi(runway, target_runway),
        "gap": runway - target_runway
    }

    # ---------------------------
    # MARGINE
    # ---------------------------

    margine = _extract_float(kpi_data.get("margine_pct"))
    target_margine = benchmark["margine_pct"]

    results["margine"] = {
        "value": margine,
        "target": target_margine,
        "status": evaluate_kpi(margine, target_margine),
        "gap": margine - target_margine
    }

    # ---------------------------
    # CONVERSIONE
    # ---------------------------

    conversione = _extract_float(kpi_data.get("conversione"))
    target_conversione = benchmark["conversione"]

    results["conversione"] = {
        "value": conversione,
        "target": target_conversione,
        "status": evaluate_kpi(conversione, target_conversione),
        "gap": conversione - target_conversione
    }

    # ---------------------------
    # BREAK EVEN
    # ---------------------------

    break_even = _extract_float(kpi_data.get("break_even_ratio"))

    results["break_even"] = {
        "value": break_even,
        "target": benchmark["break_even_ratio"],
        "status": evaluate_break_even(break_even),
        "gap": break_even - benchmark["break_even_ratio"]
    }

    return {
        "status": "success",
        "sector_name": sector_name,
        "benchmark": benchmark,
        "results": results
    }