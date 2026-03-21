path = 'app/routes/billing.py'
with open(path, 'r') as f:
    content = f.read()

# Aggiungiamo un controllo all'inizio delle funzioni di checkout
check_logic = """
    from ..services.stripe_service import stripe_enabled
    if not stripe_enabled:
        from flask import flash, redirect, url_for
        flash("I pagamenti online saranno attivi a breve. Contatta l'assistenza per l'attivazione manuale.", "info")
        return redirect(url_for('scans.dashboard'))
"""

# Inseriamo il controllo nella funzione checkout (o quella che gestisce l'acquisto)
if 'def checkout' in content:
    content = content.replace('def checkout():', 'def checkout():' + check_logic)
    with open(path, 'w') as f:
        f.write(content)
    print("✅ Rotta Billing messa in standby di sicurezza!")
else:
    print("⚠️ Funzione checkout non trovata, controllo manuale suggerito.")
