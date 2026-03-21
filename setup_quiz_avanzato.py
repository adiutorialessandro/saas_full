import re

print("🚀 Aggiornamento Quiz Strategico McKinsey in corso...")

# 1. Riscrivi forms.py completamente per inserire le nuove domande
forms_content = """from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, RadioField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, Regexp, EqualTo

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField("Ripeti Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Registrati")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Accedi")

class OnboardingForm(FlaskForm):
    tipologia_impresa = SelectField("Tipologia di impresa", choices=[('', 'Seleziona...'), ('Consulenza B2B', 'Consulenza B2B'), ('Retail', 'Retail'), ('Manifattura', 'Manifattura'), ('SaaS / Tech', 'SaaS / Tech'), ('Ho.Re.Ca.', 'Ho.Re.Ca.'), ('Immobiliare', 'Immobiliare'), ('Sanità / Studi medici', 'Sanità / Studi medici'), ('Generico', 'Altro (Generico)')], validators=[DataRequired()])
    modello = SelectField("Modello di business", choices=[('', 'Seleziona...'), ('B2B', 'B2B'), ('B2C', 'B2C'), ('SaaS', 'SaaS'), ('E-commerce', 'E-commerce'), ('Agenzia', 'Agenzia')], validators=[DataRequired()])
    dimensione = SelectField("Dimensione", choices=[('', 'Seleziona...'), ('Micro', '0-9 dipendenti'), ('Piccola', '10-49 dipendenti'), ('Media', '50-249 dipendenti'), ('Grande', 'Oltre 250 dipendenti')], validators=[DataRequired()])
    dipendenti = IntegerField("Dipendenti", validators=[DataRequired(), NumberRange(min=0)])
    area_geografica = StringField("Area geografica", validators=[DataRequired()])
    fatturato = StringField("Fatturato annuo (€)", validators=[DataRequired()])
    tipologia_clienti = SelectField("Tipologia clienti", choices=[('', 'Seleziona...'), ('PMI', 'PMI'), ('Corporate', 'Corporate'), ('Privati', 'Privati'), ('PA', 'PA')], validators=[DataRequired()])
    mese_riferimento = StringField("Mese (YYYY-MM)", validators=[DataRequired(), Regexp(r"^\d{4}-\d{2}$")])
    submit = SubmitField("Continua")

class EssentialDataForm(FlaskForm):
    cassa_attuale = FloatField("Cassa attuale (€)", validators=[Optional()])
    burn_mensile = FloatField("Burn Rate (€)", validators=[Optional()])
    incassi_mese = FloatField("Incassi mese (€)", validators=[Optional()])
    costi_fissi_mese = FloatField("Costi fissi (€)", validators=[Optional()])
    margine_lordo_pct = FloatField("Margine Lordo (%)", validators=[Optional(), NumberRange(0, 100)])
    leads_mese = FloatField("Leads (#)", validators=[Optional()])
    clienti_mese = FloatField("Nuovi Clienti (#)", validators=[Optional()])
    submit = SubmitField("Continua")

class QuizForm(FlaskForm):
    chiarezza_obiettivi = RadioField("Strategia e Obiettivi (Strategy)", choices=[('1.0', "Non c'è un piano scritto o cambia di continuo in base alle urgenze quotidiane."), ('0.5', "Esiste un piano generale discusso dal management, ma non è tradotto in obiettivi chiari per i dipendenti."), ('0.0', "La strategia è chiara, documentata e ogni team ha KPI specifici allineati all'obiettivo comune.")], validators=[DataRequired()])
    condivisione_valori = RadioField("Valori Condivisi (Shared Values)", choices=[('1.0', "La cultura è frammentata; i reparti lavorano a silos e spesso in conflitto di interessi."), ('0.5', "I valori sono noti formalmente, ma applicati in modo incostante a seconda del manager."), ('0.0', "C'è una forte identità condivisa: le decisioni quotidiane riflettono chiaramente i valori aziendali.")], validators=[DataRequired()])
    efficacia_sistemi = RadioField("Processi e Sistemi IT (Systems)", choices=[('1.0', "I processi sono manuali, non documentati e dipendono fortemente dalla memoria delle singole persone."), ('0.5', "Usiamo software base (es. Excel), ma i dati sono duplicati e l'integrazione è scarsa."), ('0.0', "I processi sono automatizzati e misurabili tramite sistemi IT integrati (ERP/CRM) utilizzati da tutti.")], validators=[DataRequired()])
    velocita_decisionale = RadioField("Struttura e Agilità (Structure)", choices=[('1.0', "Struttura molto rigida: ogni decisione richiede molteplici approvazioni rallentando l'esecuzione."), ('0.5', "Esiste una delega parziale, ma le decisioni formano ancora un collo di bottiglia sul vertice."), ('0.0', "Struttura agile: i team sono responsabilizzati e hanno autonomia decisionale sui propri obiettivi.")], validators=[DataRequired()])
    apertura_cambiamento = RadioField("Innovazione e Adattabilità (Skills)", choices=[('1.0', "Forte resistenza al cambiamento; le novità vengono viste come una distrazione dal lavoro abituale."), ('0.5', "Ci adattiamo quando è necessario, ma raramente siamo i primi a proporre innovazioni."), ('0.0', "L'innovazione è incoraggiata sistematicamente e abbiamo processi per testare rapidamente nuove idee.")], validators=[DataRequired()])
    apprendimento_errore = RadioField("Formazione e Competenze (Skills)", choices=[('1.0', "Non c'è budget né tempo dedicato alla formazione; le persone imparano solo 'facendo'."), ('0.5', "La formazione avviene solo su richiesta specifica o per adeguamenti normativi obbligatori."), ('0.0', "Esistono piani di sviluppo continui e l'aggiornamento delle competenze è un pilastro aziendale.")], validators=[DataRequired()])
    fiducia_leadership = RadioField("Stile di Leadership (Style)", choices=[('1.0', "Micromanagement: focus esclusivo sugli errori e rispetto rigido delle gerarchie."), ('0.5', "Transazionale: gestione basata su compiti e scadenze, con feedback occasionali."), ('0.0', "Trasformazionale: i leader fanno coaching, ispirano fiducia e supportano la crescita del team.")], validators=[DataRequired()])
    clima_team = RadioField("Clima e Morale (Staff)", choices=[('1.0', "Clima teso o demotivato, con alto turnover e difficoltà cronica ad attrarre talenti."), ('0.5', "Clima neutro; le persone fanno il loro dovere senza particolare entusiasmo o appartenenza."), ('0.0', "Clima eccellente: alto livello di engagement, basso turnover e forte senso di appartenenza.")], validators=[DataRequired()])
    submit = SubmitField("Genera Diagnostica")

class CreateOrganizationForm(FlaskForm):
    name = StringField("Nome azienda", validators=[DataRequired()])
    email = StringField("Email owner", validators=[DataRequired(), Email()])
    password = PasswordField("Password iniziale", validators=[DataRequired()])
    submit = SubmitField("Crea azienda")

class CreateOrgUserForm(FlaskForm):
    email = StringField("Email utente", validators=[DataRequired(), Email()])
    password = PasswordField("Password iniziale", validators=[DataRequired()])
    role = StringField("Ruolo", default="admin", validators=[DataRequired()])
    submit = SubmitField("Aggiungi utente")

class UpdateOrgUserRoleForm(FlaskForm):
    role = StringField("Ruolo", validators=[DataRequired()])
    submit = SubmitField("Aggiorna ruolo")

class ResetUserPasswordForm(FlaskForm):
    password = PasswordField("Nuova password", validators=[DataRequired()])
    password2 = PasswordField("Ripeti password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Aggiorna password")

class SectorBenchmarkForm(FlaskForm):
    sector_name = StringField("Nome Settore", validators=[DataRequired()])
    margine_lordo_target = FloatField("Target Margine (%)", validators=[DataRequired()])
    conversione_target = FloatField("Target Conversione (%)", validators=[DataRequired()])
    break_even_sano = FloatField("Break-Even Sano (ratio)", validators=[DataRequired()])
    runway_minima = IntegerField("Runway Minima (mesi)", validators=[DataRequired()])
    submit = SubmitField("Salva Benchmark")

class CreatePlanForm(FlaskForm):
    name = StringField("Nome piano", validators=[DataRequired()])
    scan_limit = IntegerField("Limite scansioni", validators=[DataRequired()])
    price_month = FloatField("Prezzo mensile", validators=[DataRequired()])
    submit = SubmitField("Crea piano")

class UpdateOrganizationPlanForm(FlaskForm):
    plan_id = SelectField("Piano", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Aggiorna piano")
"""
with open('app/forms.py', 'w') as f:
    f.write(forms_content)
