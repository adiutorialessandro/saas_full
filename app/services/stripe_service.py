import stripe
from flask import current_app


def stripe_enabled() -> bool:
    return bool(current_app.config.get("BILLING_ENABLED", False))


def configure_stripe() -> None:
    stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY", "")


def create_checkout_session(*, customer_email: str, price_id: str, success_url: str, cancel_url: str):
    if not stripe_enabled():
        raise RuntimeError("Billing disabilitato")

    configure_stripe()

    return stripe.checkout.Session.create(
        mode="subscription",
        customer_email=customer_email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )


def create_portal_session(*, customer_id: str, return_url: str):
    if not stripe_enabled():
        raise RuntimeError("Billing disabilitato")

    configure_stripe()

    return stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )


def construct_webhook_event(payload: bytes, sig_header: str):
    if not stripe_enabled():
        raise RuntimeError("Billing disabilitato")

    configure_stripe()
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET", "")
    return stripe.Webhook.construct_event(payload, sig_header, secret)