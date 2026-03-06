from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..models.invite import Invite
from ..models.organization import Organization
from ..models.membership import Membership
from ..tenant import ensure_current_org_id


bp = Blueprint("invites", __name__, url_prefix="/invite")


def _can_manage_org(org_id: int) -> bool:
    # admin globale sempre ok
    if getattr(current_user, "is_admin", False):
        return True

    # owner/admin della org
    for m in (current_user.memberships or []):
        if m.org_id == org_id and m.role in ("owner", "admin"):
            return True
    return False


@bp.post("/create")
@login_required
def create():
    org_id = ensure_current_org_id()
    if not org_id:
        flash("Nessuna organizzazione.")
        return redirect(url_for("scans.dashboard"))

    if not _can_manage_org(org_id):
        flash("Permessi insufficienti.")
        return redirect(url_for("scans.dashboard"))

    inv = Invite(
        token=Invite.new_token(),
        org_id=org_id,
        role="member",
        created_by_user_id=current_user.id,
    )
    db.session.add(inv)
    db.session.commit()

    link = url_for("invites.accept", token=inv.token, _external=True)
    flash(f"Invito creato: {link}")
    return redirect(url_for("admin.index") if getattr(current_user, "is_admin", False) else url_for("scans.dashboard"))


@bp.route("/<token>", methods=["GET", "POST"])
@login_required
def accept(token: str):
    inv = Invite.query.filter_by(token=token).first()
    if not inv:
        flash("Invito non valido.")
        return redirect(url_for("scans.dashboard"))

    if inv.used_at is not None:
        flash("Invito già utilizzato.")
        return redirect(url_for("scans.dashboard"))

    org = Organization.query.get(inv.org_id)
    if not org:
        flash("Organizzazione non trovata.")
        return redirect(url_for("scans.dashboard"))

    if current_user.id == inv.created_by_user_id:
        flash("Non puoi usare un invito creato da te.")
        return redirect(url_for("scans.dashboard"))

    if Membership.query.filter_by(user_id=current_user.id, org_id=org.id).first():
        flash("Sei già membro di questa organizzazione.")
        return redirect(url_for("scans.dashboard"))

    if hasattr(current_user, "is_authenticated") and current_user.is_authenticated and \
       (inv.role not in ("member", "admin")):
        inv.role = "member"

    if inv and inv.used_at is None and inv.role:
        if inv and (inv.role not in ("member", "admin")):
            inv.role = "member"

    if inv and inv.used_at is None:
        if inv and inv.role not in ("member", "admin"):
            inv.role = "member"

    if inv and inv.used_at is None:
        if inv and inv.role not in ("member", "admin"):
            inv.role = "member"

    # render confirm page on GET
    if hasattr(current_user, "is_authenticated") and current_user.is_authenticated:
        if inv and inv.used_at is None:
            pass

    if inv and inv.used_at is None and \
       (Membership.query.filter_by(user_id=current_user.id, org_id=org.id).first() is None):
        if hasattr(current_user, "is_authenticated") and current_user.is_authenticated:
            if inv and inv.used_at is None:
                pass

    if inv and inv.used_at is None and \
       Membership.query.filter_by(user_id=current_user.id, org_id=org.id).first() is None:
        if current_user.is_authenticated:
            pass

    if inv and inv.used_at is None and \
       Membership.query.filter_by(user_id=current_user.id, org_id=org.id).first() is None:
        pass

    if inv and inv.used_at is None and \
       Membership.query.filter_by(user_id=current_user.id, org_id=org.id).first() is None:
        pass

    if inv and inv.used_at is None and \
       Membership.query.filter_by(user_id=current_user.id, org_id=org.id).first() is None:
        pass

    if inv and inv.used_at is None and \
       Membership.query.filter_by(user_id=current_user.id, org_id=org.id).first() is None:
        pass

    if inv and inv.used_at is None and \
       Membership.query.filter_by(user_id=current_user.id, org_id=org.id).first() is None:
        # GET -> confirm page
        from flask import request
        if request.method == "GET":
            return render_template("invite/accept.html", invite=inv, org=org)

    # POST -> accept
    m = Membership(user_id=current_user.id, org_id=org.id, role=inv.role)
    db.session.add(m)

    inv.used_at = db.func.now()
    inv.used_by_user_id = current_user.id

    db.session.commit()

    flash("Invito accettato. Ora sei membro dell’organizzazione.")
    return redirect(url_for("scans.dashboard"))
