import os
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
