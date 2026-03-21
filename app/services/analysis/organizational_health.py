"""
Organizational Health Index (OHI) / McKinsey 7S
Motore di valutazione della salute della struttura organizzativa.
"""
from typing import Dict, Any

def _safe_int(val: Any, default: int = 3) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def calculate_ohi_score(quiz: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcola l'OHI mappando i punteggi 1-5 su 4 macro-pilastri direzionali.
    """
    # 1. Alignment (Strategy, Shared Values)
    alignment = (_safe_int(quiz.get("chiarezza_obiettivi")) + 
                 _safe_int(quiz.get("condivisione_valori"))) / 10 * 100

    # 2. Execution (Systems, Structure)
    execution = (_safe_int(quiz.get("efficacia_sistemi")) + 
                 _safe_int(quiz.get("velocita_decisionale"))) / 10 * 100

    # 3. Renewal (Skills, Innovation)
    renewal = (_safe_int(quiz.get("apertura_cambiamento")) + 
               _safe_int(quiz.get("apprendimento_errore"))) / 10 * 100

    # 4. Relationships (Style, Staff)
    relationships = (_safe_int(quiz.get("fiducia_leadership")) + 
                     _safe_int(quiz.get("clima_team"))) / 10 * 100

    # Punteggio Medio Globale
    ohi_score = (alignment + execution + renewal + relationships) / 4
    
    if ohi_score >= 80:
        status = "Livello Elite"
    elif ohi_score >= 60:
        status = "Fisiologico/Sano"
    elif ohi_score >= 40:
        status = "Sotto-Performante"
    else:
        status = "Criticità Sistemica"

    # Generazione Insights Dinamici
    insights = []
    if alignment < 50:
        insights.append("Scollegamento Strategico: Il team operativo è disallineato rispetto alla visione del management.")
    if execution < 50:
        insights.append("Collo di Bottiglia Operativo: I sistemi attuali (software/processi) rallentano pesantemente l'esecuzione.")
    if renewal < 50:
        insights.append("Stagnazione delle Competenze: Rischio di obsolescenza tecnologica e resistenza culturale al cambiamento.")
    if relationships < 50:
        insights.append("Tossicità Organizzativa: Sfiducia nella leadership e clima teso rischiano di generare turnover dei talenti.")
        
    if not insights:
        insights.append("La struttura organizzativa mostra un eccellente equilibrio tra cultura, sistemi ed esecuzione.")

    return {
        "score": round(ohi_score, 1),
        "status": status,
        "pillars": {
            "alignment": round(alignment, 1),
            "execution": round(execution, 1),
            "renewal": round(renewal, 1),
            "relationships": round(relationships, 1)
        },
        "insights": insights
    }