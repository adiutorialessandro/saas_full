"""
SaaS Full - Authentication Controller
Gestisce registrazione, login, logout e provisioning delle organizzazioni (tenant).
"""
import logging
from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db
from ..forms import RegisterForm, LoginForm
from ..models.user import User
from ..models.organization import Organization
from ..models.membership import Membership
from ..models.plan import Plan
from ..services.email_service import send_welcome_email

logger = logging.getLogger(__name__)
bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Registrazione nuovo utente e creazione automatica Tenant/Organization."""
    if current_user.is_authenticated:
        return redirect(url_for("scans.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if User.query.filter_by(email=email).first():
            logger.warning(f"Tentativo di registrazione duplicata per: {email}")
            flash("Questa email è già registrata. Effettua il login.", "warning")
            return render_template("auth/register.html", form=form)

        try:
            # 1. Creazione Utente
            user = User(email=email)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()

            # 2. Assegnazione Piano Base (se esistente)
            default_plan = Plan.query.first()
            plan_id = default_plan.id if default_plan else None

            # 3. Provisioning dell'Organizzazione
            org = Organization(name=f"Azienda di {email.split('@')[0]}", plan_id=plan_id)
            db.session.add(org)
            db.session.flush()

            # 4. Creazione Membership (Owner)
            membership = Membership(user_id=user.id, org_id=org.id, role="owner")
            db.session.add(membership)
            
            db.session.commit()
            logger.info(f"Nuovo utente e org creati con successo: {email} | Org ID: {org.id}")

            # 5. Invio Email di Benvenuto (Isolata per evitare crash su DB commit)
            try:
                send_welcome_email(user.email)
            except Exception as e:
                logger.error(f"Errore invio email di benvenuto a {user.email}: {str(e)}")

            # 6. Login automatico
            session["org_id"] = org.id
            login_user(user)

            flash("Account creato! Benvenuto nella tua nuova Dashboard.", "success")
            return redirect(url_for("scans.dashboard"))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Errore critico durante la registrazione: {str(e)}", exc_info=True)
            flash("Errore del server durante la registrazione. Riprova più tardi.", "danger")

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Autenticazione utente e iniezione org_id in sessione."""
    if current_user.is_authenticated:
        return redirect(url_for("scans.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(form.password.data):
            logger.warning(f"Tentativo di login fallito per email: {email}")
            flash("Credenziali non valide. Riprova.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user)
        logger.info(f"Login effettuato con successo: {email}")

        # Imposta l'org attiva nella sessione (Multi-tenancy)
        primary_org = user.primary_org_id()
        if primary_org:
            session["org_id"] = primary_org

        return redirect(url_for("scans.dashboard"))

    return render_template("auth/login.html", form=form)


@bp.get("/logout")
@login_required
def logout():
    """Termina la sessione dell'utente."""
    user_email = current_user.email
    logout_user()
    session.pop("org_id", None)
    
    logger.info(f"Logout effettuato: {user_email}")
    flash("Sei stato disconnesso in modo sicuro.", "info")
    
    return redirect(url_for("auth.login"))