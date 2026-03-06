from typing import Dict, Any

def stress_cashflow(kpi: Dict[str, Any]):

    cash = kpi.get("cash", 0)
    revenue = kpi.get("revenue", 0)
    costs = kpi.get("costs", 1)

    scenarios = {
        "demand_shock_20": revenue * 0.8,
        "demand_shock_30": revenue * 0.7,
        "late_payments": revenue * 0.75
    }

    results = {}

    for k,v in scenarios.items():

        burn = costs
        runway = cash / max((burn - v),1)

        results[k] = round(runway,2)

    return results
