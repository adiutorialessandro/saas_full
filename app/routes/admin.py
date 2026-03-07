from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..models.organization import Organization
from ..models.membership import Membership
from ..models.user import User
from ..models.scan import Scan
from ..extensions import db

from ..forms import CreateOrganizationForm

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required():
    return current_user.is_authenticated and current_user.is_admin

@bp.route("/organizations/new", methods=["GET", "POST"])
@login_required
def create_organization():
    if not current_user.is_admin:
        return "Forbidden", 403

    form = CreateOrganizationForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if User.query.filter_by(email=email).first():
            flash("Email già registrata.")
            return render_template("admin/new_org.html", form=form)

        # crea utente
        user = User(email=email)
        user.set_password(form.password.data)

        # crea azienda
        org = Organization(name=form.name.data)

        db.session.add(user)
        db.session.add(org)
        db.session.flush()

        # collega utente all'azienda
        membership = Membership(
            user_id=user.id,
            org_id=org.id,
            role="owner"
        )

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
            "scans": scans_count
        })

    return render_template("admin/organizations.html", rows=rows)
