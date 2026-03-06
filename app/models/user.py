from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # relationship (tabella membership -> user.id)
    memberships = db.relationship("Membership", backref="user", lazy=True)

    def set_password(self, pwd: str) -> None:
        self.password_hash = generate_password_hash(pwd, method="pbkdf2:sha256")

    def check_password(self, pwd: str) -> bool:
        return check_password_hash(self.password_hash, pwd)

    def primary_org_id(self) -> int:
        """
        Compatibilità: ritorna l'org_id della prima membership (se presente).
        """
        if not self.memberships:
            return 0
        return int(self.memberships[0].org_id or 0)
