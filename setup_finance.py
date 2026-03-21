import os

print("🚀 Inizio installazione Modulo Finanziario...")

# 1. Crea il Motore Finanziario (financial.py)
os.makedirs('app/services/analysis', exist_ok=True)
finance_code = """from typing import Dict, Any

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
"""
with open('app/services/analysis/financial.py', 'w') as f:
    f.write(finance_code)
print("✅ Creato app/services/analysis/financial.py")

# 2. Aggiorna report_builder.py
with open('app/services/report_builder.py', 'r') as f:
    content = f.read()

if "calculate_financial_projections" not in content:
    content = "from app.services.analysis.financial import calculate_financial_projections\n" + content
    
    target = 'return {\n        "triade": {'
    injection = '''
    # --- INTEGRAZIONE FINANCIAL ENGINE ---
    fin_projections = calculate_financial_projections(kpi_dict, b_margin_good)
    # -----------------------------------
    return {
        "triade": {'''
    content = content.replace(target, injection)
    
    target2 = '"ai_memo": ai_memo,'
    injection2 = '"ai_memo": ai_memo,\n                "financial_projections": fin_projections,'
    content = content.replace(target2, injection2)
    
    with open('app/services/report_builder.py', 'w') as f:
        f.write(content)
    print("✅ report_builder.py patchato con successo!")
else:
    print("⚠️ report_builder.py conteneva già il motore finanziario.")

# 3. Aggiorna report_full.html
html_injection = """
  {# ========================================================= #}
  {# INIZIO BLOCCO FINANCIAL PROJECTIONS                       #}
  {# ========================================================= #}
  {% set fin = vm.triade.financial_projections if vm.triade is defined and vm.triade.financial_projections else vm.financial_projections if vm.financial_projections else {} %}
  {% if fin %}
  <div style="margin-top: 60px; padding-top: 40px; border-top: 2px dashed #ccc;">
    <div class="section-header">
      <h2>Financial Intelligence & Stress Test</h2>
    </div>
    <div class="section-subtitle">Simulazioni di cassa, scenari di crisi e inefficienze.</div>

    <div class="grid-3">
      {# EBITDA GAP #}
      <div class="card" style="border-top: 6px solid #e63946;">
        <div class="card-title">📉 Inefficiency Cost</div>
        <div style="font-size: 2.2em; font-weight: 800; color: #e63946; margin: 10px 0; line-height: 1;">
          € {{ "{:,.0f}".format(fin.ebitda_gap).replace(',', '.') }}
        </div>
        <div class="card-desc">Margine annuo lasciato sul tavolo (EBITDA Gap) a causa della distanza dal target di efficienza del settore.</div>
      </div>

      {# STRESS TEST #}
      <div class="card" style="border-top: 6px solid #f59e0b;">
        <div class="card-title">🌪️ Stress Test (Runway)</div>
        <ul style="list-style: none; margin-top: 15px;">
          <li style="margin-bottom: 12px; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 5px;">
            <span style="color: #555;">Shock Ricavi -20%:</span> <strong>{{ fin.stress_test.shock_20 }} mesi</strong>
          </li>
          <li style="margin-bottom: 12px; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 5px;">
            <span style="color: #555;">Shock Ricavi -30%:</span> <strong>{{ fin.stress_test.shock_30 }} mesi</strong>
          </li>
          <li style="display: flex; justify-content: space-between;">
            <span style="color: #555;">Ritardi Incasso (50%):</span> <strong>{{ fin.stress_test.late_payments }} mesi</strong>
          </li>
        </ul>
        <div class="card-desc" style="font-size: 0.85em; margin-top: 15px;">Come cambia la sopravvivenza in caso di crisi esterna.</div>
      </div>

      {# SIMULATOR #}
      <div class="card" style="border-top: 6px solid #10b981;">
        <div class="card-title">📈 What-If Simulator</div>
        <ul style="list-style: none; margin-top: 15px;">
          <li style="margin-bottom: 12px; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 5px;">
            <span style="color: #555;">Taglio Costi 10%:</span> <strong style="color: #10b981;">{{ fin.simulator.cost_cut_10 }} mesi</strong>
          </li>
          <li style="margin-bottom: 12px; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 5px;">
            <span style="color: #555;">Taglio Costi 20%:</span> <strong style="color: #10b981;">{{ fin.simulator.cost_cut_20 }} mesi</strong>
          </li>
          <li style="display: flex; justify-content: space-between;">
            <span style="color: #555;">Ricavi +10%:</span> <strong style="color: #10b981;">{{ fin.simulator.rev_up_10 }} mesi</strong>
          </li>
        </ul>
        <div class="card-desc" style="font-size: 0.85em; margin-top: 15px;">Impatto sul cashflow delle manovre correttive.</div>
      </div>
    </div>
  </div>
  {% endif %}
"""
with open('app/templates/report_full.html', 'r') as f:
    html_content = f.read()

target_marker = "{# INIZIO BLOCCO ADVANCED STRATEGY"
if target_marker in html_content and "Financial Intelligence" not in html_content:
    parts = html_content.split(target_marker, 1)
    new_html = parts[0] + html_injection + "\n  " + target_marker + parts[1]
    with open('app/templates/report_full.html', 'w') as f:
        f.write(new_html)
    print("✅ report_full.html aggiornato con i nuovi Widget Finanziari!")
else:
    print("⚠️ report_full.html era già aggiornato o marker non trovato.")

print("🎉 INSTALLAZIONE COMPLETATA!")
