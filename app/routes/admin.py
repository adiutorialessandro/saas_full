import functools
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.scan import Scan
from app.models.benchmark import SectorBenchmark
from app.models.plan import Plan

from app.forms import (
    CreateOrganizationForm, 
    CreateOrgUserForm, 
    UpdateOrgUserRoleForm,
    ResetUserPasswordForm, 
    SectorBenchmarkForm, 
    CreatePlanForm, 
    UpdateOrganizationPlanForm
)

bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(f):
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route("/")
@admin_required
def index():
    from sqlalchemy import func
    from datetime import datetime, timedelta

    total_orgs = Organization.query.count()
    total_scans = Scan.query.count()
    total_users = User.query.count()
    
    # Calcolo MRR (Monthly Recurring Revenue) stimato
    mrr = db.session.query(func.sum(Plan.price_month)).join(Organization).filter(Organization.plan_id == Plan.id).scalar() or 0
    
    # Scan nelle ultime 24 ore
    last_24h = datetime.utcnow() - timedelta(days=1)
    scans_24h = Scan.query.filter(Scan.created_at >= last_24h).count()

    # Prepara una riga base per le Org
    orgs = Organization.query.order_by(Organization.created_at.desc()).limit(10).all()
    rows = []
    for org in orgs:
        c_users = Membership.query.filter_by(org_id=org.id).count()
        c_scans = Scan.query.filter_by(org_id=org.id).count()
        rows.append({
            "org": org,
            "users_count": c_users,
            "scans_count": c_scans
        })

    return render_template(
        "admin/index.html", 
        total_orgs=total_orgs, 
        total_scans=total_scans, 
        total_users=total_users, 
        mrr=mrr, 
        scans_24h=scans_24h,
        rows=rows
    )

@bp.route("/organizations")
@admin_required
def organizations():
    orgs = Organization.query.order_by(Organization.created_at.desc()).all()
    rows = []
    for org in orgs:
        c_users = Membership.query.filter_by(org_id=org.id).count()
        c_scans = Scan.query.filter_by(org_id=org.id).count()
        rows.append({"org": org, "users_count": c_users, "scans_count": c_scans})
    return render_template("admin/organizations.html", rows=rows)

@bp.route("/organizations/new", methods=["GET", "POST"])
@admin_required
def create_organization():
    form = CreateOrganizationForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u:
            flash("Utente owner già esistente.", "danger")
            return redirect(url_for('admin.organizations'))
        u = User(email=form.email.data)
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        o = Organization(name=form.name.data)
        db.session.add(o)
        db.session.commit()
        m = Membership(user_id=u.id, org_id=o.id, role="owner")
        db.session.add(m)
        db.session.commit()
        flash("Azienda creata con successo.", "success")
        return redirect(url_for('admin.organizations'))
    return render_template("admin/new_org.html", form=form)

@bp.route("/organizations/<int:org_id>")
@admin_required
def organization_detail(org_id):
    org = Organization.query.get_or_404(org_id)
    memberships = Membership.query.filter_by(org_id=org.id).all()
    scans = Scan.query.filter_by(org_id=org.id).order_by(Scan.created_at.desc()).all()
    return render_template("admin/organization_detail.html", org=org, memberships=memberships, scans=scans)

@bp.route("/organizations/<int:org_id>/users/new", methods=["GET", "POST"])
@admin_required
def create_org_user(org_id):
    org = Organization.query.get_or_404(org_id)
    form = CreateOrgUserForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if not u:
            u = User(email=form.email.data)
            u.set_password(form.password.data)
            db.session.add(u)
            db.session.commit()
        m = Membership.query.filter_by(user_id=u.id, org_id=org.id).first()
        if not m:
            m = Membership(user_id=u.id, org_id=org.id, role=form.role.data)
            db.session.add(m)
            db.session.commit()
            flash("Utente aggiunto all'azienda.", "success")
        else:
            flash("L'utente è già in questa azienda.", "warning")
        return redirect(url_for('admin.organization_detail', org_id=org.id))
    return render_template("admin/new_org_user.html", form=form, org=org)

@bp.route("/users/<int:user_id>/reset_password", methods=["GET", "POST"])
@admin_required
def reset_user_password(user_id):
    u = User.query.get_or_404(user_id)
    form = ResetUserPasswordForm()
    if form.validate_on_submit():
        u.set_password(form.password.data)
        db.session.commit()
        flash(f"Password aggiornata per {u.email}", "success")
        return redirect(url_for('admin.organizations'))
    return render_template("admin/reset_user_password.html", form=form, user=u)

