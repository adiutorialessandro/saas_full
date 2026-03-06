from datetime import datetime

from flask import Flask, redirect, url_for
from flask_login import current_user

from .config import Config
from .extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)

    # -----------------------------
    # Jinja filters
    # -----------------------------
    @app.template_filter("fmt_dt")
    def fmt_dt(value):
        """
        Formats datetime into 'YYYY-MM-DD HH:MM'.
        Accepts datetime or string; returns '' if None/invalid.
        """
        if not value:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        try:
            # string fallback (best-effort)
            s = str(value).replace("T", " ")
            return s[:16]
        except Exception:
            return ""

    # -----------------------------
    # Routes / Blueprints
    # -----------------------------
    from .routes.auth import bp as auth_bp
    from .routes.wizard import bp as wizard_bp
    from .routes.scans import bp as scans_bp
    from .routes.admin import bp as admin_bp
    from .routes.index import bp as index_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(wizard_bp)
    app.register_blueprint(scans_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(index_bp)

    # Health
    @app.get("/health")
    def health():
        return {"ok": True}

    return app
