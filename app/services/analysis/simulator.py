from typing import Dict, Any

def simulate_runway(kpi: Dict[str, Any], change: Dict[str, float]):

    cash = kpi.get("cash", 0)
    burn = kpi.get("burn", 1)
    revenue = kpi.get("revenue", 0)

    burn_new = burn * (1 - change.get("cost_reduction", 0))
    revenue_new = revenue * (1 + change.get("revenue_growth", 0))

    net = revenue_new - burn_new

    if net <= 0:
        return round(cash / burn_new, 2)

    return round(cash / net, 2)


def scenario_matrix(kpi):

    scenarios = {
        "cost_cut_10": simulate_runway(kpi, {"cost_reduction":0.10}),
        "cost_cut_20": simulate_runway(kpi, {"cost_reduction":0.20}),
        "revenue_up_10": simulate_runway(kpi, {"revenue_growth":0.10}),
        "revenue_up_20": simulate_runway(kpi, {"revenue_growth":0.20}),
    }

    return scenarios
