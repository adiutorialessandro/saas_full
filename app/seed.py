from .extensions import db
from .models.plan import Plan
from .models.benchmark import SectorBenchmark

def seed_plans() -> None:
    default_plans = [
        {"name": "Starter", "scan_limit": 5, "price_month": 19.0, "is_active": True},
        {"name": "Growth", "scan_limit": 50, "price_month": 49.0, "is_active": True},
        {"name": "Pro", "scan_limit": -1, "price_month": 99.0, "is_active": True},
    ]

    created = 0
    updated = 0

    for item in default_plans:
        plan = Plan.query.filter_by(name=item["name"]).first()

        if not plan:
            plan = Plan(**item)
            db.session.add(plan)
            created += 1
        else:
            changed = False
            for key, value in item.items():
                if getattr(plan, key) != value:
                    setattr(plan, key, value)
                    changed = True
            if changed:
                updated += 1

    db.session.commit()
    print(f"Plans seed completed. Created: {created}, Updated: {updated}")

def seed_benchmarks() -> None:
    # Parametri di eccellenza esclusivi per i Saloni di Acconciature
    saloni_benchmarks = [
        {
            "sector_name": "Salone Donna",
            "margine_lordo_target": 75.0,  # 75% di margine dopo il costo dei prodotti (colore/shampoo)
            "conversione_target": 15.0,    # Almeno 15% degli incassi deve venire dalla vendita prodotti (Retail)
            "runway_minima": 6.0,          # 6 mesi di liquidità per coprire i costi fissi
            "break_even_sano": 1.25        # Gli incassi devono superare di 1.25 volte i costi fissi
        },
        {
            "sector_name": "Barber / Salone Uomo",
            "margine_lordo_target": 85.0,  # L'uomo ha meno costi di prodotto chimico
            "conversione_target": 10.0,    # Rivendita cera/shampoo
            "runway_minima": 6.0,
            "break_even_sano": 1.25
        },
        {
            "sector_name": "Salone Unisex",
            "margine_lordo_target": 78.0,
            "conversione_target": 12.0,
            "runway_minima": 6.0,
            "break_even_sano": 1.25
        },
        {
            "sector_name": "Salone con cabina estetica",
            "margine_lordo_target": 70.0,  # Costi di macchinari abbassano il margine lordo
            "conversione_target": 20.0,    # L'estetica ha un potenziale retail altissimo
            "runway_minima": 6.0,
            "break_even_sano": 1.20
        }
    ]

    created = 0
    updated = 0

    for item in saloni_benchmarks:
        bench = SectorBenchmark.query.filter_by(sector_name=item["sector_name"]).first()

        if not bench:
            bench = SectorBenchmark(**item)
            db.session.add(bench)
            created += 1
        else:
            changed = False
            for key, value in item.items():
                if getattr(bench, key) != value:
                    setattr(bench, key, value)
                    changed = True
            if changed:
                updated += 1

    db.session.commit()
    print(f"Benchmarks Parrucchieri seed completed. Created: {created}, Updated: {updated}")