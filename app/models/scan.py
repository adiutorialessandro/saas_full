from ..extensions import db


class Scan(db.Model):
    __tablename__ = "scan"

    id = db.Column(db.Integer, primary_key=True)

    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    settore = db.Column(db.String(100), nullable=False)
    modello = db.Column(db.String(100), nullable=False)
    mese_riferimento = db.Column(db.String(7), nullable=False)  # YYYY-MM

    report_json = db.Column(db.Text, nullable=False)

    # --- Triad metrics snapshot (used for dashboard trend and analysis history) ---
    triad_index = db.Column(db.Float)
    finance_score = db.Column(db.Float)
    sales_score = db.Column(db.Float)
    ops_score = db.Column(db.Float)
    
    # --- Soft Delete flag ---
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)