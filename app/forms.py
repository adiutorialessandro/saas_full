from flask_wtf import FlaskForm
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
    # Lasciamo il choices vuoto di base, lo riempiamo dinamicamente nell'__init__
    tipologia_impresa = SelectField("Tipologia di impresa", choices=[], validators=[DataRequired()])
    modello = SelectField("Modello di business", choices=[('', 'Seleziona...'), ('B2B', 'B2B'), ('B2C', 'B2C'), ('SaaS', 'SaaS'), ('E-commerce', 'E-commerce'), ('Agenzia', 'Agenzia')], validators=[DataRequired()])
    dimensione = SelectField("Dimensione", choices=[('', 'Seleziona...'), ('Micro', '0-9 dipendenti'), ('Piccola', '10-49 dipendenti'), ('Media', '50-249 dipendenti'), ('Grande', 'Oltre 250 dipendenti')], validators=[DataRequired()])
    dipendenti = IntegerField("Dipendenti", validators=[DataRequired(), NumberRange(min=0)])
    area_geografica = StringField("Area geografica", validators=[DataRequired()])
    fatturato = StringField("Fatturato annuo (€)", validators=[DataRequired()])
    tipologia_clienti = SelectField("Tipologia clienti", choices=[('', 'Seleziona...'), ('PMI', 'PMI'), ('Corporate', 'Corporate'), ('Privati', 'Privati'), ('PA', 'PA')], validators=[DataRequired()])
    mese_riferimento = StringField("Mese (YYYY-MM)", validators=[DataRequired(), Regexp(r"^\d{4}-\d{2}$")])
    submit = SubmitField("Continua")

    # METODO DINAMICO: Popola il menu a tendina dal Database
    def __init__(self, *args, **kwargs):
        super(OnboardingForm, self).__init__(*args, **kwargs)
        
        # IMPORT CORRETTO DEL MODELLO
        from app.models.benchmark import SectorBenchmark 
        
        try:
            benchmarks_salvati = SectorBenchmark.query.all()
            # CAMPO CORRETTO: sector_name invece di nome_settore
            scelte_dinamiche = [('', 'Seleziona...')] + [(b.sector_name, b.sector_name) for b in benchmarks_salvati]
            
            # Assicuriamoci che l'opzione Generico ci sia sempre
            if not any(scelta[0] == 'Generico' for scelta in scelte_dinamiche):
                scelte_dinamiche.append(('Generico', 'Altro (Generico)'))
                
            self.tipologia_impresa.choices = scelte_dinamiche
        except Exception:
            # Fallback in caso di database non ancora inizializzato
            self.tipologia_impresa.choices = [('', 'Seleziona...'), ('Generico', 'Altro (Generico)')]

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

class RetailDataForm(FlaskForm):
    ricavi_dichiarati = FloatField("Ricavi Dichiarati (Annui €)", validators=[DataRequired()])
    incassi_reali = FloatField("Incassi Reali Stimati (Annui €)", validators=[DataRequired()])
    costi_personale = FloatField("Costi Personale (Annui €)", validators=[DataRequired()])
    costi_struttura = FloatField("Costi Struttura (Annui €)", validators=[DataRequired()])
    costi_prodotti = FloatField("Costi Prodotti e Materiali (Annui €)", validators=[DataRequired()])
    compenso_titolare = FloatField("Compenso Titolare (Annuo €)", validators=[Optional()])
    ticket_medio = FloatField("Ticket Medio (€)", validators=[Optional()])
    clienti_mese = IntegerField("Clienti al Mese", validators=[Optional()])
    submit = SubmitField("Genera Analisi Local Business")