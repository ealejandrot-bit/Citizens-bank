"""QC del paso 12: Σ puntos + base = score, escala PDO, tramos con reglas H-3, bandas, overrides, salida completa."""
import pickle

import numpy as np
import pandas as pd

from common import FACTOR, MODEL, OFFSET, SCORES, TABLES

S = pd.read_csv(SCORES / "household_scores.csv")
K = pickle.load(open(MODEL / "step12_scaling.pkl", "rb"))
L = pd.read_csv(TABLES / "step12_lookup.csv")
MS = pd.read_csv(TABLES / "step12_master_scale.csv")
MP = pd.read_csv(TABLES / "step12_master_scale_pre_override.csv")
BD = pd.read_csv(TABLES / "step12_bands.csv")


def test_escala_pdo():
    assert abs(FACTOR - 57.71) < 0.01 and abs(OFFSET - 427.12) < 0.01
    ch = pickle.load(open(MODEL / "step11A_champion.pkl", "rb"))
    assert K["base"] == round(OFFSET + FACTOR * ch["b0_corr"])
    p = 1 / (1 + np.exp((S.score - OFFSET) / FACTOR))
    assert np.allclose(p, S["probabilidad_pre_calibración"])


def test_suma_puntos_igual_score():
    ch = pickle.load(open(MODEL / "step11A_champion.pkl", "rb"))
    from common import PROC
    F = pd.read_parquet(PROC / "features.parquet").set_index("household_id").loc[S.household_id].reset_index()
    tot = np.full(len(F), K["base"])
    for c in ch["vars"]:
        r = F[f"{c}__miss"] if f"{c}__miss" in F else None
        lab = ch["binning"][c].bin_labels(F[c], r)
        tot = tot + pd.Series(lab).map(L[L.variable == c].set_index("bin").puntos).to_numpy()
    assert (tot == S.score.to_numpy()).all()
    # forma del SPEC (base repartida): Σ puntos SPEC = score sin redondear; difiere del entero por redondeo (≤ (n+1)/2)
    spec = np.zeros(len(F))
    for c in ch["vars"]:
        r = F[f"{c}__miss"] if f"{c}__miss" in F else None
        lab = ch["binning"][c].bin_labels(F[c], r)
        spec = spec + pd.Series(lab).map(L[L.variable == c].set_index("bin")["puntos (SPEC, base repartida)"]).to_numpy()
    assert (np.abs(spec - S.score.to_numpy()) <= (len(ch["vars"]) + 1) / 2).all()


def test_tramos_reglas_h3():
    for t in (MP, MS):
        r = t["tasa observada %"].to_numpy()
        assert r[0] >= 2 * r[1] and r[1] >= 2 * r[2] and r[2] >= 1.5 * r[3] and r[0] >= 5 * r[3]
        assert (t["eventos observados"] >= K["min_ev_dev"]).all()
        assert abs(t["% hogares"].sum() - 100) < 1e-9 and abs(t["captura eventos %"].sum() - 100) < 1e-9
    assert list(MS.tramo) == ["Crítico", "Alto", "Vigilancia", "Estable"]


def test_bandas():
    assert (BD.eventos >= K["min_ev_dev"]).all()
    assert (np.diff(BD.tasa.to_numpy()) < 0).all()
    assert (BD.hogares.sum() == MS.hogares.sum()) and (BD.eventos.sum() == MS["eventos observados"].sum())


def test_overrides():
    o = pd.read_csv(TABLES / "step12_overrides.csv")
    act = o[o.decisión != "eliminada"]
    for _, r in act[act["destino probado"] == act["decisión"]].iterrows():
        assert r["cumple precisión"] and r["cumple ≤ 30%"]
    assert set(K["overrides"].values()) <= {"Crítico", "Alto"}


def test_salida():
    assert len(S) == 20000 and S.household_id.is_unique
    assert S[["score", "tramo", "banda"]].notna().all().all()
    assert set(S.tramo) <= {"Crítico", "Alto", "Vigilancia", "Estable"}
