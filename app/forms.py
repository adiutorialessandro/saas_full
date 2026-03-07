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
    # 1 = situazione critica / poco controllo
    # 5 = situazione stabile / buon controllo
    _choices = [(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")]

    q1 = RadioField(
        "Hai una visione chiara della liquidità disponibile per i prossimi 90 giorni?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q2 = RadioField(
        "Gli incassi entrano con regolarità e nei tempi previsti?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q3 = RadioField(
        "Conosci con chiarezza il margine reale dei tuoi prodotti o servizi?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q4 = RadioField(
        "I ricavi attuali coprono con sufficiente sicurezza i costi fissi aziendali?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q5 = RadioField(
        "La generazione di lead o opportunità commerciali è costante e prevedibile?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q6 = RadioField(
        "Il processo commerciale converte lead in clienti con efficacia soddisfacente?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q7 = RadioField(
        "La tua azienda è poco dipendente da pochi clienti o poche commesse?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q8 = RadioField(
        "Hai KPI chiari e aggiornati per prendere decisioni rapide e corrette?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q9 = RadioField(
        "I costi, i processi e l’operatività sono sotto controllo senza sprechi rilevanti?",
        choices=_choices,
        coerce=int,
        validators=[DataRequired()],
    )

    q10 = RadioField(
        "Il team o l’organizzazione riesce a eseguire priorità e decisioni con continuità?",
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