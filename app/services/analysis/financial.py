from typing import Dict, Any

def calculate_financial_projections(kpi: Dict[str, Any], bench_margin: float) -> Dict[str, Any]:
    cash = float(kpi.get("cassa_attuale") or 0)
    revenue = float(kpi.get("incassi_mese") or 0)
    burn = float(kpi.get("burn_mensile") or 0)
    margin = float(kpi.get("margine_pct") or 0)
    
    # Stima uscite mensili totali
    if burn > 0:
        uscite = revenue + burn
    else:
        costi_fissi = float(kpi.get("costi_fissi_mese") or 0)
        uscite = costi_fissi + (revenue * (1 - margin))
        
    if uscite <= 0: uscite = 1
    
    # 1. Stress Test
    stress_test = {
        "shock_20": round(cash / max((uscite - revenue * 0.8), 1), 1),
        "shock_30": round(cash / max((uscite - revenue * 0.7), 1), 1),
        "late_payments": round(cash / max((uscite - revenue * 0.5), 1), 1)
    }
    
    # 2. What-If Simulator
    def sim(cost_cut=0.0, rev_up=0.0):
        new_uscite = uscite * (1 - cost_cut)
        new_rev = revenue * (1 + rev_up)
        new_burn = new_uscite - new_rev
        if new_burn <= 0: return "Safe"
        return round(cash / new_burn, 1)

    simulator = {
        "cost_cut_10": sim(cost_cut=0.10),
        "cost_cut_20": sim(cost_cut=0.20),
        "rev_up_10": sim(rev_up=0.10),
        "rev_up_20": sim(rev_up=0.20),
    }
    
    # 3. EBITDA Gap (Soldi lasciati sul tavolo annualizzati)
    ebitda_gap = 0
    if margin < bench_margin and revenue > 0:
        ebitda_gap = round((revenue * 12) * (bench_margin - margin), 0)
        
    return {
        "uscite_mensili": round(uscite, 0),
        "stress_test": stress_test,
        "simulator": simulator,
        "ebitda_gap": ebitda_gap
    }
