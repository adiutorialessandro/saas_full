from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.plan import Plan

app = create_app()
with app.app_context():
    email = "admin@saasfull.it" # <--- Puoi cambiare questa
    password = "AdminPassword2026!" # <--- E questa
    
    # Controlla se l'utente esiste già
    user = User.query.filter_by(email=email).first()
    if not user:
        # 1. Crea l'utente Admin
        user = User(email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        # 2. Crea un'organizzazione di test per l'admin
        plan = Plan.query.filter_by(name="Enterprise").first()
        org = Organization(name="Admin HQ", plan_id=plan.id if plan else None)
        db.session.add(org)
        db.session.flush()
        
        # 3. Lega l'admin all'organizzazione come Owner
        membership = Membership(user_id=user.id, org_id=org.id, role="owner")
        db.session.add(membership)
        
        db.session.commit()
        print(f"✅ Admin creato con successo!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
    else:
        print("⚠️ L'utente admin esiste già.")
