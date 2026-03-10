from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    FloatField,
    IntegerField,
    RadioField,
    SelectField,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    Regexp,
    EqualTo,
)

from app.settori import SETTORI


CHOICES_1_5 = [(1,"1"),(2,"2"),(3,"3"),(4,"4"),(5,"5")]


class RegisterForm(FlaskForm):
    email = StringField("Email Aziendale", validators=[DataRequired(), Email()], 
                        description="Inserire l'indirizzo email principale per le comunicazioni ufficiali.")
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)],
                             description="La password deve contenere almeno 6 caratteri.")

    password2 = PasswordField(
        "Conferma Password",
        validators=[DataRequired(), EqualTo("password")],
        description="Ripeti la password scelta per verifica sicurezza."
    )

    submit = SubmitField("Registrati")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Accedi")


class OnboardingForm(FlaskForm):
    settore = SelectField("Settore Merceologico", choices=SETTORI, validators=[DataRequired()],
                          description="Seleziona l'industria di appartenenza per calibrare i benchmark.")
    modello = StringField("Modello di Business", validators=[DataRequired(), Length(min=2, max=100)],
                          description="Esempio: SaaS, E-commerce, Consulenza, Manifatturiero.")

    mese_riferimento = StringField(
        "Periodo di Analisi (YYYY-MM)",
        validators=[DataRequired(), Regexp(r"^\d{4}-\d{2}$")],
        description="Inserisci l'anno e il mese dei dati che stai per caricare (es. 2024-03)."
    )

    submit = SubmitField("Continua")


class EssentialDataForm(FlaskForm):

    cassa_attuale = FloatField("Disponibilità Liquida Attuale (€)", validators=[Optional(), NumberRange(min=0)],
                               description="Somma totale della liquidità immediatamente disponibile sui conti correnti.")
    burn_mensile = FloatField("Burn Rate Mensile (€)", validators=[Optional(), NumberRange(min=0)],
                              description="L'importo netto di cassa che l'azienda consuma ogni mese per coprire il deficit operativo.")

    incassi_mese = FloatField("Volume Incassi Mensili (€)", validators=[Optional(), NumberRange(min=0)],
                              description="Totale dei flussi finanziari in entrata effettivamente percepiti nel mese.")
    costi_fissi_mese = FloatField("Opex - Costi Fissi Mensili (€)", validators=[Optional(), NumberRange(min=0)],
                                  description="Spese operative ricorrenti che non variano al variare della produzione (affitti, stipendi, software).")

    margine_lordo_pct = FloatField(
        "Margine di Contribuzione (%)",
        validators=[Optional(), NumberRange(min=0, max=100)],
        description="Percentuale del ricavo che rimane dopo aver coperto i costi diretti di produzione/vendita."
    )

    leads_mese = IntegerField("Lead Generation (N°)", validators=[Optional(), NumberRange(min=0)],
                              description="Numero di potenziali clienti interessati acquisiti nel periodo di riferimento.")
    clienti_mese = IntegerField("Nuove Conversioni (N°)", validators=[Optional(), NumberRange(min=0)],
                                description="Numero di nuovi clienti unici che hanno effettuato un acquisto nel mese.")

    submit = SubmitField("Continua")


class QuizForm(FlaskForm):

    q1 = RadioField("Solidità della Runway Finanziaria (90gg)", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                    description="Grado di certezza di poter coprire tutti gli impegni finanziari nei prossimi 3 mesi.")
    q2 = RadioField("Prevedibilità dei Flussi di Cassa", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                    description="Capacità di stimare con precisione tempi e volumi degli incassi futuri.")
    q3 = RadioField("Analisi della Marginalità Reale", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                    description="Livello di consapevolezza dei margini effettivi al netto di ogni costo nascosto.")
    q4 = RadioField("Sostenibilità della Struttura dei Costi", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                    description="Capacità dei ricavi attuali di assorbire i costi fissi senza erodere le riserve.")
    q5 = RadioField("Pipeline Commerciale Ricorrente", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                    description="Frequenza e stabilità con cui vengono generate nuove opportunità di vendita.")
    q6 = RadioField("Efficienza del Funnel di Vendita", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                    description="Capacità di trasformare i potenziali contatti in clienti paganti in modo sistematico.")
    q7 = RadioField("Indice di Concentrazione del Portafoglio", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                    description="Valuta quanto sei dipendente da pochi grandi clienti (5 = molto diversificato).")
    q8 = RadioField("Data-Driven Management (KPI)", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                    description="Quanto le decisioni aziendali si basano su dati certi e indicatori di performance.")
    q9 = RadioField("Ottimizzazione Processi e Costi", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                    description="Livello di monitoraggio e riduzione degli sprechi operativi.")
    q10 = RadioField("Execution ed Output del Team", choices=CHOICES_1_5, coerce=int, validators=[InputRequired()],
                     description="Capacità della squadra di scaricare a terra gli obiettivi prefissati nei tempi stabiliti.")

    submit = SubmitField("Genera Analisi Strategica")


class CreateOrganizationForm(FlaskForm):
    name = StringField("Ragione Sociale / Nome Brand", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email Amministratore", validators=[DataRequired(), Email()])
    password = PasswordField("Password di Accesso", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Crea Profilo Aziendale")


class CreateOrgUserForm(FlaskForm):
    email = StringField("Email Collaboratore", validators=[DataRequired(), Email()])
    password = PasswordField("Password Temporanea", validators=[DataRequired(), Length(min=6)])
    role = StringField("Inquadramento / Ruolo", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Invita Utente")


class UpdateOrgUserRoleForm(FlaskForm):
    role = StringField("Nuovo Ruolo", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Aggiorna Permessi")


class ResetUserPasswordForm(FlaskForm):
    password = PasswordField(
        "Nuova Password",
        validators=[DataRequired(), Length(min=6)],
    )
    password2 = PasswordField(
        "Conferma Nuova Password",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Ripristina Credenziali")


class CreatePlanForm(FlaskForm):
    name = StringField("Denominazione Piano", validators=[DataRequired(), Length(min=2, max=50)])
    scan_limit = StringField("Quota Analisi Incluse", validators=[DataRequired()])
    price_month = StringField("Canone Mensile (€)", validators=[DataRequired()])
    submit = SubmitField("Salva Configurazione Piano")


class UpdateOrganizationPlanForm(FlaskForm):
    plan_id = SelectField("Seleziona Nuovo Piano", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Esegui Upgrade/Downgrade")