from flask import Blueprint, redirect, url_for
from flask_login import current_user

bp = Blueprint("home", __name__)

@bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("scans.dashboard"))
    return redirect(url_for("auth.login"))
