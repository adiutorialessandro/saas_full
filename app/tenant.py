from flask import session
from flask_login import current_user

from .extensions import db
from .models.organization import Organization
from .models.membership import Membership


def current_org_id() -> int:
    try:
        return int(session.get("org_id") or 0)
    except Exception:
        return 0


def ensure_current_org_id() -> int:
    if not current_user.is_authenticated:
        return 0

    org_id = session.get("org_id")
    if org_id:
        return int(org_id)

    m = Membership.query.filter_by(user_id=current_user.id).first()
    if m:
        session["org_id"] = m.org_id
        return int(m.org_id)

    base_name = current_user.email.split("@")[0]
    org_name = f"{base_name}-org"

    org = Organization.query.filter_by(name=org_name).first()
    if not org:
        org = Organization(name=org_name)
        db.session.add(org)
        db.session.commit()

    mem = Membership(
        user_id=current_user.id,
        org_id=org.id,
        role="admin" if getattr(current_user, "is_admin", False) else "member",
    )
    db.session.add(mem)
    db.session.commit()

    session["org_id"] = org.id
    return int(org.id)
