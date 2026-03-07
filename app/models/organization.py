from ..extensions import db


class Organization(db.Model):
    __tablename__ = "organization"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"), nullable=True, index=True)

    plan = db.relationship("Plan", backref="organizations", lazy=True)