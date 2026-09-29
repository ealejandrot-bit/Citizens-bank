"""Rutas, semilla, parámetros, carga y utilidades comunes (pasos 00–17)."""
from __future__ import annotations

import hashlib
import os
import random
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "client_pulse_synthetic.xlsx"
SHEET = "client_pulse_synthetic"
PROC = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
FIGS = ROOT / "outputs" / "figs"
MODEL = ROOT / "outputs" / "model"
SCORES = ROOT / "outputs" / "scores"
REPORTS = ROOT / "reports"

SEED = 42

# Escala [DEF]: S0 = 600 @ O0 = 20:1 (buenos:malos), PDO = 40
S0, O0, PDO = 600, 20.0, 40
FACTOR = PDO / np.log(2)                 # 57.71
OFFSET = S0 - FACTOR * np.log(O0)        # 427.12

ID = "household_id"
OUTCOMES = ["hard_churn_6m", "soft_churn_3m", "value_lost_6m", "churn_excluded"]
COMPOSITES = ["multi_signal_flag", "multi_signal_count"]
PROHIBITED = OUTCOMES + [ID, "snapshot_date"]           # nunca predictores
THETA_B = 0.25                                           # umbral de pérdida para el target B [DEF propuesta, I-1]

# Missing estructural: variable → columna gatillo (NaN ⟺ gatillo = False)
STRUCTURAL = {
    "has_investments": ["aum", "aum_outflow_90d", "aum_outflow_pct_90d", "investment_redemption_pct",
                        "positions_liquidated_pct", "cash_pct_of_portfolio_chg", "aum_vs_baseline_pct"],
    "has_pension_stream": ["pension_deposit_stopped_flag"],
    "has_linked_business": ["business_payroll_stopped_flag"],
    "has_payroll_stream": ["salary_deposit_stopped_flag"],
    "has_trust": ["trustee_change_flag"],
    "has_advisory": ["return_vs_benchmark"],
}


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def load_raw() -> pd.DataFrame:
    """Lee data/raw (solo lectura). Cachea en data/processed/raw_cache.parquet, invalidado por hash del xlsx."""
    PROC.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(RAW.read_bytes()).hexdigest()[:16]
    cache = PROC / f"raw_cache_{h}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = pd.read_excel(RAW, sheet_name=SHEET)
    df.to_parquet(cache, index=False)
    return df


def eligible(df: pd.DataFrame) -> pd.Series:
    return ~df["churn_excluded"].astype(bool)


def loss_ratio(df: pd.DataFrame) -> pd.Series:
    return df["value_lost_6m"] / df["relationship_value"]


def targets(df: pd.DataFrame, theta: float = THETA_B) -> pd.DataFrame:
    """Targets A–D. B: hard ∪ (soft con pérdida ≥ θ); soft con pérdida < θ = indeterminado (NaN)."""
    el = eligible(df)
    hard = df["hard_churn_6m"] == 1
    soft = df["soft_churn_3m"] == 1
    r = loss_ratio(df)
    out = pd.DataFrame(index=df.index)
    out["y_A"] = np.where(el, hard.astype(float), np.nan)
    indet_B = el & soft & (r < theta)
    out["y_B"] = np.where(el & ~indet_B, (hard | (soft & (r >= theta))).astype(float), np.nan)
    out["y_B_indet"] = indet_B
    out["y_C"] = np.where(el, (hard | soft).astype(float), np.nan)
    out["y_D"] = np.where(el, soft.astype(float), np.nan)
    return out


def tag(x, kind: str = "DATA") -> str:
    return f"{x} [{kind}]"


def save_table(df: pd.DataFrame, name: str, index: bool = False) -> Path:
    TABLES.mkdir(parents=True, exist_ok=True)
    p = TABLES / f"{name}.csv"
    df.to_csv(p, index=index)
    return p


def md_table(df: pd.DataFrame, floatfmt: str = ",.4g") -> str:
    return df.to_markdown(index=False, floatfmt=floatfmt)


EXCLUDED_G13 = ["age_primary", "bureau_new_mortgage_elsewhere"]          # [DEF-default] G1-3
DERIVED = ["log_rv", "aum_share", "deposit_share", "streams_stopped_count", "n_streams_eligible", "n_products_held",
           "outflow_x_contact_gap", "competitor_x_new_destinations",
           "ind_sin_dato_client_reply_rate", "ind_sin_dato_meetings_cancelled_by_client",
           "ind_sin_dato_relationship_dissatisfaction_flag", "ind_sin_dato_fixed_income_maturity_not_reinvested",
           "aum_outflow_pct_90d_peer", "net_deposit_flow_pct_90d_peer", "contact_gap_ratio_peer"]


def candidates(include_composites: bool = False) -> list[str]:
    """Predictores candidatos: proveedor (uso = predictor) − G1-3 + derivadas (+ compuestos si se pide)."""
    d = pd.read_csv(TABLES / "step02_dictionary.csv")
    prov = ["segment_uhnw" if c == "segment" else c for c in d.loc[d.uso == "predictor", "columna"] if c not in EXCLUDED_G13]
    return prov + DERIVED + (COMPOSITES if include_composites else [])


def load_split(part: str) -> pd.DataFrame:
    """dev o val con todas las features (features.parquet) + targets / pesos / folds."""
    F = pd.read_parquet(PROC / "features.parquet")
    s = pd.read_parquet(PROC / f"{part}.parquet")
    keep = [c for c in s.columns if c not in F.columns or c == ID]
    out = s[keep].merge(F, on=ID, how="left")
    out["segment_uhnw"] = (out["segment"] == "UHNW").astype(int)
    for c in out.columns:
        if out[c].dtype == bool and not c.startswith(("in_pop_", "y_")):     # máscaras de población quedan bool
            out[c] = out[c].astype(int)
    return out
