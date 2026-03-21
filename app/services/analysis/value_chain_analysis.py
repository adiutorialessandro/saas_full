"""
Business System / Value Chain Analysis
Analizza i 5 layer operativi per identificare dove si disperde il margine.
"""
from typing import Dict, Any

def analyze_value_chain(kpi: Dict[str, Any], benchmarks: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scompone l'azienda in 5 stadi sequenziali per individuare il collo di bottiglia principale.
    """
    # 1. Product & R&D (Margine potenziale intrinseco)
    margine = float(kpi.get("margine_lordo_pct") or 0.0)
    target_margine = float(benchmarks.get("margine", 0.55)) * 100
    if margine > 1: # Assicura la normalizzazione
        margine = margine
    else:
        margine = margine * 100
        
    product_score = 100 if margine >= target_margine else (margine / target_margine * 100)

    # 2. Marketing & Lead Gen
    leads = float(kpi.get("leads_mese") or 0.0)
    marketing_score = 100 if leads > 15 else (leads / 15 * 100) if leads > 0 else 30

    # 3. Sales & Conversion
    conv = float(kpi.get("conversione") or 0.0)
    target_conv = float(benchmarks.get("conversione", 0.10))
    sales_score = 100 if conv >= target_conv else (conv / target_conv * 100)

    # 4. Operations & Delivery (Costi di struttura / Efficienza)
    be = float(kpi.get("break_even_ratio") or 0.0)
    ops_score = 100 if be >= 1.5 else (be / 1.5 * 100)

    # 5. Customer Success / Retention
    retention_score = 75.0 # Valore di fallback (richiederebbe LTV e Churn Rate)

    # Compilazione catena
    chain = [
        {"stage": "Sviluppo Prodotto", "score": min(100, max(0, round(product_score))), "label": "Qualità del Margine"},
        {"stage": "Marketing", "score": min(100, max(0, round(marketing_score))), "label": "Generazione Contatti"},
        {"stage": "Vendite", "score": min(100, max(0, round(sales_score))), "label": "Tasso di Chiusura"},
        {"stage": "Operations", "score": min(100, max(0, round(ops_score))), "label": "Efficienza Struttura"},
        {"stage": "Service", "score": min(100, max(0, round(retention_score))), "label": "Fidelizzazione"}
    ]

    # Determinazione scientifica del collo di bottiglia
    bottleneck = min(chain, key=lambda x: x["score"])

    # Generazione Insight per il CEO
    insight = "La catena del valore aziendale è ben bilanciata e ottimizzata."
    if bottleneck["stage"] == "Sviluppo Prodotto":
        insight = "Disfunzione all'Origine: Il modello di business è debole alla radice. I costi diretti sono troppo alti o il prezzo è errato."
    elif bottleneck["stage"] == "Marketing":
        insight = "Deficit di Trazione: Manca carburante nel motore. L'azienda necessita di maggiore visibilità e traffico qualificato."
    elif bottleneck["stage"] == "Vendite":
        insight = "Frizione Commerciale: Si generano contatti, ma il processo di vendita non riesce a monetizzarli efficacemente."
    elif bottleneck["stage"] == "Operations":
        insight = "Inefficienza Strutturale: L'azienda genera vendite, ma i costi di gestione e burocrazia distruggono il profitto."

    return {
        "value_chain": chain,
        "bottleneck": bottleneck,
        "strategic_insight": insight
    }