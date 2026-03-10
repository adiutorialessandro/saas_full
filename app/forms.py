from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    FloatField,
    RadioField,
    SelectField,
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
    password2 = PasswordField(
        "Ripeti Password",
        validators=[DataRequired(), EqualTo("password", message="Le password non coincidono")],
    )
    submit = SubmitField("Registrati")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Accedi")


class OnboardingForm(FlaskForm):
    settore = StringField(
        "Settore Merceologico", 
        validators=[DataRequired(), Length(min=2, max=100)],
        description="Indica il mercato principale in cui opera l'azienda (es. Manifatturiero, SaaS, Retail)."
    )
    modello = StringField(
        "Business Model", 
        validators=[DataRequired(), Length(min=2, max=100)],
        description="Come l'azienda genera valore (es. B2B a commessa, Abbonamento ricorrente, E-commerce)."
    )
    mese_riferimento = StringField(
        "Periodo di Analisi (YYYY-MM)",
        validators=[DataRequired(), Regexp(r"^\d{4}-\d{2}$", message="Formato richiesto: AAAA-MM")],
        description="Il mese e l'anno a cui si riferiscono i dati che stai per inserire."
    )
    submit = SubmitField("Continua")


class EssentialDataForm(FlaskForm):
    cassa_attuale = FloatField(
        "Disponibilità Liquide (€)", 
        validators=[Optional(), NumberRange(min=0)],
        description="La somma totale di denaro immediatamente disponibile sui conti correnti e in cassa oggi."
    )
    burn_mensile = FloatField(
        "Burn Rate Mensile (€)", 
        validators=[Optional(), NumberRange(min=0)],
        description="L'ammontare medio di liquidità che l'azienda 'brucia' ogni mese per coprire le proprie spese operative."
    )
    incassi_mese = FloatField(
        "Cash-In del Mese (€)", 
        validators=[Optional(), NumberRange(min=0)],
        description="Il totale del denaro effettivamente incassato dai clienti nel periodo di riferimento (non il fatturato emesso)."
    )
    costi_fissi_mese = FloatField(
        "Costi Operativi Fissi (€)", 
        validators=[Optional(), NumberRange(min=0)],
        description="Spese che non variano al variare delle vendite, come affitti, stipendi del personale fisso e software."
    )
    margine_lordo_pct = FloatField(
        "Margine di Contribuzione (%)", 
        validators=[Optional(), NumberRange(min=0, max=100)],
        description="La percentuale di guadagno che resta dopo aver pagato solo i costi diretti per produrre il bene o servizio."
    )
    leads_mese = FloatField(
        "Volume Nuove Opportunità (#)", 
        validators=[Optional(), NumberRange(min=0)],
        description="Il numero di potenziali clienti (Lead) che hanno manifestato interesse o sono entrati nel funnel di vendita."
    )
    clienti_mese = FloatField(
        "Nuove Conversioni (#)", 
        validators=[Optional(), NumberRange(min=0)],
        description="Il numero di nuovi clienti che hanno effettuato il primo acquisto o firmato un contratto nel mese."
    )
    submit = SubmitField("Continua")


class QuizForm(FlaskForm):
    # Scala di valutazione:
    # 1 = Criticità elevata / Assenza di controllo
    # 5 = Eccellenza operativa / Controllo totale
    _choices = [(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")]

    q1 = RadioField(
        "Financial Runway & Visibility",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Valuta quanto chiaramente riesci a prevedere se la cassa sarà sufficiente a coprire i debiti nei prossimi 3 mesi."
    )

    q2 = RadioField(
        "Cash Flow Stability",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Valuta la regolarità degli incassi: arrivano puntuali o soffri di ritardi che mettono a rischio i pagamenti?"
    )

    q3 = RadioField(
        "Analisi della Marginalità",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Indica quanto sei consapevole del guadagno reale netto per ogni singolo prodotto o servizio venduto."
    )

    q4 = RadioField(
        "Sostenibilità della Struttura",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Valuta se il volume d'affari attuale è ampiamente superiore ai costi fissi o se sei pericolosamente vicino al punto di pareggio."
    )

    q5 = RadioField(
        "Pipeline di Vendita",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Valuta se l'arrivo di nuovi potenziali clienti è frutto di una strategia costante o se dipende dal caso/passaparola."
    )

    q6 = RadioField(
        "Efficienza Commerciale (Conversion Rate)",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Quanto sei efficace nel trasformare un preventivo o un interesse iniziale in un contratto firmato?"
    )

    q7 = RadioField(
        "Risk Diversification",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Valuta il rischio di concentrazione: se perdessi il tuo cliente principale domani, l'azienda sopravviverebbe?"
    )

    q8 = RadioField(
        "Data-Driven Management (KPI)",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Valuta quanto le tue decisioni si basano su numeri certi e dashboard aggiornate piuttosto che sull'intuizione."
    )

    q9 = RadioField(
        "Efficienza Operativa",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Valuta la presenza di sprechi di tempo o denaro nei processi interni e nella gestione dei fornitori."
    )

    q10 = RadioField(
        "Execution & Agility",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
        description="Valuta la velocità con cui l'azienda riesce a mettere in pratica un nuovo progetto o una correzione di rotta."
    )

    submit = SubmitField("Genera Analisi Strategica")


class CreateOrganizationForm(FlaskForm):
    name = StringField("Denominazione Sociale", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email Referente (Owner)", validators=[DataRequired(), Email()])
    password = PasswordField("Password Temporanea", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Crea Profilo Aziendale")


class CreateOrgUserForm(FlaskForm):
    email = StringField("Email Utente", validators=[DataRequired(), Email()])
    password = PasswordField("Password di Accesso", validators=[DataRequired(), Length(min=6)])
    role = StringField("Qualifica/Ruolo", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Abilita Utente")


class UpdateOrgUserRoleForm(FlaskForm):
    role = StringField("Nuova Qualifica", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Aggiorna Ruolo")


class ResetUserPasswordForm(FlaskForm):
    password = PasswordField(
        "Nuova Password",
        validators=[DataRequired(), Length(min=6)],
    )
    password2 = PasswordField(
        "Conferma Password",
        validators=[DataRequired(), EqualTo("password", message="Le password non coincidono")],
    )
    submit = SubmitField("Ripristina Credenziali")


class CreatePlanForm(FlaskForm):
    name = StringField("Nome Piano Tariffario", validators=[DataRequired(), Length(min=2, max=50)])
    scan_limit = StringField("Soglia Scansioni Mensili", validators=[DataRequired()])
    price_month = StringField("Canone Mensile (€)", validators=[DataRequired()])
    submit = SubmitField("Salva Piano")


class UpdateOrganizationPlanForm(FlaskForm):
    plan_id = SelectField("Seleziona Piano", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Applica Modifiche Piano")