print("✅ Form aggiornati con le nuove domande a risposta chiusa (3 scenari).")

# 2. Patch Orchestrator per leggere le nuove metriche di Rischio (1.0 = Peggiore, 0.0 = Migliore)
path_orch = 'app/services/analysis/strategy_orchestrator.py'
with open(path_orch, 'r') as f:
    content_orch = f.read()

new_func = """def _calculate_ohi_score(quiz: Dict[str, Any]) -> Dict[str, Any]:
    if not quiz:
        return {"score": 50, "status": "Neutral", "insights": ["Dati qualitativi non disponibili."]}
    
    scores = []
    for v in quiz.values():
        try:
            val = float(v)
            if val <= 1.0:
                scores.append((1.0 - val) * 100)
            else:
                scores.append(val * 20)
        except: pass
    
    avg = (sum(scores) / len(scores)) if scores else 50
    
    status = "Elite" if avg >= 80 else "Stable" if avg >= 60 else "Fragile"
    
    insights = []
    if float(quiz.get('chiarezza_obiettivi', 0)) >= 0.5: insights.append("Mancanza di direzione strategica chiara o condivisa.")
    if float(quiz.get('velocita_decisionale', 0)) >= 0.5: insights.append("Eccessiva burocrazia interna e colli di bottiglia decisionali.")
    if float(quiz.get('fiducia_leadership', 1)) <= 0.5: insights.append("Leadership forte e riconosciuta come punto di riferimento dal team.")
    
    return {
        "score": round(avg),
        "status": status,
        "insights": insights[:3] if insights else ["La cultura aziendale appare allineata e bilanciata."]
    }"""

content_orch = re.sub(r'def _calculate_ohi_score\(.*?(?=def _calculate_value_chain)', new_func + '\n\n', content_orch, flags=re.DOTALL)

with open(path_orch, 'w') as f:
    f.write(content_orch)
print("✅ Orchestratore Strategico allineato al nuovo formato risposte.")
print("🎉 CONFIGURAZIONE BACKEND COMPLETATA!")
