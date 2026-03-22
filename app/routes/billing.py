from datetime import datetime, timezone
from flask import Blueprint, current_app, flash, redirect, request, url_for, jsonify
from flask_login import login_required, current_user

from ..extensions import db
from ..models.organization import Organization
from ..models.plan import Plan
from ..models.membership import Membership
from ..models.user import User
from ..services.stripe_service import (
    stripe_enabled,
    create_checkout_session,
    create_portal_session,
    construct_webhook_event,
)

bp = Blueprint("billing", __name__, url_prefix="/billing")

def get_user_org():
    """Recupera l'azienda di cui l'utente loggato è owner"""
    membership = Membership.query.filter_by(user_id=current_user.id, role='owner').first()
    if not membership:
        return None
    return Organization.query.get(membership.org_id)


@bp.get("/status")
@login_required
def status():
    return jsonify({
        "billing_enabled": bool(current_app.config.get("BILLING_ENABLED", False))
    })


# FIX: Ora riceve solo plan_id dal bottone del pricing
@bp.get("/checkout/<int:plan_id>")
@login_required
def checkout(plan_id: int):
    # 1. Recupera l'azienda dell'utente
    org = get_user_org()
    if not org:
        flash("Devi essere l'Owner di un'azienda per gestire l'abbonamento.", "warning")
        return redirect(url_for("wizard.step1"))

    plan = Plan.query.get_or_404(plan_id)

    # 2. FIX: Se è il piano GRATIS, lo attiviamo subito senza passare da Stripe
    if plan.price_month == 0:
        org.plan_id = plan.id
        org.billing_status = 'active'
        db.session.commit()
        flash(f"Piano {plan.name} attivato! Inizia la tua diagnostica.", "success")
        return redirect(url_for("wizard.step1"))

    # 3. Controlli Stripe
    if not stripe_enabled():
        flash("I pagamenti non sono ancora attivi. Contatta l'assistenza.", "info")
        return redirect(url_for("pricing"))

    if not plan.stripe_price_id:
        flash("Errore: Il piano non è collegato a Stripe.", "danger")
        return redirect(url_for("pricing"))

    # FIX: Se paga o annulla, lo rimandiamo al Wizard o al Pricing (non all'Admin!)
    session = create_checkout_session(
        customer_email=current_user.email,
        price_id=plan.stripe_price_id,
        success_url=url_for("wizard.step1", _external=True),
        cancel_url=url_for("pricing", _external=True)
    )

    # Salviamo provvisoriamente il piano scelto, così il webhook sa cosa attivare
    org.plan_id = plan.id
    db.session.commit()

    return redirect(session.url, code=303)


@bp.get("/portal")
@login_required
def portal():
    """Apre il portale clienti di Stripe per far scaricare le fatture o disdire"""
    org = get_user_org()
    if not org:
        return "Forbidden", 403

    if not stripe_enabled() or not org.stripe_customer_id:
        flash("Nessun abbonamento Stripe attivo trovato.")
        return redirect(url_for("wizard.step1"))

    session = create_portal_session(
        customer_id=org.stripe_customer_id,
        return_url=url_for("wizard.step1", _external=True),
    )

    return redirect(session.url, code=303)


# ==========================================
# WEBHOOK STRIPE (Lavora in background)
# ==========================================
@bp.post("/webhook")
def webhook():
    if not stripe_enabled():
        return jsonify({"ok": True, "message": "billing disabled"}), 200

    payload = request.data
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = construct_webhook_event(payload, sig_header)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    # 1. Checkout Completato
    if event_type == "checkout.session.completed":
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        customer_email = data.get("customer_details", {}).get("email")

        if customer_email:
            user = User.query.filter_by(email=customer_email.lower()).first()
            if user:
                membership = Membership.query.filter_by(user_id=user.id, role='owner').first()
                if membership:
                    org = Organization.query.get(membership.org_id)
                    if org:
                        org.stripe_customer_id = customer_id
                        org.stripe_subscription_id = subscription_id
                        org.billing_status = "active"
                        db.session.commit()

    # 2. Abbonamento Aggiornato (Rinnovo mensile)
    elif event_type == "customer.subscription.updated":
        subscription_id = data.get("id")
        status = data.get("status")
        customer_id = data.get("customer")

        period_end_ts = data.get("current_period_end")
        period_end = None
        if period_end_ts:
            try:
                period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc).replace(tzinfo=None)
            except Exception:
                period_end = None

        org = Organization.query.filter_by(stripe_subscription_id=subscription_id).first()
        if org:
            org.billing_status = status
            org.stripe_customer_id = customer_id
            org.current_period_end = period_end
            db.session.commit()

    # 3. Abbonamento Cancellato o Scaduto
    elif event_type == "customer.subscription.deleted":
        subscription_id = data.get("id")
        org = Organization.query.filter_by(stripe_subscription_id=subscription_id).first()
        if org:
            org.billing_status = "canceled"
            # Opzionale: Fallback automatico al piano "Starter" quando scade
            # default_plan = Plan.query.filter_by(name="Starter").first()
            # if default_plan: org.plan_id = default_plan.id
            db.session.commit()

    return jsonify({"received": True}), 200