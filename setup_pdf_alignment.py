import os

print("🚀 Allineamento del Report PDF in corso...")

# ==========================================
# 1. RISCRITTURA DI PAGES.PY CON I NUOVI WIDGET
# ==========================================
pages_code = """from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from .config import STYLES

def create_cover_page(meta, state):
    elements = []
    elements.append(Spacer(1, 100))
    elements.append(Paragraph("STRATEGIC ADVISORY REPORT", STYLES["CoverTitle"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Settore: {meta.get('settore', 'N/A')}", STYLES["CoverSubtitle"]))
    elements.append(Paragraph(f"Data Analisi: {meta.get('mese_riferimento', 'N/A')}", STYLES["CoverSubtitle"]))
    
    elements.append(Spacer(1, 60))
    score = state.get("overall_score", 0)
    
    score_data = [[f"Business Stability Score: {score}/100"]]
    t = Table(score_data, colWidths=[400])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 16),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 15),
    ]))
    elements.append(t)
    return elements

def create_executive_summary(state, kpi):
    elements = []
    elements.append(Paragraph("1. Executive Summary", STYLES["Heading1"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(state.get("summary", "N/A"), STYLES["Normal"]))
    elements.append(Spacer(1, 20))
    
    # AI STRATEGIC MEMO
    ai_memo = state.get("ai_memo", "")
    if ai_memo and not ai_memo.startswith("⚠️"):
        memo_data = [[Paragraph("<b>AI Executive Memo</b>", STYLES["Normal"])],
                     [Paragraph(ai_memo.replace('\\n', '<br/>'), STYLES["Normal"])]]
        t_memo = Table(memo_data, colWidths=[450])
        t_memo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f5f3ff')),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#faf5ff')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#334155')),
            ('LINEBEFORE', (0,0), (0,-1), 4, colors.HexColor('#8b5cf6')),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(KeepTogether([t_memo]))
        elements.append(Spacer(1, 25))

    elements.append(Paragraph("Posizionamento Competitivo", STYLES["Heading2"]))
    elements.append(Spacer(1, 10))
    for pos in state.get("competitive_positioning", []):
        elements.append(Paragraph(f"<b>{pos['title']}</b>: {pos['text']}", STYLES["Normal"]))
        elements.append(Spacer(1, 8))
        
    return elements

def create_financial_projections(fin):
    elements = []
    elements.append(Paragraph("2. Financial Intelligence & Stress Test", STYLES["Heading1"]))
    elements.append(Spacer(1, 15))
    
    # EBITDA Gap
    gap = fin.get("ebitda_gap", 0)
    elements.append(Paragraph("<b>Inefficiency Cost (EBITDA Gap Annualizzato)</b>", STYLES["Heading2"]))
    elements.append(Paragraph(f"Margine annuo lasciato sul tavolo a causa della distanza dall'efficienza media del settore: <b>Euro {gap:,.0f}</b>".replace(',', '.'), STYLES["Normal"]))
    elements.append(Spacer(1, 20))
    
    # Stress Test & Simulator Table
    elements.append(Paragraph("<b>Simulazioni di Cassa e Scenari (Mesi di Sopravvivenza)</b>", STYLES["Heading2"]))
    
    stress = fin.get("stress_test", {})
    sim = fin.get("simulator", {})
    
    data = [
        ["Scenario", "Impatto Stimato", "Runway Prevista"],
        ["Crisi: Ricavi -20%", "Shock di Mercato", f"{stress.get('shock_20', 0)} mesi"],
        ["Crisi: Ricavi -30%", "Shock Severo", f"{stress.get('shock_30', 0)} mesi"],
        ["Crisi: Ritardo Incassi", "Problemi di Credito", f"{stress.get('late_payments', 0)} mesi"],
        ["Azione: Taglio Costi 10%", "Efficienza Base", f"{sim.get('cost_cut_10', 0)} mesi"],
        ["Azione: Taglio Costi 20%", "Ristrutturazione", f"{sim.get('cost_cut_20', 0)} mesi"],
        ["Azione: Ricavi +10%", "Crescita", f"{sim.get('rev_up_10', 0)} mesi"]
    ]
    
    t = Table(data, colWidths=[180, 150, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0,1), (-1,3), colors.HexColor('#fff5f5')), # Rosso chiaro per crisi
        ('BACKGROUND', (0,4), (-1,-1), colors.HexColor('#f0fdf4')), # Verde chiaro per azioni
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 20))
    return elements

def create_benchmark_analysis(bench_results):
    elements = []
    elements.append(Paragraph("3. Gap Analysis vs Mercato", STYLES["Heading1"]))
    elements.append(Spacer(1, 15))
    
    data = [["KPI", "Tuo Valore", "Target Mercato", "Status"]]
    def fmt(val, is_pct=False):
        if val is None: return "N/A"
        if is_pct: return f"{val*100:.1f}%"
        return f"{val:.1f}"

    for key, res in bench_results.items():
        is_pct = key in ["margine", "conversione"]
        val_str = fmt(res["value"], is_pct)
        tgt_str = fmt(res["target"], is_pct)
        status = res["status"]
        if status == "above": status_str = "Leader"
        elif status == "below": status_str = "Critico"
        else: status_str = "In Linea"
        data.append([key.replace("_", " ").title(), val_str, tgt_str, status_str])

    t = Table(data, colWidths=[120, 100, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(t)
    return elements

def create_action_plan(actions):
    elements = []
    elements.append(Paragraph("4. Action Plan", STYLES["Heading1"]))
    elements.append(Spacer(1, 15))
    for i, action in enumerate(actions, 1):
        elements.append(Paragraph(f"<b>Fase {i}:</b> {action}", STYLES["Normal"]))
        elements.append(Spacer(1, 8))
    return elements
"""
with open('app/services/pdf/pages.py', 'w') as f:
    f.write(pages_code)


