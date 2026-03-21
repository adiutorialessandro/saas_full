import re

path = 'app/templates/dashboard.html'
try:
    with open(path, 'r') as f:
        content = f.read()

    # 1. Sostituisce la vecchia metrica con il nuovo Business Stability Score
    content = content.replace('s.triad_index', 's.overall_score')

    # 2. Rende i filtri "default" immuni ai valori Null (aggiungendo 'true' come secondo parametro)
    content = re.sub(r'\|\s*default\(([^,)]+)\)\s*\|', r'|default(\1, true)|', content)

    with open(path, 'w') as f:
        f.write(content)
        
    print("✅ Dashboard patchata! Ora usa il nuovo 'overall_score' ed è immune ai valori Null.")
except Exception as e:
    print(f"Errore: {e}")
