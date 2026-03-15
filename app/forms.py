from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, RadioField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, Regexp, EqualTo

class RegisterForm(FlaskForm):
    email = StringField("📧 Email", validators=[DataRequired(), Email()])
    password = PasswordField("🔐 Password", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField("🔐 Ripeti Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Registrati")

class LoginForm(FlaskForm):
    email = StringField("📧 Email", validators=[DataRequired(), Email()])
    password = PasswordField("🔐 Password", validators=[DataRequired()])
    submit = SubmitField("Accedi")

class OnboardingForm(FlaskForm):
    tipologia_impresa = SelectField(
        "✂️ Tipologia di Salone",
        choices=[
            ('', 'Seleziona...'),
            ('Donna', '💇‍♀️ Salone Donna'),
            ('Uomo', '🧔 Barber / Salone Uomo'),
            ('Unisex', '👫 Salone Unisex'),
            ('Salone + Estetica', '💅 Salone con cabina estetica')
        ],
        validators=[DataRequired()]
    )

    modello = SelectField(
        "👑 Fascia di Posizionamento",
        choices=[
            ('', 'Seleziona...'),
            ('Economico', '🪙 Base / Prezzi Popolari'),
            ('Medio', '✨ Fascia Media'),
            ('Premium', '💎 Premium / Lusso')
        ],
        validators=[DataRequired()]
    )

    dimensione = SelectField(
        "🪑 Dimensione del Salone",
        choices=[
            ('', 'Seleziona...'),
            ('Piccolo', '1️⃣ Piccolo (1-2 postazioni)'),
            ('Medio', '3️⃣ Medio (3-5 postazioni)'),
            ('Grande', '6️⃣ Grande (Oltre 5 postazioni)')
        ],
        validators=[DataRequired()]
    )

    dipendenti = IntegerField(
        "👥 Numero di collaboratori",
        validators=[DataRequired(), NumberRange(min=0)],
        description="Escludendo te, quanti collaboratori operano in salone? ✂️"
    )

    area_geografica = StringField(
        "📍 Provincia / Città",
        validators=[DataRequired(), Length(min=2, max=100)]
    )

    fatturato = StringField(
        "💰 Fatturato annuo stimato (€)",
        validators=[DataRequired()],
        description="Il volume d'affari complessivo dell'ultimo anno."
    )

    tipologia_clienti = SelectField(
        "💇 Frequenza Clienti",
        choices=[
            ('', 'Seleziona...'),
            ('Alta', '😊 Alta frequenza (piega settimanale)'),
            ('Media', '🙂 Media (taglio/colore mensile)'),
            ('Bassa', '😐 Bassa (solo servizi tecnici occasionali)')
        ],
        validators=[DataRequired()]
    )

    mese_riferimento = StringField(
        "📅 Mese di riferimento (YYYY-MM)",
        validators=[DataRequired(), Regexp(r"^\d{4}-\d{2}$", message="Formato: YYYY-MM")],
        description="Il mese che vuoi analizzare (es: 2024-03)"
    )

    submit = SubmitField("Continua")

class EssentialDataForm(FlaskForm):
    cassa_attuale = FloatField(
        "💰 Liquidità in Cassa (€)",
        validators=[Optional(), NumberRange(min=0)],
        description="Soldi disponibili oggi tra banca e cassa fisica. 🏦"
    )

    incassi_totali_mese = FloatField(
        "🧾 Incasso Totale Mensile (€)",
        validators=[Optional(), NumberRange(min=0)],
        description="Tutto ciò che è passato in cassa questo mese. 🧴+💇"
    )

    incassi_retail_mese = FloatField(
        "🧴 Incasso da Prodotti (Rivendita) (€)",
        validators=[Optional(), NumberRange(min=0)],
        description="Quanto hai incassato vendendo prodotti da casa? 🛍️"
    )

    numero_clienti_mese = FloatField(
        "👭 Totale Scontrini Emessi",
        validators=[Optional(), NumberRange(min=0)],
        description="Quante 'teste' sono passate in salone questo mese? 👤"
    )

    costi_materiali_mese = FloatField(
        "🎨 Spesa Prodotti Professionale (€)",
        validators=[Optional(), NumberRange(min=0)],
        description="Costi per colori, ossigeni, shampoo e monouso. 🧪"
    )

    costi_fissi_mese = FloatField(
        "🏠 Affitto, Utenze e Spese Varie (€)",
        validators=[Optional(), NumberRange(min=0)],
        description="Escludi gli stipendi qui, inseriscili sotto. ⚡"
    )

    costo_stipendi_mese = FloatField(
        "💶 Costo Totale del Personale (€)",
        validators=[Optional(), NumberRange(min=0)],
        description="Somma lorda di tutti gli stipendi dei tuoi ragazzi. 👨‍👩‍👧‍👦"
    )

    ore_lavorate_mese = FloatField(
        "⏱️ Ore Totali di Operatività",
        validators=[Optional(), NumberRange(min=0)],
        description="Somma di tutte le ore lavorate da te e dallo staff. ⏳"
    )

    percentuale_servizi_tecnici = FloatField(
        "🎨 % Servizi Tecnici (Colore/Schiariture)",
        validators=[Optional(), NumberRange(min=0, max=100)],
        description="Su 100 clienti, quante fanno un servizio tecnico e non solo piega? 🌈"
    )

    submit = SubmitField("Genera Analisi Strategica")

class QuizForm(FlaskForm):
    # Opzioni visive "Effetto Wow" per percepire immediatamente lo stato del salone
    _choices_visual = [
        ('5', "🤩 **Stellare** - Cliente entusiasta, capelli perfetti!"),
        ('4', "🙂 **Buono** - Capelli in ordine, cliente soddisfatta."),
        ('3', "😐 **Stagnante** - Capelli senza lode, cliente abituale ma tiepida."),
        ('2', "🙁 **In calo** - Capelli un po' spenti, cliente che guarda altrove."),
        ('1', "😟 **Emergenza** - Capelli rovinati e cliente che non torna!"),
    ]

    q1 = RadioField(
        "💇‍♀️ Fidelizzazione: Ritornano o spariscono?",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Le tue clienti tornano con regolarità o è un 'mordi e fuggi'?"
    )

    q2 = RadioField(
        "🧴 Upselling al Lavatesta",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Riesci a vendere una fiala o una ricostruzione a ogni lavaggio? 🫧"
    )

    q3 = RadioField(
        "🛍️ Cultura del Prodotto a Casa",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Le clienti escono con lo shampoo consigliato da te o comprano al supermercato? 🧴"
    )

    q4 = RadioField(
        "⏱️ Ottimizzazione Tempi Morti",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Mentre il colore posa, lo staff propone manicure o vendita prodotti? ⏳"
    )

    q5 = RadioField(
        "⚖️ Controllo Sprechi Colore",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Usi la bilancia digitale per ogni grammo di colore o vai 'ad occhio'? 🧪"
    )

    q6 = RadioField(
        "🌟 Marketing Stagionale",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Sfrutti le ricorrenze (Natale, Estate, Sposi) con pacchetti dedicati? 🗓️"
    )

    q7 = RadioField(
        "📸 Autorità Social",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Pubblichi regolarmente i tuoi 'Prima e Dopo' per attirare nuovi servizi tecnici? 🤳"
    )

    q8 = RadioField(
        "🎓 Crescita del Team",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Il tuo staff è aggiornato sulle ultime tendenze Balayage/Cheratina? 📚"
    )

    q9 = RadioField(
        "💸 Sicurezza sul Listino",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Ti senti sicuro quando comunichi il prezzo di un servizio tecnico complesso? 💰"
    )

    q10 = RadioField(
        "👑 Percezione del Brand",
        choices=_choices_visual,
        validators=[DataRequired()],
        description="Sei visto come l'esperto della zona o come quello 'più comodo/economico'? 🏆"
    )

    submit = SubmitField("Calcola il mio Numero Magico 🎯")

# -----------------------------
# FORM ADMIN (Invariati per logica di sistema)
# -----------------------------

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
