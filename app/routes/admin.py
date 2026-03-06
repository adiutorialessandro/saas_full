from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..models.organization import Organization
from ..models.membership import Membership
from ..models.user import User
from ..models.scan import Scan
from ..extensions import db

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required():
    return current_user.is_authenticated and current_user.is_admin


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