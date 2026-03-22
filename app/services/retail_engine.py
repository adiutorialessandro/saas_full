import json
from dataclasses import dataclass
from typing import Optional

@dataclass
class RetailInputs:
    settore: str
    mese_riferimento: str
    ricavi_dichiarati: float
    incassi_reali_stimati: float
    costi_personale: float
    costi_struttura: float
    costi_prodotti: float
    compenso_titolare: Optional[float] = None
    ticket_medio: Optional[float] = None
    clienti_mese: Optional[int] = None

def generate_retail_report(inp: RetailInputs) -> dict:
    gap_annuo = inp.incassi_reali_stimati - inp.ricavi_dichiarati
    gap_mensile = gap_annuo / 12 if gap_annuo > 0 else 0
    
    costi_totali = inp.costi_personale + inp.costi_struttura + inp.costi_prodotti
    if inp.compenso_titolare:
        costi_totali += inp.compenso_titolare
        
    utile_dichiarato = inp.ricavi_dichiarati - costi_totali
    utile_reale = inp.incassi_reali_stimati - costi_totali
    
    perc_personale_dich = (inp.costi_personale / inp.ricavi_dichiarati * 100) if inp.ricavi_dichiarati else 0
    perc_personale_reale = (inp.costi_personale / inp.incassi_reali_stimati * 100) if inp.incassi_reali_stimati else 0
    
    piano_azione = []
    
    if gap_mensile > 0:
        piano_azione.append({
            "orizzonte": "30 gg",
            "azione": "Ponte cassa (POS + contanti vs RT)",
            "dettaglio": f"Riconciliazione mensile del gap stimato di € {gap_mensile:,.0f}/mese.",
            "target": "100%",
            "owner": "Titolare"
        })
        
    piano_azione.append({
        "orizzonte": "30 gg",
        "azione": "Chiusura cassa giornaliera",
        "dettaglio": "Senza chiusura, i numeri sono opinioni.",
        "target": "> 26/30 gg",
        "owner": "Store Mgr"
    })
    
    if not inp.compenso_titolare:
        piano_azione.append({
            "orizzonte": "90 gg",
            "azione": "Compenso titolare",
            "dettaglio": "Finché è ND, il margine reale non esiste.",
            "target": "Definito e tracciato",
            "owner": "Titolare"
        })
        
    if not inp.ticket_medio or not inp.clienti_mese:
        piano_azione.append({
            "orizzonte": "60 gg",
            "azione": "Tracciamento KPI Operativi",
            "dettaglio": "Iniziare a misurare ticket medio e numero clienti nel gestionale.",
            "target": "Dati al 100%",
            "owner": "Reception"
        })

    report_data = {
        "triade": {
            "meta": {
                "settore": inp.settore,
                "mese_riferimento": inp.mese_riferimento,
                "modello": "Local/Retail"
            },
            "doppio_binario": {
                "ricavi_dichiarati": inp.ricavi_dichiarati,
                "incassi_reali": inp.incassi_reali_stimati,
                "gap_mensile": gap_mensile,
                "utile_dichiarato": utile_dichiarato,
                "utile_reale": utile_reale if inp.compenso_titolare else "ND"
            },
            "struttura_costi": {
                "personale": {
                    "valore": inp.costi_personale,
                    "perc_dichiarata": round(perc_personale_dich, 1),
                    "perc_reale": round(perc_personale_reale, 1)
                },
                "struttura": {
                    "valore": inp.costi_struttura,
                    "perc_dichiarata": round((inp.costi_struttura / inp.ricavi_dichiarati * 100), 1) if inp.ricavi_dichiarati else 0,
                    "perc_reale": round((inp.costi_struttura / inp.incassi_reali_stimati * 100), 1) if inp.incassi_reali_stimati else 0
                }
            },
            "kpi_operativi": {
                "ticket_medio": inp.ticket_medio if inp.ticket_medio else "ND",
                "clienti_mese": inp.clienti_mese if inp.clienti_mese else "ND",
                "compenso_titolare": inp.compenso_titolare if inp.compenso_titolare else "ND"
            },
            "piano_operativo_30_60_90": piano_azione
        }
    }
    return report_data
