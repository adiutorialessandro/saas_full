"""
MECE Root Cause Analysis Engine
Algoritmo basato sul framework "Mutually Exclusive, Collectively Exhaustive"
"""
from typing import Dict, Any

def analyze_mece_root_cause(kpi_data: Dict[str, Any], benchmarks: Dict[str, float]) -> Dict[str, Any]:
    """
    Naviga l'albero decisionale finanziario per isolare il collo di bottiglia critico.
    """
    # Estrazione sicura dei KPI
    cassa = float(kpi_data.get("cassa_attuale") or 0.0)
    burn = float(kpi_data.get("burn_mensile") or 0.0)
    incassi = float(kpi_data.get("incassi_mese") or 0.0)
    costi_fissi = float(kpi_data.get("costi_fissi_mese") or 0.0)
    
    # Normalizzazione percentuali (es. 40 -> 0.4)
    margine_raw = kpi_data.get("margine_lordo_pct")
    margine_pct = float(margine_raw) / 100 if margine_raw else 0.0
    conversione = float(kpi_data.get("conversione") or 0.0)

    # Benchmark Defaults
    target_margine = float(benchmarks.get("margine", 0.55))
    target_conv = float(benchmarks.get("conversione", 0.10))

    root_cause = "Non Identificabile"
    path = ["Redditività Aziendale"]
    action = "Monitorare la situazione operativa e finanziaria."

    # LIVELLO 1: Sopravvivenza Finanziaria
    if burn > 0 and (cassa / burn) < 6:
        path.append("Problema di Liquidità (Runway < 6 mesi)")
        
        # Break Even calculation
        be_ricavi = costi_fissi / margine_pct if margine_pct > 0 else float('inf')
        
        # LIVELLO 2: Entrate vs Uscite
        if incassi < be_ricavi:
            path.append("Problema di Entrate (Incassi < Break-Even)")
            
            # LIVELLO 3: Analisi Volumi vs Margini
            if margine_pct < target_margine:
                path.append("Problema di Prezzo/Costo Diretto (Margine sotto target)")
                root_cause = "Pricing Errato o Costi Variabili Troppo Alti"
                action = "Aumentare i prezzi del 10-15% o rinegoziare i costi di fornitura/servizi diretti."
            elif conversione < target_conv:
                path.append("Problema di Conversione (Tasso di chiusura sotto target)")
                root_cause = "Incapacità di convertire Lead in Clienti Paganti"
                action = "Rivedere gli script di vendita, il follow-up e la qualifica dei lead iniziali."
            else:
                path.append("Problema di Acquisizione (Volume insufficiente)")
                root_cause = "Traffico o Lead Generation insufficienti"
                action = "Espandere i canali di acquisizione o incrementare il budget marketing."
                
        else:
            path.append("Problema di Uscite (Struttura troppo pesante)")
            root_cause = "Costi Fissi Eccessivi rispetto alla scala attuale"
            action = "Tagliare software ridondanti, ridurre spazi fisici o ottimizzare le risorse non core."
            
    else:
        path.append("Struttura solida (Runway adeguata)")
        root_cause = "Nessuna minaccia critica immediata alla cassa."
        action = "Concentrarsi sulla scalabilità (Horizon 2) e valutare nuovi mercati."

    return {
        "analysis_path": " → ".join(path),
        "root_cause": root_cause,
        "recommended_action": action
    }