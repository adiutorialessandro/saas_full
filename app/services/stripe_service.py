import stripe
import os

# FORZATURA: Stripe disattivato finché non deciderai di riattivarlo
stripe_enabled = False

def create_checkout_session(*args, **kwargs):
    return None

def create_portal_session(*args, **kwargs):
    return None

def construct_webhook_event(*args, **kwargs):
    return None
