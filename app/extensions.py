from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id: str):
    """
    Flask-Login user loader.
    Deve restituire l'utente dato l'ID salvato nella sessione.
    Import inside-function per evitare circular import.
    """
    try:
        from .models.user import User
        return db.session.get(User, int(user_id))
    except Exception:
        return None
