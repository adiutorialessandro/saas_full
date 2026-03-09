<!DOCTYPE html>
<html lang="en">
<head>
  <!-- head content -->
</head>
<body>
  <!-- other content -->
  <div class="dashboard-hero-card">
      <div class="dash-hero-copy">
        <div class="dash-kicker">TRIAD INSIGHT</div>
        <h1>Scopri cosa blocca davvero la crescita della tua azienda.</h1>
        <p class="dash-lead">
          Triad Insight analizza finanza, vendite e struttura operativa.
        </p>
        <p class="dash-sublead">
          Genera un report chiaro con priorità, alert e azioni concrete.
        </p>
        <p class="dash-body">
          Triad Insight raccoglie dati essenziali, legge i segnali critici del business e produce un report leggibile immediatamente convertibile in azioni concrete.
        </p>
      </div>
      <!-- hero actions remain unchanged -->
  </div>
  <!-- other content -->
</body>
</html>

---

<div class="report-card">
  <div class="card-title card-title-inline">
    <span>Cash Runway</span>
    <span class="info-tip" tabindex="0">
      i
      <span class="info-bubble">
        Il cash runway indica per quanti mesi la tua azienda può continuare a operare con la cassa disponibile, mantenendo l’attuale ritmo di spesa.
      </span>
    </span>
  </div>
  <div class="kpi-value">
    {% if vm.kpi.runway_mesi is not none %}
      {{ "%.1f"|format(vm.kpi.runway_mesi) }} mesi
    {% else %}
      —
    {% endif %}
  </div>
</div>

---

/* Dashboard hero copy */
.dash-kicker{
  font-size:12px;
  text-transform:uppercase;
  letter-spacing:1px;
  font-weight:700;
  color:#3b82f6;
  margin-bottom:10px;
}

.dash-lead{
  font-size:20px;
  line-height:1.4;
  color:#475569;
  margin:10px 0 0;
}

.dash-sublead{
  font-size:18px;
  line-height:1.4;
  color:#0f172a;
  margin:10px 0 0;
  font-weight:600;
}

.dash-body{
  font-size:15px;
  line-height:1.6;
  color:#64748b;
  margin-top:14px;
  max-width:980px;
}

/* Tooltip KPI */
.card-title-inline{
  display:flex;
  align-items:center;
  gap:8px;
}

.info-tip{
  position:relative;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  width:18px;
  height:18px;
  border-radius:999px;
  background:#e2e8f0;
  color:#0f172a;
  font-size:12px;
  font-weight:700;
  cursor:help;
  line-height:1;
}

.info-bubble{
  position:absolute;
  left:24px;
  top:-8px;
  width:280px;
  background:#0f172a;
  color:#fff;
  padding:10px 12px;
  border-radius:10px;
  font-size:12px;
  line-height:1.45;
  box-shadow:0 10px 25px rgba(15,23,42,.22);
  opacity:0;
  visibility:hidden;
  transform:translateY(4px);
  transition:all .18s ease;
  z-index:20;
}

.info-tip:hover .info-bubble,
.info-tip:focus .info-bubble,
.info-tip:focus-within .info-bubble{
  opacity:1;
  visibility:visible;
  transform:translateY(0);
}