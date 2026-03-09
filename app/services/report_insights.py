from __future__ import annotations

"""
Utility functions used to generate strategic insights for reports.
This module must contain ONLY Python code (no HTML/CSS).
"""

from typing import Dict, Any


def report_header_payload(scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a lightweight payload used by both PDF and HTML reports.
    """

    triad_index = vm.get("triad_index")

    return {
        "company": scan_meta.get("company_name") or scan_meta.get("azienda") or "Azienda",
        "sector": scan_meta.get("settore"),
        "model": scan_meta.get("modello"),
        "reference_month": scan_meta.get("mese_riferimento"),
        "triad_index": triad_index,
    }


def executive_insight(vm: Dict[str, Any]) -> str:
    """
    Generate a short executive-level insight based on the triad index.
    """

    triad = vm.get("triad_index")

    if triad is None:
        return "Dati insufficienti per generare un insight strategico."

    if triad >= 75:
        return (
            "L'azienda mostra una struttura operativa solida con buone prospettive di crescita. "
            "La priorità è accelerare vendite e scalabilità." 
        )

    if triad >= 50:
        return (
            "La crescita è possibile ma frenata da inefficienze operative o commerciali. "
            "Serve una focalizzazione sulle priorità strategiche." 
        )

    return (
        "Il sistema aziendale mostra segnali di fragilità strutturale. "
        "È necessario intervenire rapidamente su finanza, vendite e organizzazione." 
    )


def runway_explanation() -> str:
    """
    Text used in tooltip explaining the meaning of Cash Runway.
    """

    return (
        "Il cash runway indica per quanti mesi l'azienda può continuare a operare "
        "con la cassa disponibile mantenendo l'attuale ritmo di spesa."
    )