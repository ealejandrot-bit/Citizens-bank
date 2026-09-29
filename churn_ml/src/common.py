"""Rutas, semilla, parámetros, carga de datos heredados y utilidades comunes del Modelo 2 (pasos 00–12)."""
from __future__ import annotations

import os
import random
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
M1 = ROOT.parent / "churn_scorecard"                       # Modelo 1 (solo lectura; nunca se modifica)
RAW = M1 / "data" / "raw" / "client_pulse_synthetic.xlsx"
INH = ROOT / "data" / "inherited"
PROC = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
FIGS = ROOT / "outputs" / "figs"
MODEL = ROOT / "outputs" / "model"
SCORES = ROOT / "outputs" / "scores"
REPORTS = ROOT / "reports"

SEED = 42
S0, O0, PDO = 600, 20.0, 40
FACTOR = PDO / np.log(2)                 # 57.71
OFFSET = S0 - FACTOR * np.log(O0)        # 427.12

ID = "household_id"
OUTCOMES = ["hard_churn_6m", "soft_churn_3m", "value_lost_6m", "churn_excluded"]
COMPOSITES = ["multi_signal_flag", "multi_signal_count"]
EXCLUDED_G13 = ["age_primary", "bureau_new_mortgage_elsewhere"]      # heredado de M1 (G1-3)
PROHIBITED = OUTCOMES + [ID, "snapshot_date"] + EXCLUDED_G13

# Archivos heredados de M1: (origen relativo a churn_scorecard/, destino en data/inherited/)
INHERIT = [
    ("data/processed/features.parquet", "features.parquet"),
    ("data/processed/dev.parquet", "dev.parquet"),
    ("data/processed/val.parquet", "val.parquet"),
    ("data/processed/step01_population.parquet", "step01_population.parquet"),
    ("data/processed/step07_clusters.parquet", "step07_clusters.parquet"),
    ("data/processed/step11A_oof.parquet", "m1_champion_oof_r1.parquet"),
    ("data/processed/step12_scores.parquet", "m1_step12_scores.parquet"),
    ("outputs/scores/household_scores.csv", "m1_household_scores.csv"),
    ("outputs/tables/step05_features.csv", "step05_features.csv"),
    ("outputs/tables/step06_univariate_B.csv", "step06_univariate_B.csv"),
    ("outputs/tables/step08_spearman.csv", "step08_spearman.csv"),
    ("outputs/tables/step09_iv_summary.csv", "step09_iv_summary.csv"),
    ("outputs/tables/step11A_cv_folds.csv", "m1_step11A_cv_folds.csv"),
    ("outputs/tables/step13_global.csv", "m1_step13_global.csv"),
    ("outputs/tables/step14_platt.csv", "m1_step14_platt.csv"),
    ("outputs/model/MANIFEST.json", "m1_MANIFEST.json"),
]


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def save_table(df: pd.DataFrame, name: str, index: bool = False) -> Path:
    TABLES.mkdir(parents=True, exist_ok=True)
    p = TABLES / f"{name}.csv"
    df.to_csv(p, index=index)
    return p


def md_table(df: pd.DataFrame, floatfmt: str = ",.4g") -> str:
    return df.to_markdown(index=False, floatfmt=floatfmt)


def signs() -> dict:
    """Signo de negocio por variable (G1-1 de M1): '+', '−' o '?'. Compuestos '+'."""
    s = pd.read_csv(INH / "step05_features.csv").set_index("variable")["signo esperado"].to_dict()
    s.update({c: "+" for c in COMPOSITES})
    return s


def candidates(include_composites: bool = True) -> list[str]:
    """Candidatas ML: todas las variables de M1 (proveedor − G1-3 + derivadas) + compuestos (I-2) + cluster."""
    f = pd.read_csv(INH / "step05_features.csv")
    v = [c for c in f.variable if not c.startswith("<") and c not in EXCLUDED_G13]
    return v + (COMPOSITES if include_composites else []) + ["cluster"]


def load_split(part: str) -> pd.DataFrame:
    """dev o val con todas las features + targets / pesos / folds + cluster (heredados)."""
    F = pd.read_parquet(INH / "features.parquet")
    s = pd.read_parquet(INH / f"{part}.parquet")
    keep = [c for c in s.columns if c not in F.columns or c == ID]
    out = s[keep].merge(F, on=ID, how="left").merge(pd.read_parquet(INH / "step07_clusters.parquet"), on=ID, how="left")
    out["segment_uhnw"] = (out["segment"] == "UHNW").astype(int)
    for c in out.columns:
        if out[c].dtype == bool and not c.startswith(("in_pop_", "y_")):
            out[c] = out[c].astype(int)
    return out
