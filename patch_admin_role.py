import re

path = 'app/routes/admin.py'
try:
    with open(path, 'r') as f:
        content = f.read()

    # 1. Correggiamo il decoratore admin_required per usare is_admin
    content = content.replace('if current_user.role != "admin":', 'if not getattr(current_user, "is_admin", False):')

    # 2. Rimuoviamo il parametro inesistente 'role' quando creiamo nuovi utenti nel DB
    content = content.replace(', role="user"', '')
    
    with open(path, 'w') as f:
        f.write(content)
        
    print("✅ File admin.py patchato! Ora utilizza correttamente 'is_admin' al posto di 'role'.")
except Exception as e:
    print(f"Errore durante l'aggiornamento: {e}")
