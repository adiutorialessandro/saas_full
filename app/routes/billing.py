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


def get_user_org(org_id: int):
    membership = Membership.query.filter_by(user_id=current_user.id, org_id=org_id).first()
    if not membership:
        return None
    return Organization.query.get(org_id)


@bp.get("/status")
@login_required
def status():
    return jsonify({
        "billing_enabled": bool(current_app.config.get("BILLING_ENABLED", False))
    })


@bp.get("/checkout/<int:org_id>/<int:plan_id>")
@login_required
def checkout(org_id: int, plan_id: int):
    if not stripe_enabled():
        flash("Billing non ancora attivo.")
        return redirect(url_for("admin.organization_detail", org_id=org_id))

    org = get_user_org(org_id)
    if not org:
        return "Forbidden", 403

    plan = Plan.query.get_or_404(plan_id)

    if not plan.stripe_price_id:
        flash("Il piano non è collegato a Stripe.")
        return redirect(url_for("admin.organization_detail", org_id=org.id))

    session = create_checkout_session(
        customer_email=current_user.email,
        price_id=plan.stripe_price_id,
        success_url=current_app.config.get("STRIPE_CHECKOUT_SUCCESS_URL") or url_for(
            "admin.organization_detail", org_id=org.id, _external=True
        ),
        cancel_url=current_app.config.get("STRIPE_CHECKOUT_CANCEL_URL") or url_for(
            "admin.organization_detail", org_id=org.id, _external=True
        ),
    )

    return redirect(session.url, code=303)


@bp.get("/portal/<int:org_id>")
@login_required
def portal(org_id: int):
    if not stripe_enabled():
        flash("Billing non ancora attivo.")
        return redirect(url_for("admin.organization_detail", org_id=org_id))

    org = get_user_org(org_id)
    if not org:
        return "Forbidden", 403

    if not org.stripe_customer_id:
        flash("Nessun customer Stripe associato.")
        return redirect(url_for("admin.organization_detail", org_id=org.id))

    session = create_portal_session(
        customer_id=org.stripe_customer_id,
        return_url=current_app.config.get("STRIPE_PORTAL_RETURN_URL") or url_for(
            "admin.organization_detail", org_id=org.id, _external=True
        ),
    )

    return redirect(session.url, code=303)


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

    if event_type == "checkout.session.completed":
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        customer_email = data.get("customer_details", {}).get("email")

        if customer_email:
            user = User.query.filter_by(email=customer_email.lower()).first()
            if user:
                membership = Membership.query.filter_by(user_id=user.id).first()
                if membership:
                    org = Organization.query.get(membership.org_id)
                    if org:
                        org.stripe_customer_id = customer_id
                        org.stripe_subscription_id = subscription_id
                        org.billing_status = "active"
                        db.session.commit()

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

    elif event_type == "customer.subscription.deleted":
        subscription_id = data.get("id")
        org = Organization.query.filter_by(stripe_subscription_id=subscription_id).first()
        if org:
            org.billing_status = "canceled"
            db.session.commit()

    return jsonify({"received": True}), 200
@bp.route('/pricing')
@login_required
def pricing():
    from app.models.plan import Plan
    plans = Plan.query.order_by(Plan.price_month).all()
    return render_template('pricing.html', plans=plans)

# Stripe Standby Mode: sab 21 mar 2026 18:56:06 CET
