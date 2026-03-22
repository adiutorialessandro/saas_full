import json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Inputs:
    settore: str
    modello: str
    mese_riferimento: str
    dimensione: str
    dipendenti: str
    area_geografica: str
    fatturato: str
    tipologia_clienti: str
    cassa_attuale: float
    burn_mensile: float
    incassi_mese: float
    costi_fissi_mese: float
    margine_lordo_pct: float
    leads_mese: int
    clienti_mese: int
    quiz_responses: Dict[str, Any]
    quiz_risk: list

def generate_deterministic_report(inp: Inputs, benchmark) -> dict:
    
    # 0. FALLBACK SICUREZZA
    if not benchmark:
        class DummyBench:
            sector_name = inp.settore
            margine_lordo_target = 40.0
            runway_minima = 4.0
            break_even_sano = 1.05
            conversione_target = 5.0
        benchmark = DummyBench()

    # 1. CALCOLO MATEMATICO KPI
    cassa = float(inp.cassa_attuale or 0)
    burn = float(inp.burn_mensile or 1)
    incassi = float(inp.incassi_mese or 0)
    costi_fissi = float(inp.costi_fissi_mese or 1)
    margine = float(inp.margine_lordo_pct or 30)
    
    runway = round(cassa / burn, 1) if burn > 0 else 99.0
    break_even = round(incassi / costi_fissi, 2) if costi_fissi > 0 else 99.0
    
    # --- MIGLIORAMENTO 2: PENALITÀ PROPORZIONALI ---
    score = 100
    critical_kpis = []
    
    # Distanza dal Margine
    if margine < benchmark.margine_lordo_target:
        gap = benchmark.margine_lordo_target - margine
        penalty = min(25, int((gap / benchmark.margine_lordo_target) * 40))
        score -= penalty
        if penalty > 10: critical_kpis.append({"area": "Margine Lordo", "risk": min(99, penalty * 3)})
        
    # Distanza dalla Runway
    if runway < benchmark.runway_minima:
        gap = benchmark.runway_minima - runway
        penalty = min(40, int((gap / benchmark.runway_minima) * 50))
        score -= penalty
        if penalty > 15: critical_kpis.append({"area": "Cash Runway", "risk": min(99, penalty * 2)})
        
    # Distanza Break-Even
    if break_even < benchmark.break_even_sano:
        gap = benchmark.break_even_sano - break_even
        penalty = min(20, int((gap / benchmark.break_even_sano) * 30))
        score -= penalty
        if penalty > 5: critical_kpis.append({"area": "Break-Even Ratio", "risk": min(99, penalty * 4)})
        
    score = max(0, min(100, score))
    status = "SAFE" if score >= 75 else "WARNING" if score >= 50 else "RISK"

    # --- MIGLIORAMENTO 1: INTEGRAZIONE REALE DEL QUESTIONARIO ---
    quiz = inp.quiz_responses or {}
    quiz_values = [int(v) for v in quiz.values() if str(v).isdigit()]
    
    if quiz_values:
        # Calcola la media (assumendo risposte da 1 a 5)
        org_score = int((sum(quiz_values) / (len(quiz_values) * 5)) * 100)
    else:
        org_score = 60 # Fallback se l'utente non compila il quiz
        
    org_status = "Eccellente" if org_score >= 80 else "Stabile" if org_score >= 60 else "Fragile"

    # --- MIGLIORAMENTO 3: COLLO DI BOTTIGLIA DINAMICO ---
    # Cerchiamo qual è l'area più critica tra Marketing, Sales e Cash
    sales_score = int((inp.clienti_mese / max(1, inp.leads_mese) * 100) / benchmark.conversione_target * 100) if benchmark.conversione_target else 100
    cash_score = int((runway / max(1, benchmark.runway_minima)) * 100)
    
    if cash_score < 50:
        root_cause = "Liquidità e Sopravvivenza a Rischio"
        root_path = "Financial > Cash Management > Runway"
        action = "Bloccare immediatamente le spese discrezionali e rinegoziare i termini di pagamento."
        bottleneck = "Cash"
    elif margine < benchmark.margine_lordo_target:
        root_cause = "Incapacità di Estrazione Valore"
        root_path = "Financial > Unit Economics > Gross Margin"
        action = "Rivedere il pricing e ottimizzare i costi variabili (COGS)."
        bottleneck = "Margin"
    elif sales_score < 70:
        root_cause = "Inefficienza del Processo di Vendita"
        root_path = "Operations > Sales > Conversion Rate"
        action = "Ottimizzare lo script di vendita e la qualifica dei lead."
        bottleneck = "Sales"
    else:
        root_cause = "Ottimizzazione dei Processi"
        root_path = "Operations > Scaling > Efficiency"
        action = "L'azienda è solida. Focus sull'automazione per preparare la scalabilità."
        bottleneck = "Marketing"

    # --- TESTI DINAMICI ---
    if status == "RISK":
        memo_text = f"La situazione finanziaria attuale richiede un intervento immediato. Con un runway di {runway} mesi e un punteggio di stabilità del {score}/100, è vitale proteggere la cassa."
        urgency = "ALTO"
    elif status == "WARNING":
        memo_text = f"L'azienda presenta basi valide ma inefficienze operative. Il collo di bottiglia principale risiede nell'area '{bottleneck}'. Ottimizzare quest'area per sbloccare la redditività latente."
        urgency = "MEDIO"
    else:
        memo_text = f"L'azienda sovraperforma i benchmark del settore {benchmark.sector_name}. Con metriche positive e una salute organizzativa al {org_score}/100, il focus deve spostarsi sulla conquista di nuove quote di mercato."
        urgency = "BASSO"

    # --- 4. COSTRUZIONE DIZIONARIO ---
    report_data = {
        "triade": {
            "meta": {
                "settore": benchmark.sector_name,
                "modello": inp.modello,
                "mese_riferimento": inp.mese_riferimento
            },
            "state": {
                "overall_score": score,
                "overall": status,
                "confidence": 100, 
                "maturity_label": "Consolidamento" if score > 50 else "Start/Ristrutturazione",
                "resilience_label": "Alta" if runway > 6 else "Bassa",
                "summary": "Analisi diagnostica generata tramite algoritmo proprietario SaaS Full.",
                "ai_memo": memo_text,
                "critical_kpis": critical_kpis,
                "maturity_score": score
            },
            "kpi": {
                "runway_mesi": runway,
                "margine_pct": margine / 100,
                "break_even_ratio": break_even
            },
            "financial_projections": {
                "ebitda_gap": max(0, (benchmark.margine_lordo_target - margine) * 1000), 
                "stress_test": {
                    "shock_20": round(runway * 0.8, 1),
                    "shock_30": round(runway * 0.6, 1),
                    "late_payments": round(runway * 0.4, 1)
                },
                "simulator": {
                    "cost_cut_10": round(runway * 1.2, 1),
                    "cost_cut_20": "Safe" if round(runway * 1.4, 1) > benchmark.runway_minima else round(runway * 1.4, 1),
                    "rev_up_10": round(runway * 1.15, 1)
                }
            },
            "risks": {"cash": score},
            "advanced_strategy": {
                "root_cause": {
                    "analysis_path": root_path,
                    "root_cause": root_cause,
                    "recommended_action": action
                },
                "organizational_health": {
                    "score": org_score,
                    "status": org_status,
                    "insights": [
                        "Dati basati sulle risposte dirette dell'Executive Team." if quiz_values else "Dati stimati. Si consiglia di compilare il questionario completo.",
                        "L'allineamento del team richiede attenzione immediata." if org_score < 60 else "Cultura aziendale allineata agli obiettivi di business."
                    ]
                },
                "value_chain": {
                    "bottleneck": {"stage": bottleneck},
                    "strategic_insight": f"Focalizzare le risorse per risolvere le inefficienze nella fase di {bottleneck}.",
                    "value_chain": [
                        {"stage": "Marketing", "score": 85, "label": "Lead Gen"},
                        {"stage": "Sales", "score": min(100, sales_score), "label": "Conv."},
                        {"stage": "Cash", "score": min(100, cash_score), "label": "Runway"}
                    ]
                },
                "three_horizons": {
                    "urgency_level": urgency,
                    "resource_allocation": {"H1": "70%", "H2": "20%", "H3": "10%"} if urgency == "ALTO" else {"H1": "50%", "H2": "30%", "H3": "20%"},
                    "horizons": {
                        "Horizon_1_Core": {"focus": "Gestione Emergenze" if urgency == "ALTO" else "Ottimizzazione Core", "actions": [action, "Monitoraggio KPI settimanale"]},
                        "Horizon_2_Emerging": {"focus": "Espansione Margini", "actions": ["Upselling sui clienti esistenti", "Automazione processi manuali"]},
                        "Horizon_3_Future": {"focus": "Innovazione Disruptiva", "actions": ["Lancio nuovi prodotti", "Espansione in nuovi mercati geografici"]}
                    }
                }
            }
        }
    }
    
    return report_data