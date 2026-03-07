import os


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY") or "dev-secret"

    db_url = os.environ.get("DATABASE_URL", "sqlite:///dev.db")

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BILLING_ENABLED = os.environ.get("BILLING_ENABLED", "false").lower() == "true"

    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PORTAL_RETURN_URL = os.environ.get("STRIPE_PORTAL_RETURN_URL", "")
    STRIPE_CHECKOUT_SUCCESS_URL = os.environ.get("STRIPE_CHECKOUT_SUCCESS_URL", "")
    STRIPE_CHECKOUT_CANCEL_URL = os.environ.get("STRIPE_CHECKOUT_CANCEL_URL", "")

    EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@saasfull.local")
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")