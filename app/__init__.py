from flask import Flask, redirect, url_for
from .config import Config
from .extensions import db, login_manager

from .routes.auth import bp as auth_bp
from .routes.wizard import bp as wizard_bp
from .routes.scans import bp as scans_bp
from .routes.admin import bp as admin_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    @app.template_filter("fmt_dt")
    def fmt_dt(value):
        if not value:
            return ""
        try:
            return value.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return str(value)

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    @app.route("/health")
    def health():
        return "ok", 200

    app.register_blueprint(auth_bp)
    app.register_blueprint(wizard_bp)
    app.register_blueprint(scans_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app
