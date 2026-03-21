import re

path = 'app/templates/admin/index.html'
try:
    with open(path, 'r') as f:
        content = f.read()

    # Sostituiamo il vecchio nome della rotta con quello nuovo e corretto
    content = content.replace("url_for('admin.list_benchmarks')", "url_for('admin.benchmarks')")

    with open(path, 'w') as f:
        f.write(content)
        
    print("✅ Link dei Benchmark corretto nella Dashboard Admin!")
except Exception as e:
    print(f"Errore durante l'aggiornamento: {e}")
