import os

class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY") or "dev-secret"

    db_url = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
