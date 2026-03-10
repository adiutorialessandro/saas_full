from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db
from ..forms import RegisterForm, LoginForm
from ..models.user import User
from ..models.organization import Organization
from ..models.membership import Membership
from ..models.plan import Plan
from ..services.email_service import send_welcome_email

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("scans.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if User.query.filter_by(email=email).first():
            flash("Email già registrata.")
            return render_template("auth/register.html", form=form)

        u = User(email=email)
        u.set_password(form.password.data)

        # Assegna automaticamente il piano base alla nuova azienda
        default_plan = Plan.query.first()
        plan_id = default_plan.id if default_plan else None

        org = Organization(name="La mia azienda", plan_id=plan_id)
        db.session.add(org)
        db.session.flush()

        db.session.add(u)
        db.session.flush()

        m = Membership(user_id=u.id, org_id=org.id, role="owner")
        db.session.add(m)
        db.session.commit()

        # Protezione anti-crash per le email
        try:
            send_welcome_email(u.email)
        except Exception as e:
            print(f"Server Email non configurato (ignorato): {e}")

        session["org_id"] = org.id
        login_user(u)

        flash("Account creato! Benvenuto nella dashboard.")
        return redirect(url_for("scans.dashboard"))

    return render_template("auth/register.html", form=form)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("scans.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        u = User.query.filter_by(email=email).first()

        if not u or not u.check_password(form.password.data):
            flash("Credenziali non valide.")
            return render_template("auth/login.html", form=form)

        login_user(u)

        if u.primary_org_id():
            session["org_id"] = u.primary_org_id()

        return redirect(url_for("scans.dashboard"))

    return render_template("auth/login.html", form=form)

@bp.get("/logout")
@login_required
def logout():
    logout_user()
    session.pop("org_id", None)
    flash("Logout effettuato.")
    return redirect(url_for("auth.login"))
