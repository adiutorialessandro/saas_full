from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user

from ..extensions import db
from ..models.user import User
from ..models.organization import Organization
from ..models.membership import Membership
from ..models.scan import Scan
from ..forms import (
    CreateOrganizationForm,
    CreateOrgUserForm,
    UpdateOrgUserRoleForm,
    ResetUserPasswordForm,
)

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required() -> bool:
    return current_user.is_authenticated and bool(getattr(current_user, "is_admin", False))


@bp.get("/")
@login_required
def index():
    if not admin_required():
        return "Forbidden", 403

    users_count = User.query.count()
    orgs_count = Organization.query.count()
    scans_count = Scan.query.count()

    rows = []
    scans = Scan.query.order_by(Scan.id.desc()).limit(20).all()
    for s in scans:
        org = Organization.query.filter_by(id=s.org_id).first()
        user = User.query.filter_by(id=s.user_id).first()
        rows.append({
            "scan": s,
            "org_name": org.name if org else "—",
            "user_email": user.email if user else "—",
        })

    return render_template(
        "admin/index.html",
        users_count=users_count,
        orgs_count=orgs_count,
        scans_count=scans_count,
        rows=rows,
    )


@bp.route("/organizations/new", methods=["GET", "POST"])
@login_required
def create_organization():
    if not admin_required():
        return "Forbidden", 403

    form = CreateOrganizationForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        org_name = form.name.data.strip()

        if User.query.filter_by(email=email).first():
            flash("Email già registrata.")
            return render_template("admin/new_org.html", form=form)

        if Organization.query.filter_by(name=org_name).first():
            flash("Nome azienda già esistente.")
            return render_template("admin/new_org.html", form=form)

        user = User(email=email, is_admin=False)
        user.set_password(form.password.data)

        org = Organization(name=org_name)

        db.session.add(user)
        db.session.add(org)
        db.session.flush()

        membership = Membership(user_id=user.id, org_id=org.id, role="owner")
        db.session.add(membership)
        db.session.commit()

        flash("Azienda creata con successo.")
        return redirect(url_for("admin.organizations"))

    return render_template("admin/new_org.html", form=form)


@bp.get("/organizations")
@login_required
def organizations():
    if not admin_required():
        return "Forbidden", 403

    orgs = Organization.query.order_by(Organization.id.desc()).all()

    rows = []
    for org in orgs:
        owner = (
            db.session.query(User)
            .join(Membership, Membership.user_id == User.id)
            .filter(Membership.org_id == org.id, Membership.role == "owner")
            .first()
        )

        users_count = Membership.query.filter_by(org_id=org.id).count()
        scans_count = Scan.query.filter_by(org_id=org.id).count()

        rows.append({
            "org": org,
            "owner": owner.email if owner else "—",
            "users": users_count,
            "scans": scans_count,
        })

    return render_template("admin/organizations.html", rows=rows)


@bp.get("/organizations/<int:org_id>")
@login_required
def organization_detail(org_id: int):
    if not admin_required():
        return "Forbidden", 403

    org = Organization.query.get_or_404(org_id)

    memberships = Membership.query.filter_by(org_id=org.id).order_by(Membership.id.asc()).all()

    users = []
    for m in memberships:
        u = User.query.filter_by(id=m.user_id).first()
        if u:
            users.append({
                "id": u.id,
                "email": u.email,
                "is_admin": bool(u.is_admin),
                "role": m.role,
                "membership_id": m.id,
            })

    scans = Scan.query.filter_by(org_id=org.id).order_by(Scan.id.desc()).all()

    return render_template(
        "admin/organization_detail.html",
        org=org,
        users=users,
        scans=scans,
    )


@bp.route("/organizations/<int:org_id>/users/new", methods=["GET", "POST"])
@login_required
def create_org_user(org_id: int):
    if not admin_required():
        return "Forbidden", 403

    org = Organization.query.get_or_404(org_id)
    form = CreateOrgUserForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        role = form.role.data.strip().lower()

        if role not in {"owner", "admin", "manager", "member"}:
            flash("Ruolo non valido. Usa: owner, admin, manager o member.")
            return render_template("admin/new_org_user.html", form=form, org=org)

        if User.query.filter_by(email=email).first():
            flash("Email già registrata.")
            return render_template("admin/new_org_user.html", form=form, org=org)

        user = User(email=email, is_admin=False)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.flush()

        membership = Membership(user_id=user.id, org_id=org.id, role=role)
        db.session.add(membership)
        db.session.commit()

        flash("Utente cliente creato con successo.")
        return redirect(url_for("admin.organization_detail", org_id=org.id))

    return render_template("admin/new_org_user.html", form=form, org=org)


