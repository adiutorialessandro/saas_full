import logging
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)

def _get_safe_sender():
    """Recupera il mittente in sicurezza. Se manca, usa un fallback."""
    return current_app.config.get("MAIL_DEFAULT_SENDER") or "SaaS Full Advisory <a.a.personalstudio@gmail.com>"


def send_welcome_email(user_email):
    """Invia un'email di benvenuto in HTML al nuovo utente."""
    try:
        msg = Message(
            subject="🚀 Benvenuto in SaaS Full - Inizia la tua analisi!",
            sender=_get_safe_sender(),  # <-- Sicurezza anti-crash
            recipients=[user_email]
        )
        
        # Recuperiamo l'URL base del sito
        base_url = current_app.config.get("APP_BASE_URL", "http://127.0.0.1:5000")
        login_url = f"{base_url}/auth/login"
        
        # Compiliamo il template HTML inserendo le variabili
        msg.html = render_template(
            "emails/welcome.html", 
            login_url=login_url
        )
        
        mail.send(msg)
        logger.info(f"Email di benvenuto inviata con successo a {user_email}")
        return True
        
    except Exception as e:
        logger.error(f"Impossibile inviare email di benvenuto a {user_email}: {str(e)}")
        return False


def send_admin_creation_email(user_email, raw_password):
    """Invia le credenziali quando l'admin crea un'azienda manualmente."""
    try:
        msg = Message(
            subject="🔑 Il tuo account SaaS Full è pronto!",
            sender=_get_safe_sender(),  # <-- Sicurezza anti-crash
            recipients=[user_email]
        )
        
        base_url = current_app.config.get("APP_BASE_URL", "http://127.0.0.1:5000")
        
        msg.html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
            <h2 style="color: #1a365d;">Benvenuto in SaaS Full!</h2>
            <p>Il tuo spazio di lavoro strategico è stato attivato dal nostro team.</p>
            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0;"><b>Email:</b> {user_email}</p>
                <p style="margin: 5px 0 0 0;"><b>Password:</b> {raw_password}</p>
            </div>
            <p>Ti consigliamo di accedere e cambiare la password il prima possibile.</p>
            <a href="{base_url}/auth/login" style="display: inline-block; background: #3182ce; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 10px;">Accedi alla Dashboard</a>
        </div>
        """
        mail.send(msg)
        logger.info(f"Email credenziali inviata a {user_email}")
        return True
    except Exception as e:
        logger.error(f"Errore invio email credenziali a {user_email}: {str(e)}")
        return False


def send_plan_change_email(user_email, plan_name):
    """Avvisa l'utente che il suo piano è stato aggiornato."""
    try:
        msg = Message(
            subject="🚀 Upgrade: Il tuo piano SaaS Full è stato aggiornato",
            sender=_get_safe_sender(),  # <-- Sicurezza anti-crash
            recipients=[user_email]
        )
        
        base_url = current_app.config.get("APP_BASE_URL", "http://127.0.0.1:5000")
        
        msg.html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
            <h2 style="color: #10b981;">Piano Aggiornato!</h2>
            <p>Ottime notizie! Il tuo piano è stato aggiornato con successo a <b>{plan_name}</b>.</p>
            <p>Ora hai accesso ai nuovi limiti operativi previsti dal tuo abbonamento.</p>
            <a href="{base_url}/auth/login" style="display: inline-block; background: #3182ce; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 10px;">Vai alla Dashboard</a>
        </div>
        """
        mail.send(msg)
        logger.info(f"Email cambio piano inviata a {user_email}")
        return True
    except Exception as e:
        logger.error(f"Errore invio email piano a {user_email}: {str(e)}")
        return False