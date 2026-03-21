import re

path = 'app/templates/quiz.html'
with open(path, 'r') as f:
    content = f.read()

# Il codice della schermata di caricamento e lo script JS
loading_ui = """
    <div id="loading-overlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.98); z-index: 9999; flex-direction: column; justify-content: center; align-items: center; color: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; backdrop-filter: blur(10px);">
        
        <div style="position: relative; width: 100px; height: 100px; margin-bottom: 40px;">
            <i class="fas fa-circle-notch fa-spin" style="font-size: 4rem; color: #38bdf8; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);"></i>
            <i class="fas fa-brain" style="font-size: 1.5rem; color: white; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);"></i>
        </div>
        
        <h2 id="loading-text" style="font-size: 1.8rem; font-weight: 800; margin-bottom: 15px; letter-spacing: -0.5px; text-align: center;">Inizializzazione Motore Algoritmico...</h2>
        <p style="color: #94a3b8; font-size: 1rem; margin-bottom: 30px; text-align: center; max-width: 400px;">Attendi mentre i nostri modelli analizzano i tuoi dati e costruiscono il piano d'azione.</p>
        
        <div style="width: 350px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden;">
            <div id="progress-bar" style="width: 5%; height: 100%; background: linear-gradient(90deg, #38bdf8, #8b5cf6); transition: width 0.5s ease-out; box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);"></div>
        </div>
        
        <p style="color: #475569; margin-top: 25px; font-size: 0.85rem; font-family: monospace;">Elaborazione sicura end-to-end</p>
    </div>

    <script>
        document.querySelector('form').addEventListener('submit', function(e) {
            // Mostra l'overlay
            document.getElementById('loading-overlay').style.display = 'flex';
            
            // Le frasi ad effetto che cambieranno ogni 1.5 secondi
            const texts = [
                "Calcolo del Business Stability Score...",
                "Analisi Modelli Finanziari ed EBITDA Gap...",
                "Esecuzione Stress Test di Cassa...",
                "Valutazione Framework McKinsey 7S...",
                "Connessione al Cluster OpenAI...",
                "Generazione Executive Memo in corso...",
                "Impaginazione Dossier Strategico...",
                "Quasi pronto..."
            ];
            
            let i = 0;
            const textEl = document.getElementById('loading-text');
            const barEl = document.getElementById('progress-bar');
            
            // Aggiorna testo e barra progressivamente
            const interval = setInterval(() => {
                i++;
                if (i < texts.length) {
                    textEl.innerText = texts[i];
                    barEl.style.width = ((i + 1) * 100 / texts.length) + '%';
                } else {
                    clearInterval(interval);
                    barEl.style.width = '100%';
                }
            }, 1500); // Cambia frase ogni 1.5 secondi
        });
    </script>
{% endblock %}
"""

# Sostituiamo il tag di chiusura con il nuovo blocco
if "loading-overlay" not in content:
    content = content.replace("{% endblock %}", loading_ui)
    with open(path, 'w') as f:
        f.write(content)
    print("✅ Effetto Wow applicato con successo al Wizard!")
else:
    print("⚠️ L'animazione era già presente nel file.")