# ==========================================
# 2. RISCRITTURA DI ENGINE.PY PER INTEGRARE PAGES.PY
# ==========================================
engine_code = """import os
from io import BytesIO
from typing import Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Spacer, PageBreak

from .config import setup_pdf_fonts, PDF_MARGINS
from .pages import (
    create_cover_page,
    create_executive_summary,
    create_financial_projections,
    create_benchmark_analysis,
    create_action_plan
)

def generate_scan_pdf_enterprise(out_path: Any, scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Any:
    setup_pdf_fonts()
    is_memory = isinstance(out_path, BytesIO)
    if not is_memory:
        out_path = str(out_path)
        
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        rightMargin=PDF_MARGINS["right"], leftMargin=PDF_MARGINS["left"],
        topMargin=PDF_MARGINS["top"], bottomMargin=PDF_MARGINS["bottom"]
    )
    
    elements = []
    triade = vm.get("triade", vm)
    meta = triade.get("meta", {})
    state = triade.get("state", {})
    kpi = triade.get("kpi", {})
    fin_proj = triade.get("financial_projections", {})
    bench_results = vm.get("benchmark_results", {})
    
    # 1. Copertina
    elements.extend(create_cover_page(meta, state))
    elements.append(PageBreak())
    
    # 2. Executive Summary & AI Memo
    elements.extend(create_executive_summary(state, kpi))
    elements.append(Spacer(1, 20))
    
    # 3. Financial Intelligence (NUOVO)
    if fin_proj:
        elements.extend(create_financial_projections(fin_proj))
        elements.append(PageBreak())
    
    # 4. Benchmark
    if bench_results:
        elements.extend(create_benchmark_analysis(bench_results))
        elements.append(PageBreak())
        
    # 5. Action Plan
    actions = triade.get("action_plan", [])
    if actions:
        elements.extend(create_action_plan(actions))
    
    doc.build(elements)
    return out_path

# Alias retrocompatibilità
def generate_scan_pdf(out_path, scan_meta, vm): return generate_scan_pdf_enterprise(out_path, scan_meta, vm)
def generate_report(out_path, scan_meta, vm): return generate_scan_pdf_enterprise(out_path, scan_meta, vm)
def generate_one_pager(out_path, scan_meta, vm): return generate_scan_pdf_enterprise(out_path, scan_meta, vm)
"""
with open('app/services/pdf/engine.py', 'w') as f:
    f.write(engine_code)

print("✅ Motore PDF aggiornato con successo! Intelligenza Artificiale e Stress Test inclusi nel documento.")
