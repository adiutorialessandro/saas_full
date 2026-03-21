import os

print("🚀 Aggiornamento Admin Dashboard con Statistiche Live...")

# 1. Aggiornamento delle rotte in admin.py per calcolare i KPI del SaaS
admin_path = 'app/routes/admin.py'
with open(admin_path, 'r') as f:
    content = f.read()

# Calcolo MRR e statistiche
stats_logic = """
    # --- CALCOLO STATISTICHE SAAS ---
    from app.models.organization import Organization
    from app.models.scan import Scan
    from app.models.user import User
    from app.models.plan import Plan
    from sqlalchemy import func
    
    total_orgs = Organization.query.count()
    total_scans = Scan.query.count()
    total_users = User.query.count()
    
    # Calcolo MRR (Monthly Recurring Revenue) stimato
    # Somma il prezzo del piano di ogni organizzazione
    mrr = db.session.query(func.sum(Plan.price_month)).join(Organization).filter(Organization.plan_id == Plan.id).scalar() or 0
    
    # Scan nelle ultime 24 ore
    from datetime import datetime, timedelta
    last_24h = datetime.utcnow() - timedelta(days=1)
    scans_24h = Scan.query.filter(Scan.created_at >= last_24h).count()
    # --------------------------------
"""

if "total_orgs =" not in content:
    # Inseriamo la logica dentro la funzione index()
    content = content.replace('def index():', 'def index():\n' + stats_logic)
    
    # Passiamo le variabili al template
    content = content.replace('return render_template("admin/index.html")', 
                             'return render_template("admin/index.html", total_orgs=total_orgs, total_scans=total_scans, total_users=total_users, mrr=mrr, scans_24h=scans_24h)')
    
    with open(admin_path, 'w') as f:
        f.write(content)

# 2. Aggiornamento del Template admin/index.html
admin_html_path = 'app/templates/admin/index.html'
with open(admin_html_path, 'r') as f:
    html = f.read()

stats_ui = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px;">
        <div class="card" style="border-left: 5px solid #8b5cf6; padding: 20px;">
            <div style="color: #64748b; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">Estimated MRR</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #1e293b;">€ {{ "{:,.2f}".format(mrr).replace(',', '.') }}</div>
            <div style="color: #10b981; font-size: 0.8rem; margin-top: 5px;"><i class="fas fa-chart-line"></i> Ricavo Mensile</div>
        </div>
        <div class="card" style="border-left: 5px solid #3b82f6; padding: 20px;">
            <div style="color: #64748b; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">Total Scans</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #1e293b;">{{ total_scans }}</div>
            <div style="color: #3b82f6; font-size: 0.8rem; margin-top: 5px;"><i class="fas fa-bolt"></i> {{ scans_24h }} nelle ultime 24h</div>
        </div>
        <div class="card" style="border-left: 5px solid #10b981; padding: 20px;">
            <div style="color: #64748b; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">Organizations</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #1e293b;">{{ total_orgs }}</div>
            <div style="color: #64748b; font-size: 0.8rem; margin-top: 5px;">Tenant Attivi</div>
        </div>
        <div class="card" style="border-left: 5px solid #f59e0b; padding: 20px;">
            <div style="color: #64748b; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">Users</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #1e293b;">{{ total_users }}</div>
            <div style="color: #64748b; font-size: 0.8rem; margin-top: 5px;">Utenti Registrati</div>
        </div>
    </div>
"""

if "Estimated MRR" not in html:
    # Inseriamo le stats subito dopo il titolo H1
    html = html.replace('</h1>', '</h1>\n' + stats_ui)
    with open(admin_html_path, 'w') as f:
        f.write(html)

print("✅ Admin Dashboard aggiornata con le Statistiche Live!")