# ==========================================
# FIX: VISUALIZZAZIONE SCANSIONI ADMIN
# ==========================================
@bp.route("/scans/<int:scan_id>")
@admin_required
def view_scan(scan_id):
    from app.routes.scans import _prepare_scan_view_model # Importiamo la logica DRY

    scan = Scan.query.get_or_404(scan_id)
    
    # Decodifichiamo i dati AI in modo sicuro per evitare errori Jinja
    vm = _prepare_scan_view_model(scan)
    
    return render_template("scans/view_scan.html", scan=scan, vm=vm)

@bp.route("/benchmarks", methods=["GET", "POST"])
@admin_required
def benchmarks():
    benchmarks_list = SectorBenchmark.query.all()
    form = SectorBenchmarkForm()
    if form.validate_on_submit():
        b = SectorBenchmark(
            sector_name=form.sector_name.data,
            margine_lordo_target=form.margine_lordo_target.data,
            conversione_target=form.conversione_target.data,
            break_even_sano=form.break_even_sano.data,
            runway_minima=form.runway_minima.data
        )
        db.session.add(b)
        db.session.commit()
        flash("Benchmark creato.", "success")
        return redirect(url_for('admin.benchmarks'))
    return render_template("admin/generic_form.html", form=form, title="Benchmark di Settore", benchmarks=benchmarks_list)

# ==========================================
# GESTIONE SAAS: PIANI TARIFFARI E LIMITI
# ==========================================

@bp.get("/plans")
@admin_required
def plans():
    plans_list = Plan.query.all()
    return render_template("admin/plans.html", plans=plans_list)

@bp.route("/plans/new", methods=["GET", "POST"])
@admin_required
def create_plan():
    form = CreatePlanForm()
    if form.validate_on_submit():
        p = Plan(
            name=form.name.data,
            scan_limit=form.scan_limit.data,
            price_month=form.price_month.data
        )
        db.session.add(p)
        db.session.commit()
        flash("Piano creato con successo.", "success")
        return redirect(url_for('admin.plans'))
    return render_template("admin/generic_form.html", form=form, title="Crea Nuovo Piano")

@bp.route("/organizations/<int:org_id>/update_plan", methods=["GET", "POST"])
@admin_required
def update_org_plan(org_id):
    org = Organization.query.get_or_404(org_id)
    form = UpdateOrganizationPlanForm()
    form.plan_id.choices = [(p.id, p.name) for p in Plan.query.order_by('price_month').all()]
    if request.method == "GET":
        form.plan_id.data = org.plan_id
    if form.validate_on_submit():
        org.plan_id = form.plan_id.data
        db.session.commit()
        flash(f"Piano aggiornato per l'azienda {org.name}.", "success")
        return redirect(url_for('admin.organization_detail', org_id=org.id))
    return render_template("admin/generic_form.html", form=form, title=f"Cambia Piano: {org.name}")

@bp.route("/organizations/<int:org_id>/users/<int:user_id>/role", methods=["GET", "POST"])
@admin_required
def edit_org_user_role(org_id, user_id):
    mem = Membership.query.filter_by(org_id=org_id, user_id=user_id).first_or_404()
    form = UpdateOrgUserRoleForm(obj=mem)
    if form.validate_on_submit():
        mem.role = form.role.data
        db.session.commit()
        flash("Ruolo utente aggiornato.", "success")
        return redirect(url_for('admin.organization_detail', org_id=org_id))
    return render_template("admin/generic_form.html", form=form, title=f"Modifica Ruolo Utente")

@bp.route("/plans/edit/<int:plan_id>", methods=["GET", "POST"])
@admin_required
def edit_plan(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    
    if request.method == "POST":
        plan.name = request.form.get("name")
        plan.scan_limit = int(request.form.get("scan_limit", 0))
        plan.price_month = float(request.form.get("price_month", 0.0))
        plan.stripe_price_id = request.form.get("stripe_price_id")
        
        db.session.commit()
        flash("Piano aggiornato con successo!", "success")
        return redirect(url_for("admin.plans"))
        
    return render_template("admin/edit_plan.html", plan=plan)