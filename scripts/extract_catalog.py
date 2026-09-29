"""Extrae el catálogo de las 37 variables del Excel a CSV y le agrega columnas de control.

Columnas agregadas:
  applies_to  : subpoblación donde la variable existe; fuera de ella es NULL (no cero).
  build_step  : paso en que se construye (por grupo, para que las variables que
                comparten mecánica y se solapan se generen juntas y coherentes).
  status      : pending / built / validated.

Uso: python scripts/extract_catalog.py
"""
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "docs" / "Client_Pulse_37_Variables.xlsx"
OUT = ROOT / "data" / "catalog" / "variables_catalog.csv"

APPLIES_TO = {
    "aum_outflow": "has_investments",
    "salary_deposit_stopped_flag": "has_payroll_stream",
    "recurring_deposit_stopped_flag": "has_any_recurring_stream",
    "recurring_deposit_change_pct": "has_any_recurring_stream",
    "investment_redemption_pct": "has_investments",
    "aum_vs_baseline_pct": "has_investments & history_months>=6",
    "pension_deposit_stopped_flag": "has_pension_stream",
    "business_payroll_stopped_flag": "has_linked_business",
    "fixed_income_maturity_not_reinvested": "has_investments & had_maturities_90d",
    "cash_pct_of_portfolio_chg": "has_investments",
    "return_vs_benchmark": "has_advisory",
    "trustee_change_flag": "has_trust",
    "positions_liquidated_pct": "has_investments",
}

STEP_BY_GROUP = {
    "Balances & AUM": 1,
    "Recurring deposits & flows": 2,
    "Transfers": 3,
    "Investments": 4,
    "Relationship & closures": 5,
    "Banker": 6,
    "Complaints & voice of client": 7,
    "External & composite": 8,
}

# Variables ya construidas y validadas (se actualiza al cerrar cada paso).
BUILT = {"aum_outflow", "deposit_balance_change_pct", "aum_vs_baseline_pct", "deposit_balance_vs_6m_avg_pct",
         "salary_deposit_stopped_flag", "recurring_deposit_stopped_flag", "recurring_deposit_change_pct",
         "net_deposit_flow", "pension_deposit_stopped_flag", "business_payroll_stopped_flag",
         "external_transfer_pct_of_balance", "new_external_destinations", "transfer_to_competitor_bank_amount",
         "external_transfer_acceleration", "net_external_flow", "external_destination_concentration",
         "outflow_vs_baseline_pct", "investment_redemption_pct", "fixed_income_maturity_not_reinvested",
         "cash_pct_of_portfolio_chg", "return_vs_benchmark", "positions_liquidated_pct",
         "products_closed", "accounts_closed", "share_of_wallet", "share_of_wallet_change", "trustee_change_flag",
         "banker_change_6m_flag", "contact_gap_ratio", "client_reply_rate", "meetings_cancelled_by_client",
         "complaint_escalated_flag", "complaint_age_days", "repeat_complaint_flag", "relationship_dissatisfaction_flag",
         "multi_signal_flag", "bureau_new_mortgage_elsewhere"}

COLS = {
    "#": "id", "Priority": "priority", "Group": "group", "Variable": "variable",
    "Business definition": "definition", "Calculation (simplified)": "calculation",
    "Source system": "source_system", "Window(s)": "windows", "Data type / unit": "data_type",
    "Considerations & exclusions": "considerations", "Alert threshold (illustrative)": "alert_threshold",
    "Predictive strength": "predictive_strength", "Feasibility": "feasibility",
    "Detailed logic (for data engineering)": "detailed_logic",
}


def main() -> None:
    ws = openpyxl.load_workbook(XLSX, read_only=True)["Variables"]
    rows = list(ws.iter_rows(values_only=True))
    df = pd.DataFrame(rows[1:], columns=rows[0]).dropna(subset=["Variable"])
    df = df[list(COLS)].rename(columns=COLS)
    df["id"] = df["id"].astype(int)
    df["applies_to"] = df["variable"].map(APPLIES_TO).fillna("all")
    df["build_step"] = df["group"].map(STEP_BY_GROUP).astype(int)
    df["status"] = df["variable"].map(lambda v: "validated" if v in BUILT else "pending")
    assert len(df) == 37 and df["variable"].is_unique, "El Excel debe tener 37 variables únicas"
    assert df["build_step"].notna().all()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"{len(df)} variables -> {OUT.relative_to(ROOT)}")
    print(df.groupby(["build_step", "group"]).size().to_string())


if __name__ == "__main__":
    main()
