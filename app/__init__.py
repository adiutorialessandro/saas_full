import os
from flask import Flask, render_template
from .extensions import db, migrate, login_manager
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    from .routes.auth import bp as auth_bp
    from .routes.admin import bp as admin_bp
    from .routes.orgs import bp as orgs_bp
    from .routes.invites import bp as invites_bp
    from .routes.billing import bp as billing_bp
    from .routes.wizard import bp as wizard_bp
    from .routes.scans import bp as scans_bp
    from .routes.report import bp as report_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(orgs_bp)
    app.register_blueprint(invites_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(wizard_bp)
    app.register_blueprint(scans_bp)
    app.register_blueprint(report_bp)

    # ========================================================
    # FIX: FILTRO JINJA PER LE DATE
    # ========================================================
    @app.template_filter('fmt_dt')
    def fmt_dt(value):
        if value is None:
            return ""
        try:
            return value.strftime("%d/%m/%Y")
        except Exception:
            return str(value)

    @app.route("/")
    def index():
        from .models.plan import Plan
        plans = Plan.query.all()
        return render_template("landing.html", plans=plans)
    
    @app.route('/pricing')
    def pricing():
        from .models.plan import Plan
        plans = Plan.query.all()
        return render_template('pricing.html', plans=plans)

    # ========================================================
    # AUTO-RISOLUZIONE DEL DATABASE AL LANCIO
    # ========================================================
    with app.app_context():
        db.create_all()
        
        from .models.benchmark import SectorBenchmark
        if SectorBenchmark.query.count() == 0:
            benchmarks = [
                {"sector_name": "Consulenza B2B", "margine_lordo_target": 62.0, "conversione_target": 26.0, "break_even_sano": 1.10, "runway_minima": 6},
                {"sector_name": "Retail", "margine_lordo_target": 33.0, "conversione_target": 5.0, "break_even_sano": 1.05, "runway_minima": 3},
                {"sector_name": "Manifattura", "margine_lordo_target": 37.0, "conversione_target": 20.0, "break_even_sano": 1.08, "runway_minima": 4},
                {"sector_name": "SaaS / Tech", "margine_lordo_target": 72.0, "conversione_target": 10.0, "break_even_sano": 1.20, "runway_minima": 12},
                {"sector_name": "Ho.Re.Ca.", "margine_lordo_target": 61.0, "conversione_target": 0.0, "break_even_sano": 1.05, "runway_minima": 2},
                {"sector_name": "Immobiliare", "margine_lordo_target": 42.0, "conversione_target": 13.0, "break_even_sano": 1.10, "runway_minima": 6},
                {"sector_name": "Sanità / Studi medici", "margine_lordo_target": 52.0, "conversione_target": 50.0, "break_even_sano": 1.15, "runway_minima": 4}
            ]
            for b in benchmarks:
                db.session.add(SectorBenchmark(**b))
            db.session.commit()

        # CREAZIONE PIANI AUTOMATICA CON LIMITE SBLOCCATO
        from .models.plan import Plan
        if Plan.query.count() == 0:
            p1 = Plan(name="Starter", scan_limit=100, price_month=0.0)
            p2 = Plan(name="Pro", scan_limit=10, price_month=49.0)
            p3 = Plan(name="Enterprise", scan_limit=-1, price_month=199.0)
            db.session.add_all([p1, p2, p3])
            db.session.commit()

        # FIX PER UTENTI ESISTENTI SENZA PIANO
        from .models.organization import Organization
        default_plan = Plan.query.filter_by(name="Starter").first()
        if default_plan:
            orgs = Organization.query.filter_by(plan_id=None).all()
            for o in orgs:
                o.plan_id = default_plan.id
            db.session.commit()

    return app

from .models import user, organization, scan, plan, invite, membership
