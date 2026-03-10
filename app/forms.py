cat << 'EOF' > app/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    FloatField,
    RadioField,
    SelectField,
    IntegerField
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    Regexp,
    EqualTo,
)

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField("Ripeti Password", validators=[DataRequired(), EqualTo("password", message="Le password non coincidono")])
    submit = SubmitField("Registrati")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Accedi")

class OnboardingForm(FlaskForm):
    tipologia_impresa = SelectField(
        "Tipologia di impresa",
        choices=[
            ('', 'Seleziona...'), 
            ('Consulenza B2B', 'Consulenza B2B'), 
            ('Retail', 'Retail'), 
            ('Manifattura', 'Manifattura'), 
            ('SaaS / Tech', 'SaaS / Tech'), 
            ('Ho.Re.Ca.', 'Ho.Re.Ca.'), 
            ('Immobiliare', 'Immobiliare'), 
            ('Sanità / Studi medici', 'Sanità / Studi medici'), 
            ('Generico', 'Altro (Generico)')
        ],
        validators=[DataRequired()],
        description="Seleziona il mercato principale per confrontare i tuoi dati con i benchmark."
    )
    modello = SelectField(
        "Modello di business",
        choices=[
            ('', 'Seleziona...'),
            ('B2B', 'B2B (Business to Business)'),
            ('B2C', 'B2C (Business to Consumer)'),
            ('SaaS', 'SaaS (Software as a Service)'),
            ('E-commerce', 'E-commerce'),
            ('Agenzia', 'Agenzia di servizi')
        ],
        validators=[DataRequired()],
        description="Come l'azienda genera valore e vende i propri prodotti/servizi."
    )
    dimensione = SelectField(
        "Dimensione dell'impresa",
        choices=[
            ('', 'Seleziona...'),
            ('Micro', 'Microimpresa (0-9 dipendenti)'),
            ('Piccola', 'Piccola impresa (10-49 dipendenti)'),
            ('Media', 'Media impresa (50-249 dipendenti)'),
            ('Grande', 'Grande impresa (Oltre 250 dipendenti)')
        ],
        validators=[DataRequired()]
    )
    dipendenti = IntegerField(
        "Numero di dipendenti",
        validators=[DataRequired(), NumberRange(min=0)],
        description="Numero esatto o approssimativo di collaboratori."
    )
    area_geografica = StringField(
        "Area geografica",
        validators=[DataRequired(), Length(min=2, max=100)],
        description="Es. Nord Italia, Lombardia, Estero."
    )
    fatturato = StringField(
        "Fatturato indicativo annuo (€)",
        validators=[DataRequired()],
        description="Fatturato annuo stimato (es. 500000)."
    )
    tipologia_clienti = SelectField(
        "Tipologia di clienti",
        choices=[
            ('', 'Seleziona...'),
            ('PMI', 'Aziende PMI'),
            ('Corporate', 'Grandi Aziende (Corporate)'),
            ('Privati', 'Consumatori finali (Privati)'),
            ('PA', 'Pubblica Amministrazione')
        ],
        validators=[DataRequired()],
        description="Il tuo target di clientela principale."
    )
    mese_riferimento = StringField(
        "Mese riferimento (YYYY-MM)",
        validators=[DataRequired(), Regexp(r"^\d{4}-\d{2}$", message="Formato: YYYY-MM")],
        description="Il periodo a cui si riferiscono i dati che inserirai."
    )
    submit = SubmitField("Continua")

class EssentialDataForm(FlaskForm):
    cassa_attuale = FloatField("Disponibilità Liquide (€)", validators=[Optional(), NumberRange(min=0)])
    burn_mensile = FloatField("Burn Rate Mensile (€)", validators=[Optional(), NumberRange(min=0)])
    incassi_mese = FloatField("Cash-In del Mese (€)", validators=[Optional(), NumberRange(min=0)])
    costi_fissi_mese = FloatField("Costi Operativi Fissi (€)", validators=[Optional(), NumberRange(min=0)])
    margine_lordo_pct = FloatField("Margine di Contribuzione (%)", validators=[Optional(), NumberRange(min=0, max=100)])
    leads_mese = FloatField("Volume Nuove Opportunità (#)", validators=[Optional(), NumberRange(min=0)])
    clienti_mese = FloatField("Nuove Conversioni (#)", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Continua")

class QuizForm(FlaskForm):
    _choices = [(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")]
    q1 = RadioField("Financial Runway & Visibility", choices=_choices, coerce=int, validators=[DataRequired()])
    q2 = RadioField("Cash Flow Stability", choices=_choices, coerce=int, validators=[DataRequired()])
    q3 = RadioField("Analisi della Marginalità", choices=_choices, coerce=int, validators=[DataRequired()])
    q4 = RadioField("Sostenibilità della Struttura", choices=_choices, coerce=int, validators=[DataRequired()])
    q5 = RadioField("Pipeline di Vendita", choices=_choices, coerce=int, validators=[DataRequired()])
    q6 = RadioField("Efficienza Commerciale", choices=_choices, coerce=int, validators=[DataRequired()])
    q7 = RadioField("Risk Diversification", choices=_choices, coerce=int, validators=[DataRequired()])
    q8 = RadioField("Data-Driven Management", choices=_choices, coerce=int, validators=[DataRequired()])
    q9 = RadioField("Efficienza Operativa", choices=_choices, coerce=int, validators=[DataRequired()])
    q10 = RadioField("Execution & Agility", choices=_choices, coerce=int, validators=[DataRequired()])
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
EOF