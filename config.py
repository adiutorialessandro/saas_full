import os

class Config:
    # === SICUREZZA ===
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY") or "dev-secret"

    # === DATABASE ===
    db_url = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === BILLING & STRIPE ===
    BILLING_ENABLED = os.environ.get("BILLING_ENABLED", "false").lower() == "true"
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PORTAL_RETURN_URL = os.environ.get("STRIPE_PORTAL_RETURN_URL", "")
    STRIPE_CHECKOUT_SUCCESS_URL = os.environ.get("STRIPE_CHECKOUT_SUCCESS_URL", "")
    STRIPE_CHECKOUT_CANCEL_URL = os.environ.get("STRIPE_CHECKOUT_CANCEL_URL", "")

    # === CONFIGURAZIONE EMAIL (FLASK-MAIL) ===
    # Legge le chiavi impostate su Render
    EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "true").lower() == "true"
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = False

    # Credenziali
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "a.a.personalstudio@gmail.com")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")

    # Mittente
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "SaaS Full Advisory <a.a.personalstudio@gmail.com>")
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")
