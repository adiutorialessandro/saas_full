from flask import Blueprint, redirect, url_for, flash, session
from flask_login import login_required, current_user

bp = Blueprint("orgs", __name__, url_prefix="/orgs")


@bp.get("/switch/<int:org_id>")
@login_required
def switch(org_id: int):
    # consenti switch solo se l'utente è membro dell'org
    mids = [m.org_id for m in (current_user.memberships or [])]
    if org_id not in mids and not getattr(current_user, "is_admin", False):
        flash("Accesso negato.")
        return redirect(url_for("scans.dashboard"))

    session["org_id"] = int(org_id)
    flash(f"Organizzazione selezionata: #{org_id}")
    return redirect(url_for("scans.dashboard"))
