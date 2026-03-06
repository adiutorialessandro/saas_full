from flask import Blueprint, redirect, url_for
from flask_login import current_user

bp = Blueprint("index", __name__)

@bp.get("/")
def index():
    if getattr(current_user, "is_authenticated", False):
        return redirect(url_for("scans.dashboard"))
    return redirect(url_for("auth.login"))
