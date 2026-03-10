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
    tipologia_impresa = SelectField(
        "Tipologia di impresa",
        choices=[('', 'Seleziona...'), ('Consulenza B2B', 'Consulenza B2B'), ('Retail', 'Retail'), ('Manifattura', 'Manifattura'), ('SaaS / Tech', 'SaaS / Tech'), ('Ho.Re.Ca.', 'Ho.Re.Ca.'), ('Immobiliare', 'Immobiliare'), ('Sanità / Studi medici', 'Sanità / Studi medici'), ('Generico', 'Altro (Generico)')],
        validators=[DataRequired()], description="Seleziona il mercato principale per confrontare i tuoi dati con le medie di settore."
    )
    modello = SelectField(
        "Modello di business",
        choices=[('', 'Seleziona...'), ('B2B', 'B2B (Business to Business)'), ('B2C', 'B2C (Business to Consumer)'), ('SaaS', 'SaaS (Software)'), ('E-commerce', 'E-commerce'), ('Agenzia', 'Agenzia di servizi')],
        validators=[DataRequired()], description="Come l'azienda genera valore e vende i propri prodotti o servizi ai clienti."
    )
    dimensione = SelectField(
        "Dimensione dell'impresa",
        choices=[('', 'Seleziona...'), ('Micro', 'Microimpresa (0-9 dipendenti)'), ('Piccola', 'Piccola impresa (10-49 dipendenti)'), ('Media', 'Media impresa (50-249 dipendenti)'), ('Grande', 'Grande impresa (Oltre 250 dipendenti)')],
        validators=[DataRequired()]
    )
    dipendenti = IntegerField("Numero di dipendenti", validators=[DataRequired(), NumberRange(min=0)], description="Numero esatto o approssimativo di collaboratori e dipendenti a carico.")
    area_geografica = StringField("Area geografica", validators=[DataRequired(), Length(min=2, max=100)], description="Es. Nord Italia, Lombardia, Estero. Serve per contestualizzare il costo del lavoro.")
    fatturato = StringField("Fatturato indicativo annuo (€)", validators=[DataRequired()], description="Il volume d'affari (fatturato) stimato o registrato nell'ultimo anno.")
    tipologia_clienti = SelectField(
        "Tipologia di clienti",
        choices=[('', 'Seleziona...'), ('PMI', 'Aziende PMI'), ('Corporate', 'Grandi Aziende (Corporate)'), ('Privati', 'Consumatori finali (Privati)'), ('PA', 'Pubblica Amministrazione')],
        validators=[DataRequired()], description="A chi ti rivolgi prevalentemente per le tue vendite."
    )
    mese_riferimento = StringField("Mese riferimento (YYYY-MM)", validators=[DataRequired(), Regexp(r"^\d{4}-\d{2}$", message="Formato: YYYY-MM")], description="Il mese di riferimento dei dati che inserirai (Es: 2024-03).")
    submit = SubmitField("Continua")

class EssentialDataForm(FlaskForm):
    cassa_attuale = FloatField("Disponibilità Liquide (€)", validators=[Optional(), NumberRange(min=0)], description="I soldi effettivi attualmente disponibili sui conti correnti aziendali e in cassa.")
    burn_mensile = FloatField("Burn Rate Mensile (€)", validators=[Optional(), NumberRange(min=0)], description="I costi fissi che devi pagare ogni mese per tenere aperta l'azienda, indipendentemente dalle vendite (affitti, stipendi fissi, software, ecc.).")
    incassi_mese = FloatField("Cash-In del Mese (€)", validators=[Optional(), NumberRange(min=0)], description="Il totale dei soldi incassati (entrati fisicamente in banca) in un mese medio.")
    costi_fissi_mese = FloatField("Costi Operativi Fissi (€)", validators=[Optional(), NumberRange(min=0)], description="Il totale delle spese mensili fisse necessarie per operare.")
    margine_lordo_pct = FloatField("Margine di Contribuzione (%)", validators=[Optional(), NumberRange(min=0, max=100)], description="Quello che ti rimane in tasca da una vendita dopo aver sottratto solo i costi diretti (es. materie prime) per produrre o erogare il servizio. Esprimilo in percentuale (es. 40).")
    leads_mese = FloatField("Volume Nuove Opportunità (#)", validators=[Optional(), NumberRange(min=0)], description="Il numero di nuovi potenziali clienti (contatti/lead) che ricevi in media in un mese.")
    clienti_mese = FloatField("Nuove Conversioni (#)", validators=[Optional(), NumberRange(min=0)], description="Quanti di quei contatti o preventivi diventano effettivamente clienti paganti ogni mese.")
    submit = SubmitField("Continua")

