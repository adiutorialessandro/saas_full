import re

path = 'app/models/user.py'
with open(path, 'r') as f:
    content = f.read()

# Definiamo la proprietà current_org che cerca la prima organizzazione disponibile per l'utente
current_org_property = """
    @property
    def current_org(self):
        from app.models.membership import Membership
        from app.models.organization import Organization
        # Prende la prima membership dell'utente e restituisce l'organizzazione collegata
        member = Membership.query.filter_by(user_id=self.id).first()
        if member:
            return Organization.query.get(member.org_id)
        return None
"""

# Inseriamo la proprietà all'interno della classe User
if 'def current_org(self):' not in content:
    # La inseriamo prima dell'ultimo metodo o alla fine della classe
    content = content.rstrip()
    if content.endswith(':'): # Se la classe è vuota o finisce male
        content += current_org_property
    else:
        # Cerchiamo l'ultima riga della classe e incolliamo
        content += current_org_property

    with open(path, 'w') as f:
        f.write(content)
    print("✅ Proprietà 'current_org' aggiunta al modello User!")
else:
    print("⚠️ La proprietà esisteva già.")
