from ..extensions import db


class Organization(db.Model):
    __tablename__ = "organization"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"), nullable=True, index=True)

    # Billing dormant-ready
    stripe_customer_id = db.Column(db.String(120), nullable=True, index=True)
    stripe_subscription_id = db.Column(db.String(120), nullable=True, index=True)
    billing_status = db.Column(db.String(50), nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)

    plan = db.relationship("Plan", backref="organizations", lazy=True)

    def __repr__(self) -> str:
        return f"<Organization {self.id} {self.name}>"