from pathlib import Path
from app.services.pdf_report import generate_scan_pdf_enterprise

scan_meta = {
    "settore": "Servizi",
    "modello": "b2b",
    "mese_riferimento": "2026-02",
    "id": "TEST-001",
}

vm = {
    "deck_mode": True,  # metti False se vuoi REPORT MODE
    "branding": {"watermark": "CONFIDENTIAL"},
    "risks": {"cash": 0.72, "margini": 0.435, "acq": 0.435},
    "state": {"overall": "ATTENZIONE"},
    "kpi": {"runway_mesi": 3.1, "break_even_ratio": 1.05, "conversione": 0.0833, "margine_pct": 0.45},
    "alerts": [
        {"level": "ATTENZIONE", "text": "Runway stimata 3.1 mesi: margine di sicurezza limitato. Cashflow settimanale consigliato."},
        {"level": "ATTENZIONE", "text": "Conversione media (8.33%): ottimizza messaggi, pipeline e prossimi step."},
        {"level": "ATTENZIONE", "text": "Vicino al break-even (ratio 1.05): piccole variazioni possono creare deficit."},
    ],
}

out = Path("out_scan.pdf")
p = generate_scan_pdf_enterprise(out, scan_meta, vm)
print("Creato:", p.resolve())
