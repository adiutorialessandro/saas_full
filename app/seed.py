from .extensions import db
from .models.plan import Plan


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