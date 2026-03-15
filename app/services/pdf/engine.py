# filepath: app/services/pdf/engine.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from reportlab.pdfgen import canvas
from .config import PAGE_SIZE
from .pages import render_scan_pages, render_one_pager
from .utils import clamp01

from ..report_insights import report_header_payload
from .narrative import (
    confidence_score,
    drivers_payload,
    hero_insight,
    plan_tasks_payload,
)

# =============================
# COSTANTI VISIVE
# =============================

COLOR_MAP = {
    "VERDE": {"hex": "#27ae60", "rgb": (39, 174, 96)},
    "GIALLO": {"hex": "#f0a500", "rgb": (240, 165, 0)},
    "ROSSO": {"hex": "#c5221f", "rgb": (197, 34, 31)},
    "GOLD": {"hex": "#D4AF37", "rgb": (212, 175, 55)},
    "DARK": {"hex": "#1a1a2e", "rgb": (26, 26, 46)},
}

# =============================
# LOGICA DI BUSINESS: EFFETTO WOW
# =============================

class HairSalonConsultant:
    """Trasforma i dati grezzi in intuizioni da coach di alto livello."""
    
    @staticmethod
    def get_magic_number(kpi: Dict) -> Dict:
        incasso = kpi.get("incassi_totali_mese", 0)
        # Obiettivo: +10% margine tramite micro-azioni quotidiane
        target_extra = (incasso * 0.10) / 24 # 24 giorni lavorativi medi
        
        return {
            "valore": round(target_extra, 2),
            "azione": "Vendi 2 shampoo o 1 trattamento gloss extra ogni giorno.",
            "impatto": f"Questo copre circa {round(incasso * 0.10)}€ di costi fissi/bollette."
        }

    @staticmethod
    def analyze_staff(kpi: Dict) -> Dict:
        ore = kpi.get("ore_lavorate_mese", 0)
        incasso = kpi.get("incassi_totali_mese", 0)
        stipendi = kpi.get("costo_stipendi_mese", 0)
        
        resa_h = incasso / ore if ore > 0 else 0
        costo_h = stipendi / ore if ore > 0 else 0
        
        return {
            "resa": round(resa_h, 2),
            "costo": round(costo_h, 2),
            "status": "ROSSO" if resa_h < (costo_h * 1.5) else "VERDE"
        }

    @staticmethod
    def seasonal_advice(mese_rif: str) -> str:
        try:
            m = int(mese_rif.split('-')[1])
        except:
            m = datetime.now().month
            
        if m in [9, 10]: return "🍁 Azione: Kit Ricostruzione post-estate a ogni cliente."
        if m == 11: return "🎄 Azione: Gift Card ora per evitare il vuoto di Gennaio."
        if m in [3, 4]: return "🌸 Azione: Promo Balayage per il cambio look stagionale."
        return "⚙️ Azione: Ottimizza i tempi di posa per liberare una poltrona extra."

# =============================
# NORMALIZZAZIONE BENCHMARK
# =============================

def _get_salon_benchmarks(kpi: Dict[str, Any]) -> Dict[str, Any]:
    """
    Se mancano i benchmark di sistema, generiamo target ideali per un Salone di Bellezza.
    """
    margine_val = kpi.get("margine_pct", 0.35)
    conv_val = kpi.get("conversione", 0.50)
    runway_val = kpi.get("runway_mesi", 2.0)
    be_val = kpi.get("break_even_ratio", 0.9)

    return {
        "margine": {
            "value": margine_val, 
            "target": 0.45, # Il target di un salone sano è 45%
            "status": "VERDE" if margine_val >= 0.45 else "GIALLO" if margine_val >= 0.30 else "ROSSO"
        },
        "conversione": {
            "value": conv_val, 
            "target": 0.70, # Su 10 ingressi, 7 devono comprare
            "status": "VERDE" if conv_val >= 0.70 else "GIALLO" if conv_val >= 0.50 else "ROSSO"
        },
        "runway": {
            "value": runway_val, 
            "target": 6.0, # 6 mesi di cassa per stare sereni
            "status": "VERDE" if runway_val >= 6 else "GIALLO" if runway_val >= 3 else "ROSSO"
        },
        "break_even": {
            "value": be_val, 
            "target": 1.2, # Fatturare 20% in più del punto di pareggio
            "status": "VERDE" if be_val >= 1.2 else "GIALLO" if be_val >= 1.0 else "ROSSO"
        }
    }

# =============================
# COSTRUZIONE CONTESTO (CTX)
# =============================

def _build_ctx(scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Dict[str, Any]:
    kpi = vm.get("kpi", {})
    risks = vm.get("risks", {})
    mese = scan_meta.get("mese_riferimento", "2024-01")
    
    consultant = HairSalonConsultant()
    
    # Calcolo rischi
    cash_r = clamp01(risks.get("cash", 0.5))
    marg_r = clamp01(risks.get("margini", 0.5))
    acq_r = clamp01(risks.get("acq", 0.5))
    
    # Status generale
    max_risk = max(cash_r, marg_r, acq_r)
    overall = "ROSSO" if max_risk >= 0.66 else "GIALLO" if max_risk >= 0.33 else "VERDE"

    # Preparazione Benchmarks (Il pezzo mancante!)
    benchmarks_data = vm.get("benchmark_results")
    if not benchmarks_data:
        benchmarks_data = _get_salon_benchmarks(kpi)

    return {
        "settore": scan_meta.get("settore"),
        "modello": scan_meta.get("modello"),
        "mese": mese,
        "overall": overall,
        "overall_color": COLOR_MAP[overall]["rgb"],
        
        # Insight Wow
        "magic_number": consultant.get_magic_number(kpi),
        "staff_data": consultant.analyze_staff(kpi),
        "seasonal_tip": consultant.seasonal_advice(mese),
        "tecnico_perc": kpi.get("percentuale_servizi_tecnici", 0),
        
        # Dati Standard
        "triad": round((1 - max_risk) * 100, 1),
        "cash_r": cash_r,
        "marg_r": marg_r,
        "acq_r": acq_r,
        "confidence": confidence_score(vm),
        "summary": hero_insight(vm),
        "drivers": drivers_payload(vm),
        "plan": plan_tasks_payload(vm),
        "benchmarks": benchmarks_data, # ECCOLO! Ripristinato.
        "header_payload": report_header_payload(vm, {}),
    }

# =============================
# FUNZIONI DI GENERAZIONE (CON ALIAS)
# =============================

def generate_report(out_path: str | Path, scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ctx = _build_ctx(scan_meta, vm)
    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)
    render_scan_pages(c, ctx)
    c.save()
    return out_path

def generate_one_pager(out_path: str | Path, scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ctx = _build_ctx(scan_meta, vm)
    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)
    render_one_pager(c, ctx)
    c.save()
    return out_path

# --- ALIAS PER COMPATIBILITÀ ---
def generate_scan_pdf(out_path: str | Path, scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Path:
    return generate_report(out_path, scan_meta, vm)

def generate_scan_pdf_enterprise(out_path: str | Path, scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Path:
    return generate_report(out_path, scan_meta, vm)