from ..extensions import db


class Membership(db.Model):
    __tablename__ = "membership"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False, index=True)

    role = db.Column(db.String(20), nullable=False, default="member")  # member/admin
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
