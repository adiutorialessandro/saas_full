import smtplib
from email.message import EmailMessage
from typing import Optional

from flask import current_app, render_template


def email_enabled() -> bool:
    return bool(current_app.config.get("EMAIL_ENABLED", False))


def _build_message(to_email: str, subject: str, text_body: str, html_body: Optional[str] = None) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config.get("EMAIL_FROM")
    msg["To"] = to_email
    msg.set_content(text_body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    return msg


def send_email(to_email: str, subject: str, text_body: str, html_template: Optional[str] = None, **context) -> bool:
    if not email_enabled():
        current_app.logger.info(
            "EMAIL DISABLED | to=%s | subject=%s | body=%s",
            to_email,
            subject,
            text_body[:200],
        )
        return False

    html_body = None
    if html_template:
        html_body = render_template(html_template, **context)

    msg = _build_message(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )

    host = current_app.config.get("SMTP_HOST")
    port = current_app.config.get("SMTP_PORT")
    username = current_app.config.get("SMTP_USERNAME")
    password = current_app.config.get("SMTP_PASSWORD")
    use_tls = current_app.config.get("SMTP_USE_TLS", True)

    if not host:
        current_app.logger.warning("SMTP_HOST non configurato.")
        return False

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()

            if username and password:
                server.login(username, password)

            server.send_message(msg)

        current_app.logger.info("Email inviata a %s con subject '%s'", to_email, subject)
        return True

    except Exception as exc:
        current_app.logger.exception("Errore invio email a %s: %s", to_email, exc)
        return False


def send_welcome_email(user_email: str) -> bool:
    text_body = (
        "Benvenuto su SaaS Full.\n\n"
        "Il tuo account è stato creato con successo.\n"
        "Ora puoi accedere alla piattaforma e iniziare a lavorare sui tuoi scan."
    )
    return send_email(
        to_email=user_email,
        subject="Benvenuto su SaaS Full",
        text_body=text_body,
        html_template="emails/welcome.html",
        user_email=user_email,
    )


def send_client_created_email(user_email: str, org_name: str) -> bool:
    text_body = (
        f"La tua azienda '{org_name}' è stata creata con successo su SaaS Full.\n\n"
        "Puoi accedere alla piattaforma con le tue credenziali."
    )
    return send_email(
        to_email=user_email,
        subject="Azienda creata con successo",
        text_body=text_body,
        html_template="emails/client_created.html",
        user_email=user_email,
        org_name=org_name,
    )


def send_user_invite_email(user_email: str, org_name: str, role: str) -> bool:
    text_body = (
        f"Sei stato aggiunto all'azienda '{org_name}' su SaaS Full.\n\n"
        f"Ruolo assegnato: {role}\n"
        "Accedi con le credenziali ricevute dall'amministratore."
    )
    return send_email(
        to_email=user_email,
        subject="Invito a SaaS Full",
        text_body=text_body,
        html_template="emails/invite_user.html",
        user_email=user_email,
        org_name=org_name,
        role=role,
    )


def send_password_reset_notice_email(user_email: str, org_name: str) -> bool:
    text_body = (
        f"La password del tuo account per l'azienda '{org_name}' è stata aggiornata.\n\n"
        "Se non riconosci questa modifica, contatta l'amministratore."
    )
    return send_email(
        to_email=user_email,
        subject="Password aggiornata",
        text_body=text_body,
        html_template="emails/password_reset_notice.html",
        user_email=user_email,
        org_name=org_name,
    )


def send_plan_notice_email(user_email: str, org_name: str, plan_name: str, message: str) -> bool:
    text_body = (
        f"Azienda: {org_name}\n"
        f"Piano: {plan_name}\n\n"
        f"{message}"
    )
    return send_email(
        to_email=user_email,
        subject="Aggiornamento piano SaaS Full",
        text_body=text_body,
        html_template="emails/plan_notice.html",
        user_email=user_email,
        org_name=org_name,
        plan_name=plan_name,
        message=message,
    )