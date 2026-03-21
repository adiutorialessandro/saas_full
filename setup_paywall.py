import os

print("🚀 Installazione Paywall e Gestione Limiti SaaS...")

# ==========================================
# 1. CREAZIONE DELLA PAGINA PREZZI (PRICING)
# ==========================================
pricing_html = """{% extends "base.html" %}
{% block content %}
<style>
  .pricing-container { max-width: 1000px; margin: 60px auto; padding: 0 20px; text-align: center; }
  .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-top: 50px; }
  .plan-card { background: white; border-radius: 20px; padding: 40px; border: 1px solid #e2e8f0; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: transform 0.3s; position: relative; overflow: hidden; display: flex; flex-direction: column; }
  .plan-card:hover { transform: translateY(-5px); border-color: #38bdf8; }
  .plan-card.popular { border: 2px solid #8b5cf6; }
  .plan-card.popular::before { content: 'CONSIGLIATO'; position: absolute; top: 20px; right: -35px; background: #8b5cf6; color: white; padding: 5px 40px; transform: rotate(45deg); font-size: 0.7rem; font-weight: bold; letter-spacing: 1px; }
  .plan-name { font-size: 1.5rem; font-weight: 800; color: #1e293b; margin-bottom: 10px; }
  .plan-price { font-size: 3.5rem; font-weight: 900; color: #0f172a; margin-bottom: 25px; line-height: 1; }
  .plan-price span { font-size: 1.2rem; color: #64748b; font-weight: 500; }
  .plan-features { list-style: none; margin-bottom: 30px; text-align: left; flex-grow: 1; }
  .plan-features li { margin-bottom: 15px; font-size: 1rem; color: #475569; display: flex; align-items: flex-start; gap: 10px; line-height: 1.4; }
  .plan-features li i { color: #10b981; margin-top: 3px; }
  .btn-upgrade { display: inline-block; width: 100%; padding: 16px; border-radius: 12px; font-weight: bold; text-decoration: none; text-align: center; transition: all 0.2s; font-size: 1.1rem; }
  .btn-upgrade.primary { background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: white; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.2); }
  .btn-upgrade.secondary { background: #f1f5f9; color: #64748b; }
  .btn-upgrade.primary:hover { box-shadow: 0 10px 25px rgba(139, 92, 246, 0.4); transform: translateY(-2px); }
</style>

<div class="pricing-container">
    <span class="badge badge-warning" style="background: #fef08a; color: #854d0e; margin-bottom: 15px; font-size: 0.9rem; padding: 8px 16px;">UPGRADE NECESSARIO</span>
    <h1 style="font-size: 3rem; font-weight: 900; color: #0f172a; margin-bottom: 20px; letter-spacing: -1px;">Sblocca il Potere Diagnostico</h1>
    <p style="font-size: 1.2rem; color: #64748b; max-width: 650px; margin: 0 auto; line-height: 1.6;">Hai raggiunto il limite operativo del tuo piano. Passa a un livello superiore per continuare a generare analisi strategiche avanzate per la tua azienda.</p>

    <div class="pricing-grid">
        {% for plan in plans %}
        <div class="plan-card {% if loop.index == 2 or plan.price_month > 0 %}popular{% endif %}">
            <div class="plan-name">{{ plan.name }}</div>
            <div class="plan-price">€{{ "%.0f"|format(plan.price_month) }}<span>/mese</span></div>
            
            <ul class="plan-features">
                <li><i class="fas fa-check-circle"></i> <strong>{{ plan.scan_limit if plan.scan_limit != -1 else 'Illimitati' }}</strong> Dossier Strategici / mese</li>
                <li><i class="fas fa-check-circle"></i> Report PDF McKinsey Style</li>
                <li><i class="fas fa-check-circle"></i> Calcolo Business Stability Score</li>
                {% if plan.price_month > 0 or plan.scan_limit > 1 %}
                <li><i class="fas fa-check-circle"></i> AI Strategic Memo (OpenAI)</li>
                <li><i class="fas fa-check-circle"></i> What-If Simulator & Stress Test</li>
                <li><i class="fas fa-check-circle"></i> Analisi McKinsey 7S e 3 Orizzonti</li>
                {% else %}
                <li style="color: #cbd5e1;"><i class="fas fa-times-circle" style="color: #cbd5e1;"></i> Funzioni AI disabilitate</li>
                {% endif %}
            </ul>

            {% if plan.price_month > 0 %}
            <form action="{{ url_for('billing.create_checkout_session') if 'billing.create_checkout_session' in request.url_rule.endpoint else '#' }}" method="POST">
                <input type="hidden" name="plan_id" value="{{ plan.id }}">
                <button type="submit" class="btn-upgrade primary" style="border: none; cursor: pointer;">Scegli {{ plan.name }}</button>
            </form>
            {% else %}
            <button disabled class="btn-upgrade secondary" style="border: none;">Piano Base (Attuale)</button>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""
with open('app/templates/pricing.html', 'w') as f:
    f.write(pricing_html)

# ==========================================
# 2. INIEZIONE ROTTA /PRICING IN BILLING.PY
# ==========================================
billing_path = 'app/routes/billing.py'
with open(billing_path, 'r') as f:
    billing_content = f.read()

if "def pricing():" not in billing_content:
    pricing_route = """
@bp.route('/pricing')
@login_required
def pricing():
    from app.models.plan import Plan
    plans = Plan.query.order_by(Plan.price_month).all()
    return render_template('pricing.html', plans=plans)
"""
    with open(billing_path, 'a') as f:
        f.write(pricing_route)

# ==========================================
# 3. APPLICAZIONE DEL BLOCCO AL WIZARD
# ==========================================
wizard_path = 'app/routes/wizard.py'
with open(wizard_path, 'r') as f:
    wizard_content = f.read()

limit_check = """
    # --- SAAS LIMIT CHECK (PAYWALL) ---
    from app.models.scan import Scan
    org = current_user.current_org
    if org and org.plan:
        if org.plan.scan_limit != -1:
            scan_count = Scan.query.filter_by(org_id=org.id).count()
            if scan_count >= org.plan.scan_limit:
                flash("Hai raggiunto il limite di scansioni gratuite del tuo piano. Fai l'upgrade per sbloccare nuove analisi.", "warning")
                return redirect(url_for('billing.pricing'))
    # ----------------------------------
"""

if "SAAS LIMIT CHECK" not in wizard_content:
    # Cerchiamo l'inizio della funzione step1() e iniettiamo il controllo
    wizard_content = wizard_content.replace('def step1():', 'def step1():\n' + limit_check)
    with open(wizard_path, 'w') as f:
        f.write(wizard_content)

print("✅ Paywall configurato con successo!")
