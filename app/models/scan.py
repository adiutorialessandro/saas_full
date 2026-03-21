"""
SaaS Full - Scan Model
Rappresenta un singolo report/analisi generata per un'azienda.
"""
from ..extensions import db

class Scan(db.Model):
    __tablename__ = "scan"

    id = db.Column(db.Integer, primary_key=True)

    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    settore = db.Column(db.String(100), nullable=False)
    modello = db.Column(db.String(100), nullable=False)
    mese_riferimento = db.Column(db.String(7), nullable=False)  # Formato YYYY-MM

    # Output del motore strategico
    report_json = db.Column(db.Text, nullable=False)
    
    # Dati grezzi di input (Utili per Machine Learning o ricalcolo report futuri)
    raw_data = db.Column(db.Text, nullable=True)

    # --- Triad metrics snapshot (Per grafici storici nella Dashboard) ---
    triad_index = db.Column(db.Float)
    finance_score = db.Column(db.Float)
    sales_score = db.Column(db.Float)
    ops_score = db.Column(db.Float)
    
    def __repr__(self) -> str:
        return f"<Scan {self.id} | Org: {self.org_id}>"