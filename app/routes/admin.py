from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from ..extensions import db
from ..models.user import User
from ..models.scan import Scan

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin():
    if not getattr(current_user, "is_admin", False):
        flash("Accesso negato.")
        return False
    return True


@bp.get("/")
@login_required
def index():
    if not _require_admin():
        return redirect(url_for("scans.dashboard"))

    users = User.query.order_by(User.id.desc()).all()
    scans = Scan.query.order_by(Scan.id.desc()).limit(50).all()

    kpi = {
        "users": len(users),
        "scans": Scan.query.count(),
    }
    return render_template("admin/index.html", users=users, scans=scans, kpi=kpi)


@bp.post("/user/<int:user_id>/toggle-admin")
@login_required
def toggle_admin(user_id: int):
    if not _require_admin():
        return redirect(url_for("scans.dashboard"))

    u = User.query.get(user_id)
    if not u:
        flash("Utente non trovato.")
        return redirect(url_for("admin.index"))

    # evita di togliere admin a se stesso per sbaglio (puoi rimuovere se vuoi)
    if u.id == current_user.id:
        flash("Non puoi modificare il tuo ruolo admin da qui.")
        return redirect(url_for("admin.index"))

    u.is_admin = not bool(u.is_admin)
    db.session.commit()
    flash(f"Admin per {u.email}: {u.is_admin}")
    return redirect(url_for("admin.index"))


@bp.post("/user/<int:user_id>/delete")
@login_required
def delete_user(user_id: int):
    if not _require_admin():
        return redirect(url_for("scans.dashboard"))

    u = User.query.get(user_id)
    if not u:
        flash("Utente non trovato.")
        return redirect(url_for("admin.index"))

    if u.id == current_user.id:
        flash("Non puoi eliminare te stesso.")
        return redirect(url_for("admin.index"))

    # cancella scans utente
    Scan.query.filter_by(user_id=u.id).delete()
    db.session.delete(u)
    db.session.commit()
    flash("Utente eliminato (con scans).")
    return redirect(url_for("admin.index"))


@bp.post("/scan/<int:scan_id>/delete")
@login_required
def delete_scan(scan_id: int):
    if not _require_admin():
        return redirect(url_for("scans.dashboard"))

    s = Scan.query.get(scan_id)
    if not s:
        flash("Scan non trovato.")
        return redirect(url_for("admin.index"))

    db.session.delete(s)
    db.session.commit()
    flash("Scan eliminato.")
    return redirect(url_for("admin.index"))
