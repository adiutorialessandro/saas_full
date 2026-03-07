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
    settore = StringField("Settore", validators=[DataRequired(), Length(min=2, max=100)])
    modello = StringField("Modello", validators=[DataRequired(), Length(min=2, max=100)])
    mese_riferimento = StringField(
        "Mese riferimento (YYYY-MM)",
        validators=[DataRequired(), Regexp(r"^\d{4}-\d{2}$", message="Formato: YYYY-MM")],
    )
    submit = SubmitField("Continua")


class EssentialDataForm(FlaskForm):
    cassa_attuale = FloatField("Cassa attuale (€)", validators=[Optional(), NumberRange(min=0)])
    burn_mensile = FloatField("Burn mensile (€)", validators=[Optional(), NumberRange(min=0)])
    incassi_mese = FloatField("Incassi mese (€)", validators=[Optional(), NumberRange(min=0)])
    costi_fissi_mese = FloatField("Costi fissi mese (€)", validators=[Optional(), NumberRange(min=0)])
    margine_lordo_pct = FloatField("Margine lordo (%)", validators=[Optional(), NumberRange(min=0, max=100)])
    leads_mese = FloatField("Lead mese (#)", validators=[Optional(), NumberRange(min=0)])
    clienti_mese = FloatField("Clienti mese (#)", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Continua")


class QuizForm(FlaskForm):
    # 1 = situazione critica / fragile / poco controllata
    # 5 = situazione solida / stabile / ben controllata
    _choices = [(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")]

    q1 = RadioField(
        "Quanto hai visibilità reale e aggiornata sulla tenuta finanziaria della tua azienda nei prossimi 90 giorni?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q2 = RadioField(
        "Quanto gli incassi sono regolari, prevedibili e coerenti con i tempi di cassa di cui l’azienda ha bisogno?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q3 = RadioField(
        "Quanto hai controllo sul margine reale generato dai tuoi prodotti, servizi o commesse?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q4 = RadioField(
        "Quanto il livello attuale dei ricavi copre con sicurezza costi fissi e struttura aziendale?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q5 = RadioField(
        "Quanto il flusso di nuove opportunità commerciali è costante e non dipende dal caso o da iniziative sporadiche?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q6 = RadioField(
        "Quanto il processo commerciale riesce a trasformare lead e opportunità in clienti in modo efficace e ripetibile?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q7 = RadioField(
        "Quanto il business è diversificato e non dipendente da pochi clienti, pochi canali o poche commesse critiche?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q8 = RadioField(
        "Quanto le decisioni aziendali vengono prese su KPI chiari, aggiornati e realmente utili alla gestione?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q9 = RadioField(
        "Quanto costi, processi e operatività sono sotto controllo senza dispersioni, inefficienze o sprechi significativi?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q10 = RadioField(
        "Quanto il team o l’organizzazione riesce a trasformare rapidamente le priorità in esecuzione concreta e risultati?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    submit = SubmitField("Genera scan")


class CreateOrganizationForm(FlaskForm):
    name = StringField("Nome azienda", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email owner", validators=[DataRequired(), Email()])
    password = PasswordField("Password iniziale", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Crea azienda")


class CreateOrgUserForm(FlaskForm):
    email = StringField("Email utente", validators=[DataRequired(), Email()])
    password = PasswordField("Password iniziale", validators=[DataRequired(), Length(min=6)])
    role = StringField("Ruolo", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Aggiungi utente")


class UpdateOrgUserRoleForm(FlaskForm):
    role = StringField("Ruolo", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Aggiorna ruolo")


class ResetUserPasswordForm(FlaskForm):
    password = PasswordField(
        "Nuova password",
        validators=[DataRequired(), Length(min=6)],
    )
    password2 = PasswordField(
        "Ripeti password",
        validators=[DataRequired(), EqualTo("password", message="Le password non coincidono")],
    )
    submit = SubmitField("Aggiorna password")


class CreatePlanForm(FlaskForm):
    name = StringField("Nome piano", validators=[DataRequired(), Length(min=2, max=50)])
    scan_limit = StringField("Limite scansioni", validators=[DataRequired()])
    price_month = StringField("Prezzo mensile", validators=[DataRequired()])
    submit = SubmitField("Crea piano")


class UpdateOrganizationPlanForm(FlaskForm):
    plan_id = SelectField("Piano", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Aggiorna piano")