@bp.route("/organizations/<int:org_id>/users/<int:user_id>/role", methods=["GET", "POST"])
@login_required
def update_org_user_role(org_id: int, user_id: int):
    if not admin_required():
        return "Forbidden", 403

    org = Organization.query.get_or_404(org_id)
    user = User.query.get_or_404(user_id)
    membership = Membership.query.filter_by(org_id=org.id, user_id=user.id).first_or_404()

    form = UpdateOrgUserRoleForm(role=membership.role)

    if form.validate_on_submit():
        role = form.role.data.strip().lower()

        if role not in {"owner", "admin", "manager", "member"}:
            flash("Ruolo non valido. Usa: owner, admin, manager o member.")
            return render_template(
                "admin/edit_org_user_role.html",
                form=form,
                org=org,
                user=user,
                membership=membership,
            )

        membership.role = role
        db.session.commit()

        flash("Ruolo aggiornato con successo.")
        return redirect(url_for("admin.organization_detail", org_id=org.id))

    return render_template(
        "admin/edit_org_user_role.html",
        form=form,
        org=org,
        user=user,
        membership=membership,
    )


@bp.route("/organizations/<int:org_id>/users/<int:user_id>/reset-password", methods=["GET", "POST"])
@login_required
def reset_org_user_password(org_id: int, user_id: int):
    if not admin_required():
        return "Forbidden", 403

    org = Organization.query.get_or_404(org_id)
    user = User.query.get_or_404(user_id)

    membership = Membership.query.filter_by(org_id=org.id, user_id=user.id).first()
    if not membership:
        flash("Associazione utente/azienda non trovata.")
        return redirect(url_for("admin.organization_detail", org_id=org.id))

    form = ResetUserPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Password aggiornata con successo.")
        return redirect(url_for("admin.organization_detail", org_id=org.id))

    return render_template("admin/reset_user_password.html", form=form, org=org, user=user)


@bp.post("/organizations/<int:org_id>/users/<int:user_id>/delete")
@login_required
def delete_org_user(org_id: int, user_id: int):
    if not admin_required():
        return "Forbidden", 403

    org = Organization.query.get_or_404(org_id)
    user = User.query.get_or_404(user_id)

    membership = Membership.query.filter_by(org_id=org.id, user_id=user.id).first()
    if not membership:
        flash("Associazione utente/azienda non trovata.")
        return redirect(url_for("admin.organization_detail", org_id=org.id))

    db.session.delete(membership)
    db.session.flush()

    remaining_memberships = Membership.query.filter_by(user_id=user.id).count()
    if remaining_memberships == 0:
        db.session.delete(user)

    db.session.commit()
    flash("Utente rimosso dall'azienda.")
    return redirect(url_for("admin.organization_detail", org_id=org.id))


@bp.post("/user/<int:user_id>/toggle-admin")
@login_required
def toggle_admin(user_id: int):
    if not admin_required():
        return "Forbidden", 403

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("Non puoi modificare il tuo ruolo admin da qui.")
        return redirect(url_for("admin.index"))

    user.is_admin = not bool(user.is_admin)
    db.session.commit()

    flash(f"Permessi admin aggiornati per {user.email}.")
    return redirect(url_for("admin.index"))


@bp.post("/user/<int:user_id>/delete")
@login_required
def delete_user(user_id: int):
    if not admin_required():
        return "Forbidden", 403

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("Non puoi eliminare il tuo account da qui.")
        return redirect(url_for("admin.index"))

    memberships = Membership.query.filter_by(user_id=user.id).all()
    for m in memberships:
        db.session.delete(m)

    db.session.delete(user)
    db.session.commit()

    flash("Utente eliminato.")
    return redirect(url_for("admin.index"))


@bp.post("/scan/<int:scan_id>/delete")
@login_required
def delete_scan(scan_id: int):
    if not admin_required():
        return "Forbidden", 403

    scan = Scan.query.get_or_404(scan_id)
    db.session.delete(scan)
    db.session.commit()

    flash(f"Scan #{scan_id} eliminato.")
    return redirect(url_for("admin.index"))