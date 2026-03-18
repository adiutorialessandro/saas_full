from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership

app = create_app()

def create_admin_user(email, password):
    with app.app_context():
        # 1. Gestione Utente (basato su app/models/user.py)
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"L'utente {email} esiste già. Aggiorno password e permessi...")
            user.set_password(password)
            user.is_admin = True
        else:
            print(f"Creazione nuovo utente: {email}")
            user = User(
                email=email,
                is_admin=True
            )
            user.set_password(password)
            db.session.add(user)
        
        # Flush per ottenere l'ID dell'utente prima del commit
        db.session.flush()

        # 2. Gestione Organizzazione (basato su app/models/organization.py)
        org = Organization.query.filter_by(name="Admin Organization").first()
        if not org:
            print("Creazione organizzazione di default...")
            org = Organization(name="Admin Organization")
            db.session.add(org)
            db.session.flush()

        # 3. Gestione Membership (corretto con 'org_id')
        # Il tuo modello User usa .org_id per le membership
        membership = Membership.query.filter_by(user_id=user.id, org_id=org.id).first()
        if not membership:
            print(f"Assegnazione utente all'organizzazione {org.name}...")
            membership = Membership(
                user_id=user.id,
                org_id=org.id,
                role='admin'
            )
            db.session.add(membership)
        else:
            membership.role = 'admin'
        
        try:
            db.session.commit()
            print(f"\nSUCCESSO! Credenziali create:")
            print(f"Email: {email}")
            print(f"Password: {password}")
        except Exception as e:
            db.session.rollback()
            print(f"Errore durante il salvataggio: {e}")

if __name__ == "__main__":
    # Puoi cambiare la password qui sotto prima di eseguire
    create_admin_user("admin@saasfull.com", "123456")