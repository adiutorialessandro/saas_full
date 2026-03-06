import secrets
from ..extensions import db


class Invite(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False, index=True)

    role = db.Column(db.String(20), nullable=False, server_default="member")  # member|admin
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    used_at = db.Column(db.DateTime, nullable=True)
    used_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    @staticmethod
    def new_token() -> str:
        return secrets.token_urlsafe(32)
