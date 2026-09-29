"""QC de la fase 6: splits disjuntos y heredados de M1, estratificación, subconjunto A-lite y gate pre-registrado intacto."""
import hashlib
import json

import pandas as pd
import yaml

from config import CFG, P, get

S = pd.read_parquet(P.processed / "splits.parquet")
M1 = P.m1 / "data" / "processed"


def test_disjuntos_y_heredados():
    tr, va, te = (set(S.household_id[S.split == s]) for s in ("train", "validation", "test"))
    assert not (tr & va) and not (tr & te) and not (va & te)
    assert te == set(pd.read_parquet(M1 / "val.parquet").household_id)
    assert tr | va == set(pd.read_parquet(M1 / "dev.parquet").household_id)
    assert abs(len(va) / (len(tr) + len(va)) - get("splits.validation_frac_of_dev")) < 0.001


def test_estratificacion():
    z = pd.read_csv(P.out(6) / "split_sizes.csv")
    t = z[z.segmento == "total"].set_index("muestra")
    assert abs(t.loc["train", "tasa A %"] - t.loc["validation", "tasa A %"]) < 0.5
    assert abs(t.loc["train", "tasa B %"] - t.loc["validation", "tasa B %"]) < 0.5


def test_subconjunto_alite():
    assert S.loc[S.test_alite, "split"].eq("test").all()
    al = pd.read_csv(P.alite / "outputs" / "tables" / "04_split.csv")
    assert set(S.household_id[S.test_alite]) <= set(al.household_id[al.muestra == "holdout"])


def test_gate_preregistrado_sin_cambios():
    g = json.load(open(P.out(6) / "gate_preregistered.json"))
    assert g["sha256 del bloque gate de config.yaml"] == hashlib.sha256(yaml.safe_dump(CFG["gate"], sort_keys=True).encode()).hexdigest()
    assert g["test abierto"] is False and g["gate pre-registrado"]["delta_pr_auc"] == get("gate.delta_pr_auc")
