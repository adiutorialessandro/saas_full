from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.benchmark import SectorBenchmark
from app.services.scoring_engine import business_stability_score


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Inputs:
    settore: str
    modello: str
    mese_riferimento: str
    quiz_risk: List[float]

    dimensione: Optional[str] = None
    dipendenti: Optional[int] = None
    area_geografica: Optional[str] = None
    fatturato: Optional[str] = None
    tipologia_clienti: Optional[str] = None

    # Dati salone
    cassa_attuale: Optional[float] = None
    incassi_totali_mese: Optional[float] = None
    incassi_retail_mese: Optional[float] = None
    numero_clienti_mese: Optional[float] = None
    costi_materiali_mese: Optional[float] = None
    costi_fissi_mese: Optional[float] = None
    ore_lavorate_mese: Optional[float] = None

    # Nuovi campi "wow"
    costo_stipendi_mese: Optional[float] = None
    percentuale_servizi_tecnici: Optional[float] = None


def build_report(inp: Inputs, bench: Optional[SectorBenchmark] = None) -> Dict[str, Any]:
    # ---------------------------------------------------
    # KPI BASE
    # ---------------------------------------------------
    burn = inp.costi_fissi_mese if inp.costi_fissi_mese is not None else 0

    runway_mesi = None
    if inp.cassa_attuale is not None and burn > 0:
        runway_mesi = inp.cassa_attuale / burn

    margine_pct = None
    if inp.incassi_totali_mese is not None and inp.costi_materiali_mese is not None and inp.incassi_totali_mese > 0:
        margine_pct = (inp.incassi_totali_mese - inp.costi_materiali_mese) / inp.incassi_totali_mese

    conversione = None
    if inp.incassi_retail_mese is not None and inp.incassi_totali_mese is not None and inp.incassi_totali_mese > 0:
        conversione = inp.incassi_retail_mese / inp.incassi_totali_mese

    fiche_media = None
    if inp.incassi_totali_mese is not None and inp.numero_clienti_mese is not None and inp.numero_clienti_mese > 0:
        fiche_media = inp.incassi_totali_mese / inp.numero_clienti_mese

    break_even_ratio = None
    if (
        inp.incassi_totali_mese is not None
        and inp.costi_fissi_mese is not None
        and margine_pct is not None
        and margine_pct > 0
    ):
        if inp.costi_fissi_mese > 0:
            be_ricavi = inp.costi_fissi_mese / margine_pct
            break_even_ratio = inp.incassi_totali_mese / be_ricavi
        else:
            break_even_ratio = 999.0

    burn_cash_ratio = None
    if burn > 0 and inp.cassa_attuale is not None and inp.cassa_attuale > 0:
        burn_cash_ratio = burn / inp.cassa_attuale

    # ---------------------------------------------------
    # BENCHMARK TARGET
    # ---------------------------------------------------
    b_margin_good = (
        bench.margine_lordo_target / 100
        if bench and getattr(bench, "margine_lordo_target", None) is not None
        else 0.80
    )
    b_margin_bad = b_margin_good * 0.6

    b_conv_good = (
        bench.conversione_target / 100
        if bench and getattr(bench, "conversione_target", None) is not None and bench.conversione_target > 0
        else 0.15
    )
    b_conv_bad = b_conv_good * 0.3

    b_be_good = bench.break_even_sano if bench and getattr(bench, "break_even_sano", None) is not None else 1.2
    b_be_bad = 0.95

    b_runway_good = bench.runway_minima if bench and getattr(bench, "runway_minima", None) is not None else 6
    b_runway_bad = 2

    # ---------------------------------------------------
    # FUNZIONI SUPPORTO
    # ---------------------------------------------------
    def norm(value, good, bad, higher=True):
        if value is None:
            return None

        v = float(value)
        if good == bad:
            return 0

        if higher:
            if v >= good:
                return 0
            if v <= bad:
                return 1
            return (good - v) / (good - bad)
        else:
            if v <= good:
                return 0
            if v >= bad:
                return 1
            return (v - good) / (bad - good)

    def safe_round(value, digits=2):
        return round(value, digits) if value is not None else None

    def mese_numero(mese_riferimento: str) -> Optional[str]:
        try:
            return mese_riferimento.split("-")[1]
        except Exception:
            return None

    def label_retail(conv: Optional[float]) -> str:
        if conv is None:
            return "Non calcolabile"
        if conv >= 0.18:
            return "Retail eccellente"
        if conv >= 0.10:
            return "Retail discreto"
        return "Retail debole"

    def label_produttivita(val: Optional[float]) -> str:
        if val is None:
            return "Non calcolabile"
        if val >= 35:
            return "Produttività premium"
        if val >= 25:
            return "Produttività discreta"
        return "Produttività fragile"

    # ---------------------------------------------------
    # RISCHI
    # ---------------------------------------------------
    r_runway = norm(runway_mesi, b_runway_good, b_runway_bad, True)
    r_margin = norm(margine_pct, b_margin_good, b_margin_bad, True)
    r_conv = norm(conversione, b_conv_good, b_conv_bad, True)
    r_be = norm(break_even_ratio, b_be_good, b_be_bad, True)
    r_burn = norm(burn_cash_ratio, 0.12, 0.25, False)

    quiz = inp.quiz_risk or [0.6] * 10
    quiz = [max(0, min(1, float(q))) for q in quiz]
    quiz_avg = sum(quiz) / len(quiz)

    def combine(primary):
        if primary is None:
            return quiz_avg
        return primary * 0.65 + quiz_avg * 0.35

    risk_cash = combine(r_runway)
    if r_burn is not None:
        risk_cash = max(risk_cash, r_burn * 0.8)

    if r_margin is not None and r_be is not None:
        marg_mix = (r_margin * 0.6) + (r_be * 0.4)
    else:
        marg_mix = r_margin if r_margin is not None else (r_be if r_be is not None else quiz_avg)

    risk_margini = combine(marg_mix)
    risk_acq = combine(r_conv)

    critical_candidates = [
        ("💰 Cassa / Sopravvivenza", risk_cash),
        ("✂️ Margini / Break-even", risk_margini),
        ("🧴 Vendita Prodotti", risk_acq),
    ]

    critical_kpis = [
        {"area": name, "risk": round(value * 100, 1)}
        for name, value in sorted(critical_candidates, key=lambda x: (x[1] if x[1] is not None else 0), reverse=True)
    ][:3]

    base_risk = (risk_cash * 0.45 + risk_margini * 0.30 + risk_acq * 0.25)

    penalty = 0
    if runway_mesi is not None and runway_mesi < b_runway_bad:
        penalty += 0.12
    if break_even_ratio is not None and break_even_ratio < b_be_bad:
        penalty += 0.08
    if margine_pct is not None and margine_pct < b_margin_bad:
        penalty += 0.06
    if conversione is not None and b_conv_bad > 0 and conversione < b_conv_bad:
        penalty += 0.05

    overall_risk = min(1, base_risk + penalty)
    triad_index = round((1 - overall_risk) * 100, 2)

    resilience_components = []
    if runway_mesi is not None:
        resilience_components.append(min(runway_mesi / b_runway_good, 1))
    if margine_pct is not None:
        resilience_components.append(min(margine_pct / b_margin_good, 1))
    if break_even_ratio is not None:
        resilience_components.append(min(break_even_ratio / b_be_good, 1))
    if conversione is not None and b_conv_good > 0:
        resilience_components.append(min(conversione / b_conv_good, 1))

    resilience_index = round((sum(resilience_components) / len(resilience_components)) * 100, 2) if resilience_components else None

    if resilience_index is None:
        resilience_label = "Resilienza non calcolabile"
    elif resilience_index >= 75:
        resilience_label = "Resilienza elevata"
    elif resilience_index >= 50:
        resilience_label = "Resilienza moderata"
    else:
        resilience_label = "Resilienza fragile"

    if triad_index >= 70:
        maturity_label = "Maturità: Avanzata"
    elif triad_index >= 45:
        maturity_label = "Maturità: Intermedia"
    else:
        maturity_label = "Maturità: Fragile"

    kpi_count = sum([
        runway_mesi is not None,
        margine_pct is not None,
        conversione is not None,
        break_even_ratio is not None,
    ])
    confidence = round((kpi_count / 4) * 100) if kpi_count > 0 else 50

    kpi_dict = {
        "runway_mesi": runway_mesi,
        "margine_pct": margine_pct,
        "conversione": conversione,
        "break_even_ratio": break_even_ratio,
    }

    stability = business_stability_score(kpi_dict)
    stability_score = stability.get("score")
    stability_status = stability.get("status")

    # ---------------------------------------------------
    # KPI WOW 1: RESA ORARIA STAFF
    # ---------------------------------------------------
    resa_oraria_team = None
    costo_orario_staff = None
    margine_orario_team = None

    if inp.incassi_totali_mese is not None and inp.ore_lavorate_mese is not None and inp.ore_lavorate_mese > 0:
        resa_oraria_team = inp.incassi_totali_mese / inp.ore_lavorate_mese

    if inp.costo_stipendi_mese is not None and inp.ore_lavorate_mese is not None and inp.ore_lavorate_mese > 0:
        costo_orario_staff = inp.costo_stipendi_mese / inp.ore_lavorate_mese

    if resa_oraria_team is not None and costo_orario_staff is not None:
        margine_orario_team = resa_oraria_team - costo_orario_staff

    produttivita_staff = {
        "resa_oraria_team": safe_round(resa_oraria_team),
        "costo_orario_staff": safe_round(costo_orario_staff),
        "margine_orario_team": safe_round(margine_orario_team),
        "label": label_produttivita(resa_oraria_team),
        "insight": None,
        "azione": None,
    }

    if margine_orario_team is not None:
        if margine_orario_team < 10:
            produttivita_staff["insight"] = (
                "⚠️ Ogni ora di lavoro produce troppo poco margine. Il team lavora, ma non sta valorizzando abbastanza ogni cliente."
            )
            produttivita_staff["azione"] = (
                "✂️ Insegna a proporre sempre un extra durante lavaggio, posa o chiusura servizio: fiala, gloss, maschera premium o mantenimento a casa."
            )
        elif margine_orario_team < 18:
            produttivita_staff["insight"] = (
                "🟡 La resa oraria è discreta ma ancora migliorabile: state incassando, ma non abbastanza per un salone che vuole posizionarsi in alto."
            )
            produttivita_staff["azione"] = (
                "🧴 Standardizza una frase di upsell per tutto il team e misura chi converte meglio su retail e trattamenti."
            )
        else:
            produttivita_staff["insight"] = (
                "🏆 Ottima resa oraria: il team sta trasformando bene il tempo in fatturato."
            )
            produttivita_staff["azione"] = (
                "👑 Consolidare il metodo: script di vendita, protocollo lavatesta e focus sui servizi premium."
            )

    # ---------------------------------------------------
    # KPI WOW 2: DIAGNOSI PIEGACIFICIO
    # ---------------------------------------------------
    piegacificio_alert = {
        "attivo": False,
        "livello": "ok",
        "percentuale_servizi_tecnici": inp.percentuale_servizi_tecnici,
        "titolo": "Mix servizi equilibrato",
        "messaggio": "Il mix servizi non mostra criticità evidenti.",
        "azione": "Continua a proteggere il tempo tecnico in agenda.",
        "color": "#10b981",
        "icon": "🎨",
    }

    if inp.percentuale_servizi_tecnici is not None:
        pct = inp.percentuale_servizi_tecnici
        if pct < 35:
            piegacificio_alert = {
                "attivo": True,
                "livello": "critico",
                "percentuale_servizi_tecnici": pct,
                "titolo": "⚠️ Attenzione: salone in modalità Piegacificio",
                "messaggio": "Stai consumando ore e fisico su servizi a basso margine. Il tecnico è troppo basso per sostenere crescita premium.",
                "azione": "🎯 Lancia subito una Color Week o una Schiariture Week con bonus gloss o tonalizzazione inclusa.",
                "color": "#ef4444",
                "icon": "🚨",
            }
        elif pct < 50:
            piegacificio_alert = {
                "attivo": True,
                "livello": "attenzione",
                "percentuale_servizi_tecnici": pct,
                "titolo": "🟡 Rischio Piegacificio",
                "messaggio": "Il numero di servizi tecnici è troppo vicino alla soglia minima. Stai lavorando molto ma non abbastanza in profondità.",
                "azione": "💡 Allena il team a trasformare piega + mantenimento in proposta colore, riflessante, gloss o ricostruzione.",
                "color": "#f59e0b",
                "icon": "⚠️",
            }

    # ---------------------------------------------------
    # KPI WOW 3: NUMERO MAGICO DI DOMANI
    # ---------------------------------------------------
    numero_magico = {
        "titolo": "🎯 Il tuo Numero Magico di Domani",
        "shampoo_extra_al_giorno": None,
        "trattamenti_extra_al_giorno": None,
        "extra_mensile_stimato": None,
        "messaggio": None,
        "azione_staff": None,
    }

    giorni_lavorativi_mese = 26
    target_extra_mensile = 0.0

    if inp.incassi_totali_mese is not None and inp.costi_fissi_mese is not None:
        # target pragmatico: 5% dei ricavi o 10% dei costi fissi, il maggiore dei due
        target_extra_mensile = max(inp.incassi_totali_mese * 0.05, inp.costi_fissi_mese * 0.10)
    elif inp.incassi_totali_mese is not None:
        target_extra_mensile = inp.incassi_totali_mese * 0.05
    elif inp.costi_fissi_mese is not None:
        target_extra_mensile = inp.costi_fissi_mese * 0.10

    if target_extra_mensile > 0:
        valore_medio_shampoo = 18.0
        valore_medio_trattamento = 25.0

        shampoo_extra_al_giorno = max(1, round((target_extra_mensile * 0.4) / valore_medio_shampoo / giorni_lavorativi_mese))
        trattamenti_extra_al_giorno = max(1, round((target_extra_mensile * 0.6) / valore_medio_trattamento / giorni_lavorativi_mese))

        extra_generato = ((shampoo_extra_al_giorno * valore_medio_shampoo) + (trattamenti_extra_al_giorno * valore_medio_trattamento)) * giorni_lavorativi_mese

        numero_magico["shampoo_extra_al_giorno"] = shampoo_extra_al_giorno
        numero_magico["trattamenti_extra_al_giorno"] = trattamenti_extra_al_giorno
        numero_magico["extra_mensile_stimato"] = safe_round(extra_generato)
        numero_magico["messaggio"] = (
            f"Per migliorare il margine del salone non devi stravolgere tutto: ti bastano "
            f"{shampoo_extra_al_giorno} shampoo in più al giorno e "
            f"{trattamenti_extra_al_giorno} trattamento/i extra al lavatesta. "
            f"Questo può generare circa {safe_round(extra_generato)}€ in più al mese."
        )
        numero_magico["azione_staff"] = (
            "📣 Messaggio da dare domattina al team: 'Oggi ogni postazione deve proporre almeno un extra di mantenimento e un trattamento tecnico in più.'"
        )

    # ---------------------------------------------------
    # KPI WOW 4: CALENDARIO STAGIONALE INTELLIGENTE
    # ---------------------------------------------------
    mese = mese_numero(inp.mese_riferimento)

    stagionalita = {
        "mese": mese,
        "titolo": "📅 Azione stagionale consigliata",
        "messaggio": "Analisi stagionale non disponibile.",
        "azione": None,
        "campagna": None,
        "icon": "📅",
    }

    if mese in {"09", "10"}:
        stagionalita = {
            "mese": mese,
            "titolo": "☀️ Post-estate: capelli stressati",
            "messaggio": "L’estate rovina struttura, lucidità e tenuta del colore. Questo è il momento ideale per ricostruzione e cheratina.",
            "azione": "🧴 Proponi a tutte il pacchetto Ricostruzione Profonda / Cheratina post-mare.",
            "campagna": "Settimana Rinascita Capello",
            "icon": "🌊",
        }
    elif mese == "11":
        stagionalita = {
            "mese": mese,
            "titolo": "🎄 Pre-Natale: prepara l’incasso e proteggi gennaio",
            "messaggio": "Dicembre porterà volume, ma gennaio rischia di svuotarsi se non lo riempi ora.",
            "azione": "🎁 Vendi Gift Card Natale e fissa già ora gli appuntamenti di ricarica colore di gennaio.",
            "campagna": "Gift Card + Rebooking Gennaio",
            "icon": "🎄",
        }
    elif mese == "12":
        stagionalita = {
            "mese": mese,
            "titolo": "✨ Dicembre: massimo valore per cliente",
            "messaggio": "Nel mese più forte non devi solo riempire l’agenda: devi alzare la fiche media.",
            "azione": "👑 Spingi upgrade premium: glow finish, trattamento express, piega luxury, kit regalo retail.",
            "campagna": "Natale Premium Upgrade",
            "icon": "✨",
        }
    elif mese in {"01", "02"}:
        stagionalita = {
            "mese": mese,
            "titolo": "❄️ Inverno: difendi la cassa",
            "messaggio": "Nei mesi freddi molte clienti rallentano. Qui vince chi lavora su mantenimento, pacchetti e ritorno programmato.",
            "azione": "📞 Richiama le clienti ferme e proponi piano colore + trattamento in formula pacchetto.",
            "campagna": "Ritorno in Salone",
            "icon": "❄️",
        }
    elif mese in {"03", "04"}:
        stagionalita = {
            "mese": mese,
            "titolo": "🌸 Primavera: stagione dei cambi look",
            "messaggio": "Le clienti sono più aperte a schiariture, refresh immagine e servizi tecnici trasformativi.",
            "azione": "🎨 Spingi balayage, schiariture soft, face framing e gloss tonalizzanti.",
            "campagna": "Spring Light Week",
            "icon": "🌸",
        }
    elif mese in {"05", "06"}:
        stagionalita = {
            "mese": mese,
            "titolo": "🌞 Pre-estate: protezione e luminosità",
            "messaggio": "Prima del mare le clienti vogliono luce, tenuta e capelli facili da gestire.",
            "azione": "🧴 Vendi protocolli anti-secco, anti-umidità e protezione colore con retail abbinato.",
            "campagna": "Summer Ready Hair",
            "icon": "🌞",
        }
    elif mese in {"07", "08"}:
        stagionalita = {
            "mese": mese,
            "titolo": "🏖️ Estate: retail e mantenimento",
            "messaggio": "In estate non tutte fanno servizi lunghi, ma è il mese perfetto per la vendita di prodotti di mantenimento.",
            "azione": "🛍️ Crea kit sole/mare con shampoo, maschera e protettore UV.",
            "campagna": "Summer Hair Kit",
            "icon": "🏖️",
        }

    # ---------------------------------------------------
    # KPI WOW 5: REDDITIVITA PER POLTRONA
    # ---------------------------------------------------

    fatturato_per_poltrona = None
    benchmark_poltrona = 7500
    gap_poltrona = None

    if inp.incassi_totali_mese is not None and inp.dipendenti and inp.dipendenti > 0:
        fatturato_per_poltrona = inp.incassi_totali_mese / inp.dipendenti
        gap_poltrona = benchmark_poltrona - fatturato_per_poltrona

    poltrona_kpi = {
        "fatturato_per_poltrona": safe_round(fatturato_per_poltrona),
        "benchmark": benchmark_poltrona,
        "gap": safe_round(gap_poltrona),
        "insight": None,
        "azione": None,
    }

    if fatturato_per_poltrona is not None:
        if fatturato_per_poltrona < 4500:
            poltrona_kpi["insight"] = "🚨 Ogni poltrona produce troppo poco fatturato rispetto al potenziale del settore."
            poltrona_kpi["azione"] = "Aumenta servizi tecnici e fiche media per sfruttare meglio ogni postazione."
        elif fatturato_per_poltrona < benchmark_poltrona:
            poltrona_kpi["insight"] = "🟡 Il salone produce ma sotto il benchmark medio."
            poltrona_kpi["azione"] = "Ottimizza agenda, upsell e mix servizi."
        else:
            poltrona_kpi["insight"] = "🏆 Ottima redditività per postazione."
            poltrona_kpi["azione"] = "Proteggi questo livello e consolida servizi premium."


    # ---------------------------------------------------
    # KPI WOW 6: SIMULATORE CRESCITA FATTURATO
    # ---------------------------------------------------

    simulatore_crescita = {
        "incremento_fiche_media": None,
        "incremento_annuo": None,
        "messaggio": None,
    }

    if fiche_media is not None and inp.numero_clienti_mese:

        aumento_target = 7

        incremento_mensile = aumento_target * inp.numero_clienti_mese
        incremento_annuo = incremento_mensile * 12

        simulatore_crescita["incremento_fiche_media"] = aumento_target
        simulatore_crescita["incremento_annuo"] = safe_round(incremento_annuo)

        simulatore_crescita["messaggio"] = (
            f"Se aumenti la fiche media di soli {aumento_target}€ per cliente "
            f"il salone può generare circa {safe_round(incremento_annuo)}€ in più all'anno."
        )


    # ---------------------------------------------------
    # KPI WOW 7: DIAGNOSI SATURAZIONE AGENDA
    # ---------------------------------------------------

    saturazione_agenda = None
    saturazione_target = 0.80
    perdita_potenziale = None

    if inp.numero_clienti_mese and inp.ore_lavorate_mese and inp.ore_lavorate_mese > 0:
        clienti_per_ora = inp.numero_clienti_mese / inp.ore_lavorate_mese
        saturazione_agenda = min(clienti_per_ora / 0.5, 1)  # ipotesi 30 min per cliente medio

    agenda_kpi = {
        "saturazione_agenda": safe_round(saturazione_agenda, 2) if saturazione_agenda is not None else None,
        "target": saturazione_target,
        "perdita_potenziale": None,
        "insight": None,
        "azione": None,
    }

    if saturazione_agenda is not None:

        if fiche_media and inp.numero_clienti_mese:
            clienti_target = inp.numero_clienti_mese * (saturazione_target / max(saturazione_agenda, 0.01))
            perdita_clienti = max(0, clienti_target - inp.numero_clienti_mese)
            perdita_potenziale = perdita_clienti * fiche_media
            agenda_kpi["perdita_potenziale"] = safe_round(perdita_potenziale)

        if saturazione_agenda < 0.55:
            agenda_kpi["insight"] = "🚨 Agenda troppo vuota: molte ore della giornata non stanno generando fatturato."
            agenda_kpi["azione"] = "Attiva campagne di richiamo clienti dormienti e promuovi servizi tecnici ad alto valore."

        elif saturazione_agenda < 0.75:
            agenda_kpi["insight"] = "🟡 Agenda discreta ma migliorabile: esistono ancora slot non monetizzati."
            agenda_kpi["azione"] = "Ottimizza il rebooking e inserisci servizi brevi tra appuntamenti lunghi."

        else:
            agenda_kpi["insight"] = "🏆 Agenda ben saturata: il tempo del salone viene sfruttato bene."
            agenda_kpi["azione"] = "Ora lavora sull'aumento della fiche media e servizi premium."

    # ---------------------------------------------------
    # EXECUTIVE SUMMARY
    # ---------------------------------------------------
    if stability_status == "Critical":
        executive_summary = "🚨 Salone esposto a rischio elevato. Devi proteggere subito cassa, margine e saturazione agenda."
    elif stability_status == "Risk":
        executive_summary = "⚠️ Il salone ha basi presenti ma non consolidate. Priorità: alzare resa oraria, retail e servizi tecnici."
    elif stability_status == "Attention":
        executive_summary = "🟡 Salone in discreta salute, ma con forte spazio di miglioramento su marginalità e posizionamento."
    else:
        executive_summary = "🏆 Salone solido. Ora devi consolidare brand, aumentare il valore medio cliente e mantenere il vantaggio."

    # ---------------------------------------------------
    # ANALISI COMPETITIVA
    # ---------------------------------------------------
    competitors_analysis = []

    if margine_pct is not None:
        if margine_pct >= b_margin_good:
            competitors_analysis.append({
                "title": "Marginalità Leader",
                "icon": "🏆",
                "text": "Ottimo controllo del costo tecnico e buon posizionamento prezzi. Il salone trattiene valore.",
                "color": "#10b981",
            })
        elif margine_pct >= b_margin_bad:
            competitors_analysis.append({
                "title": "Marginalità in Media",
                "icon": "⚖️",
                "text": "I margini sono discreti ma vulnerabili a sprechi colore, listino basso o servizi troppo leggeri.",
                "color": "#f59e0b",
            })
        else:
            competitors_analysis.append({
                "title": "Svantaggio sui Margini",
                "icon": "🚨",
                "text": "Stai trattenendo troppo poco da ogni servizio: prezzo, spreco tecnico o mix servizi sono da correggere.",
                "color": "#ef4444",
            })

    if runway_mesi is not None:
        if runway_mesi >= b_runway_good:
            competitors_analysis.append({
                "title": "Cassa Superiore",
                "icon": "🛡️",
                "text": "Hai una protezione finanziaria buona. Il salone può affrontare eventuali cali con più serenità.",
                "color": "#10b981",
            })
        elif runway_mesi >= b_runway_bad:
            competitors_analysis.append({
                "title": "Autonomia Standard",
                "icon": "🟡",
                "text": "La cassa regge, ma non consente errori prolungati su agenda, costi o bassa stagione.",
                "color": "#f59e0b",
            })
        else:
            competitors_analysis.append({
                "title": "Rischio Finanziario",
                "icon": "🚨",
                "text": "La liquidità è troppo corta. Serve una reazione immediata per aumentare incasso e proteggere i flussi.",
                "color": "#ef4444",
            })

    if conversione is not None and b_conv_good > 0:
        if conversione >= b_conv_good:
            competitors_analysis.append({
                "title": "Retail Eccellente",
                "icon": "🧴",
                "text": "Il salone sa monetizzare bene anche senza fatica fisica aggiuntiva. Ottimo presidio del mantenimento a casa.",
                "color": "#10b981",
            })
        else:
            competitors_analysis.append({
                "title": "Retail Debole",
                "icon": "📉",
                "text": "Le clienti escono senza portare a casa prodotti. Stai perdendo margine facile e ricorrente.",
                "color": "#ef4444",
            })

    if resa_oraria_team is not None:
        if resa_oraria_team >= 35:
            competitors_analysis.append({
                "title": "Team ad Alta Produttività",
                "icon": "✂️",
                "text": "Ogni ora lavorata viene valorizzata bene. Il tempo del salone produce.",
                "color": "#10b981",
            })
        elif resa_oraria_team >= 25:
            competitors_analysis.append({
                "title": "Produttività Intermedia",
                "icon": "⏱️",
                "text": "Buon livello operativo, ma ci sono ancora ore che non esprimono pieno valore.",
                "color": "#f59e0b",
            })
        else:
            competitors_analysis.append({
                "title": "Produttività Bassa",
                "icon": "🪑",
                "text": "C'è troppo valore disperso tra tempi morti, servizi poco redditizi o scarso upsell.",
                "color": "#ef4444",
            })

    if not competitors_analysis:
        competitors_analysis.append({
            "title": "Dati Insufficienti",
            "icon": "🔍",
            "text": "Inserisci più dati economici e operativi per sbloccare la diagnosi avanzata del salone.",
            "color": "#64748b",
        })

    # ---------------------------------------------------
    # DECISIONI MANAGERIALI
    # ---------------------------------------------------
    decisions = {
        "cash": (
            "💰 Urgenza alta: ridurre uscite fisse non essenziali e aumentare immediatamente l’incasso medio giornaliero."
            if risk_cash >= 0.55
            else "💰 La liquidità è sotto controllo: mantieni il presidio settimanale."
        ),
        "margini": (
            "✂️ Urgenza alta: verifica listino, spreco tecnico e protocollo colore. Ogni servizio deve lasciare più margine."
            if risk_margini >= 0.55
            else "✂️ Margini discreti: ora lavora di precisione su pricing e mix servizi."
        ),
        "acq": (
            "🧴 Urgenza alta: implementa script di retail e upsell alla postazione e al lavatesta."
            if risk_acq >= 0.55
            else "🧴 Flusso aggiuntivo discreto: continua a sviluppare retail e mantenimento."
        ),
    }

    # ---------------------------------------------------
    # ACTION PLAN WOW
    # ---------------------------------------------------
    action_plan = [
        "🎯 Comunica ogni mattina al team il Numero Magico del giorno.",
        "🧴 Obbliga ogni postazione a proporre almeno 1 prodotto mantenimento per cliente target.",
        "✂️ Trasforma ogni tempo di posa in opportunità di upsell o riordino agenda.",
        "⚖️ Usa sempre la bilancia per il colore: ogni grammo sprecato è margine perso.",
        "📸 Pubblica prima/dopo reali dei servizi più redditizi, non solo pieghe.",
        "🎨 Proteggi il tecnico in agenda: meno servizi leggeri, più servizi trasformativi.",
        "👑 Alza la fiche media con upgrade premium facili da spiegare.",
        "🎓 Allena il team con uno script unico per retail, trattamento e rebooking.",
        "📞 Richiama le clienti dormienti e proponi ritorno programmato.",
        "🗓️ Inserisci campagne mensili in base alla stagione, non improvvisare le promo.",
    ]

    # Azioni aggiuntive intelligenti in base ai dati
    strategic_actions = []

    if piegacificio_alert["attivo"]:
        strategic_actions.append("🚨 Blocco immediato: aumenta la quota di servizi tecnici nelle prossime 2 settimane.")

    if conversione is not None and conversione < 0.10:
        strategic_actions.append("🧴 Retail boost: crea kit casa e fai scegliere il prodotto davanti allo specchio, non alla cassa.")

    if fiche_media is not None and fiche_media < 60:
        strategic_actions.append("💳 Fiche media bassa: costruisci 3 upgrade semplici da 10€, 20€ e 30€.")

    if resa_oraria_team is not None and resa_oraria_team < 25:
        strategic_actions.append("⏱️ Ogni ora va monetizzata meglio: riduci tempi morti, ritardi e servizi senza profondità.")

    if inp.modello and inp.modello.lower() == "premium":
        strategic_actions.append("👑 Salone premium: smetti di comunicare sconto, comunica trasformazione, firma stilistica e mantenimento.")

    if inp.tipologia_clienti and inp.tipologia_clienti.lower() == "alta":
        strategic_actions.append("💆‍♀️ Clientela frequente: sfrutta il ritorno abituale per inserire pacchetti rituali e membership.")

    if inp.tipologia_clienti and inp.tipologia_clienti.lower() == "bassa":
        strategic_actions.append("🎨 Clientela occasionale: aumenta il valore di ogni visita con servizi tecnici ad alto impatto.")

    # ---------------------------------------------------
    # BENCHMARK RESULTS
    # ---------------------------------------------------
    def bench_status(value, target):
        if value is None:
            return None
        if value > target:
            return "above"
        if value < target:
            return "below"
        return "equal"

    benchmark_results = {
        "runway": {
            "value": runway_mesi,
            "target": b_runway_good,
            "gap": (runway_mesi - b_runway_good) if runway_mesi is not None else None,
            "status": bench_status(runway_mesi, b_runway_good),
        },
        "margine": {
            "value": margine_pct,
            "target": b_margin_good,
            "gap": (margine_pct - b_margin_good) if margine_pct is not None else None,
            "status": bench_status(margine_pct, b_margin_good),
        },
        "conversione": {
            "value": conversione,
            "target": b_conv_good,
            "gap": (conversione - b_conv_good) if conversione is not None else None,
            "status": bench_status(conversione, b_conv_good),
        },
        "break_even": {
            "value": break_even_ratio,
            "target": b_be_good,
            "gap": (break_even_ratio - b_be_good) if break_even_ratio is not None else None,
            "status": bench_status(break_even_ratio, b_be_good),
        },
    }

    # ---------------------------------------------------
    # RETURN FINALE
    # ---------------------------------------------------
    return {
        "triade": {
            "meta": {
                "settore": inp.settore,
                "modello": inp.modello,
                "mese_riferimento": inp.mese_riferimento,
                "created_at": utc_now_iso(),
                "dimensione": inp.dimensione,
                "dipendenti": inp.dipendenti,
                "area_geografica": inp.area_geografica,
                "fatturato": inp.fatturato,
                "tipologia_clienti": inp.tipologia_clienti,
                "benchmark_settore": {
                    "settore_riferimento": bench.sector_name if bench else "Salone Media Nazionale",
                    "margine_target": b_margin_good,
                    "conversione_target": b_conv_good,
                    "runway_target": b_runway_good,
                    "be_target": b_be_good,
                },
            },
            "state": {
                "overall": stability_status,
                "overall_score": stability_score,
                "confidence": confidence,
                "summary": executive_summary,
                "business_stability": stability,
                "maturity_score": triad_index,
                "maturity_label": maturity_label,
                "resilience_index": resilience_index,
                "resilience_label": resilience_label,
                "critical_kpis": critical_kpis,
                "competitive_positioning": competitors_analysis,
            },
            "risks": {
                "cash": round(risk_cash, 4),
                "margini": round(risk_margini, 4),
                "acq": round(risk_acq, 4),
            },
            "kpi": {
                "runway_mesi": runway_mesi,
                "margine_pct": margine_pct,
                "conversione": conversione,
                "break_even_ratio": break_even_ratio,
                "burn_cash_ratio": burn_cash_ratio,
                "fiche_media": fiche_media,
                "incassi_totali_mese": inp.incassi_totali_mese,
                "costi_fissi_mese": inp.costi_fissi_mese,
                "cassa_attuale": inp.cassa_attuale,
                "retail_label": label_retail(conversione),
            },
            "wow": {
                "numero_magico_domani": numero_magico,
                "produttivita_staff": produttivita_staff,
                "diagnosi_piegacificio": piegacificio_alert,
                "calendario_stagionale": stagionalita,
                "redditivita_poltrona": poltrona_kpi,
                "simulatore_crescita": simulatore_crescita,
                "diagnosi_agenda": agenda_kpi,
            },
            "decisions": decisions,
            "action_plan": action_plan,
            "strategic_actions": strategic_actions,
        },
        "benchmark_results": benchmark_results,
    }