class QuizForm(FlaskForm):
    _choices = [(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")]
    q1 = RadioField("Financial Runway & Visibility", choices=_choices, coerce=int, validators=[DataRequired()], description="Hai chiara visibilità su quanti mesi l'azienda può sopravvivere con la cassa attuale in caso di assenza di nuovi incassi?")
    q2 = RadioField("Cash Flow Stability", choices=_choices, coerce=int, validators=[DataRequired()], description="Le tue entrate mensili sono stabili e prevedibili (voto alto) o subiscono forti sbalzi e ritardi (voto basso)?")
    q3 = RadioField("Analisi della Marginalità", choices=_choices, coerce=int, validators=[DataRequired()], description="Conosci esattamente quanto guadagni su ogni singolo prodotto/servizio venduto e sai se qualcuno è in perdita?")
    q4 = RadioField("Sostenibilità della Struttura", choices=_choices, coerce=int, validators=[DataRequired()], description="I costi per mantenere l'azienda sono ben coperti dagli incassi (voto alto) o iniziano a pesare troppo (voto basso)?")
    q5 = RadioField("Pipeline di Vendita", choices=_choices, coerce=int, validators=[DataRequired()], description="Hai un flusso costante, prevedibile e organizzato di nuovi potenziali clienti interessati?")
    q6 = RadioField("Efficienza Commerciale", choices=_choices, coerce=int, validators=[DataRequired()], description="Riesci a trasformare facilmente i contatti in clienti chiudendo i contratti senza dover fare sconti eccessivi?")
    q7 = RadioField("Risk Diversification", choices=_choices, coerce=int, validators=[DataRequired()], description="Il tuo fatturato è ben distribuito (voto alto) o sei a rischio se perdi 1-2 clienti principali (voto basso)?")
    q8 = RadioField("Data-Driven Management", choices=_choices, coerce=int, validators=[DataRequired()], description="Prendi le decisioni basandoti su numeri e report periodici o ti affidi quasi esclusivamente al tuo intuito e all'esperienza?")
    q9 = RadioField("Efficienza Operativa", choices=_choices, coerce=int, validators=[DataRequired()], description="I processi interni sono ben organizzati o tu e il team perdete molto tempo in inefficienze, ritardi o doppi passaggi?")
    q10 = RadioField("Execution & Agility", choices=_choices, coerce=int, validators=[DataRequired()], description="Riesci ad adattare rapidamente l'azienda ai cambiamenti del mercato e a implementare velocemente nuove idee operative?")
    submit = SubmitField("Genera Analisi Strategica")

class CreateOrganizationForm(FlaskForm):
    name = StringField("Nome azienda", validators=[DataRequired()])
    email = StringField("Email owner", validators=[DataRequired(), Email()])
    password = PasswordField("Password iniziale", validators=[DataRequired()])
    submit = SubmitField("Crea azienda")

class CreateOrgUserForm(FlaskForm):
    email = StringField("Email utente", validators=[DataRequired(), Email()])
    password = PasswordField("Password iniziale", validators=[DataRequired()])
    role = StringField("Ruolo", validators=[DataRequired()])
    submit = SubmitField("Aggiungi utente")

class UpdateOrgUserRoleForm(FlaskForm):
    role = StringField("Ruolo", validators=[DataRequired()])
    submit = SubmitField("Aggiorna ruolo")

class ResetUserPasswordForm(FlaskForm):
    password = PasswordField("Nuova password", validators=[DataRequired()])
    password2 = PasswordField("Ripeti password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Aggiorna password")

class CreatePlanForm(FlaskForm):
    name = StringField("Nome piano", validators=[DataRequired()])
    scan_limit = StringField("Limite scansioni", validators=[DataRequired()])
    price_month = StringField("Prezzo mensile", validators=[DataRequired()])
    submit = SubmitField("Crea piano")

class UpdateOrganizationPlanForm(FlaskForm):
    plan_id = SelectField("Piano", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Aggiorna piano")
