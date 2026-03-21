import os

# 1. Crea il servizio AI
ai_service_code = """import os
from typing import Dict, Any

def generate_ai_memo(state: Dict[str, Any], kpi: Dict[str, Any], meta: Dict[str, Any]) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == 'sk-la-tua-chiave-segreta-qui':
        return "⚠️ Integrazione OpenAI non attiva. Inserisci la tua vera OPENAI_API_KEY nel file .env per sbloccare il memo generato dall'Intelligenza Artificiale."

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        prompt = f'''
        Agisci come un Senior Partner di McKinsey. Scrivi un "Memo Strategico" esecutivo (massimo 3 brevi paragrafi) diretto al CEO.
        
        Contesto Aziendale:
        - Settore: {meta.get('settore', 'N/A')}
        - Salute Globale: {state.get('overall', 'N/A')} (Score: {state.get('overall_score', 'N/A')}/100)
        - Diagnosi algoritmica: {state.get('summary', 'N/A')}
        
        Dati Finanziari:
        - Runway (Cassa): {kpi.get('runway_mesi', 'N/A')} mesi
        - Margine Operativo: {kpi.get('margine_pct', 'N/A')}
        
        Regole:
        1. Tono freddo, analitico, direzionale e spietatamente orientato all'azione.
        2. Niente saluti ("Gentile CEO", ecc.). Inizia subito con l'analisi.
        3. Fornisci la priorità assoluta per i prossimi 30 giorni basandoti su cassa e margine.
        '''

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sei uno stratega aziendale d'élite."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=400
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Errore generazione AI: {str(e)}"
"""

with open('app/services/ai_service.py', 'w') as f:
    f.write(ai_service_code)
print("✅ Creato app/services/ai_service.py")

# 2. Aggiorna report_builder.py
rb_path = 'app/services/report_builder.py'
with open(rb_path, 'r') as f:
    content = f.read()

if 'generate_ai_memo' not in content:
    content = "from app.services.ai_service import generate_ai_memo\n" + content
    
    target = 'return {\n        "triade": {'
    replacement = '''
    # --- INTEGRAZIONE OPENAI ---
    ai_memo = generate_ai_memo(
        state={"overall": stability_status, "overall_score": stability_score, "summary": executive_summary},
        kpi=kpi_dict,
        meta={"settore": inp.settore}
    )
    # ---------------------------
    return {
        "triade": {'''
    content = content.replace(target, replacement)
    
    target2 = '"competitive_positioning": competitors_analysis,'
    replacement2 = '"competitive_positioning": competitors_analysis,\n                "ai_memo": ai_memo,'
    content = content.replace(target2, replacement2)

    with open(rb_path, 'w') as f:
        f.write(content)
    print("✅ report_builder.py aggiornato con successo!")
else:
    print("⚠️ report_builder.py conteneva già l'integrazione.")
