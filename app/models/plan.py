from ..extensions import db


class Plan(db.Model):
    __tablename__ = "plan"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    scan_limit = db.Column(db.Integer, nullable=False, default=0)  # -1 = illimitato
    price_month = db.Column(db.Float, nullable=False, default=0.0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Billing dormant-ready
    stripe_price_id = db.Column(db.String(120), nullable=True)

    def __repr__(self) -> str:
        return f"<Plan {self.id} {self.name}>"