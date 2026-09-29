"""QC del paso 0: la ficha del dataset (SPEC §C) recalculada de forma independiente."""
import numpy as np
import openpyxl
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from common import RAW, SHEET, STRUCTURAL, TABLES, eligible, load_raw, loss_ratio, targets


@pytest.fixture(scope="module")
def df():
    return load_raw()


@pytest.fixture(scope="module")
def d(df):
    return df[eligible(df)]


def test_hoja_forma_unidad_snapshot(df):
    assert openpyxl.load_workbook(RAW, read_only=True).sheetnames == [SHEET]
    assert df.shape == (20_000, 62)
    assert df.household_id.is_unique
    assert df.snapshot_date.astype(str).str[:10].unique().tolist() == ["2025-12-31"]


def test_segmentos(df):
    assert df.segment.value_counts().to_dict() == {"HNW": 18_897, "UHNW": 1_103}


def test_excluidos(df):
    ex = df[df.churn_excluded.astype(bool)]
    assert len(ex) == 123
    assert ex[["hard_churn_6m", "soft_churn_3m", "value_lost_6m"]].isna().all().all()
    assert ex.history_months.between(13, 24).all() and ex.tenure_years.min() >= 1.14


def test_targets_hard_soft(df):
    el = eligible(df)
    hard, soft = df.hard_churn_6m == 1, df.soft_churn_3m == 1
    r = loss_ratio(df)
    assert el.sum() == 19_877
    assert hard.sum() == 1_200 and round(100 * hard[el].mean(), 2) == 6.04
    assert np.allclose(r[hard], 1.0)
    assert soft.sum() == 1_756 and round(100 * soft[el].mean(), 2) == 8.83
    assert r[soft].between(0.20, 0.60).all() and abs(r[soft].median() - 0.40) < 0.005
    assert (hard & soft).sum() == 0
    assert ((df.value_lost_6m > 0) == (hard | soft)).all() and (df.value_lost_6m > 0).sum() == 2_956


def test_opciones_target(df):
    t = targets(df)
    assert int(t.y_A.sum()) == 1_200 and int(t.y_A.notna().sum()) == 19_877
    assert int(t.y_B.sum()) == 2_740 and int(t.y_B.notna().sum()) == 19_661 and int(t.y_B_indet.sum()) == 216
    assert int(t.y_C.sum()) == 2_956 and int(t.y_D.sum()) == 1_756
    assert round(100 * t.y_B.mean(), 1) == 13.9 and round(100 * t.y_C.mean(), 1) == 14.9


def test_churn_por_valor_y_tamano(d):
    rv = d.relationship_value
    assert round(100 * rv[d.hard_churn_6m == 1].sum() / rv.sum(), 2) == 6.46
    assert round(100 * d.value_lost_6m.sum() / rv.sum(), 2) == 10.32
    assert round(rv.sum() / 1e9, 2) == 206.27 and round(d.aum.sum() / 1e9, 2) == 135.09
    assert d.has_investments.sum() == 17_030 and (~d.has_investments).sum() == 2_847
    s = rv.sort_values(ascending=False)
    assert round(100 * s.head(int(0.05 * len(s))).sum() / s.sum(), 1) == 37.4
    assert round(100 * s.head(int(0.01 * len(s))).sum() / s.sum(), 1) == 18.1
    assert round(rv.median() / 1e6, 2) == 4.84 and round(rv.quantile(.05) / 1e6, 2) == 1.27 and round(rv.quantile(.95) / 1e6, 1) == 31.8


def test_rv_vs_aum_mas_depositos(df):
    """Ficha: 'RV ≠ AUM + depósitos'. Literalmente cierto en flotantes; en sustancia RV = AUM + depósitos al centavo (D0.2)."""
    diff = (df.relationship_value - df.aum.fillna(0) - df.deposit_balance).abs()
    assert (diff > 0).any()                 # la desigualdad literal de la ficha
    assert (diff.round(6) <= 0.01).all()   # pero la identidad se cumple al centavo (redondeo a 1e-6 quita ruido de flotante) → D0.2


def test_missing_estructural(d):
    for trig, cols in STRUCTURAL.items():
        g = d[trig].astype(bool)
        for c in cols:
            na = d[c].isna()
            exc = ((~na & ~g) | (na & g)).mean()
            assert exc <= 0.03, (c, exc)                                   # excepciones ≤ 3%
            if trig == "has_investments":
                assert (na & ~g).sum() == 2_847 and (~na & ~g).sum() == 0  # sin inversiones ⟹ NaN


def test_missing_no_estructural(df):
    got = [round(100 * df[c].isna().mean(), 1) for c in
           ["client_reply_rate", "meetings_cancelled_by_client", "relationship_dissatisfaction_flag", "fixed_income_maturity_not_reinvested"]]
    assert got == [48.0, 60.7, 70.4, 73.9]


def test_antiguedad_historia(d):
    assert (d.tenure_years < 1).sum() == 404 and (d.history_months < 24).sum() == 1_417


def test_compuestos(df, d):
    assert (df.multi_signal_flag == (df.multi_signal_count >= 3)).all()
    binarias = ["salary_deposit_stopped_flag", "recurring_deposit_stopped_flag", "banker_change_6m_flag", "complaint_escalated_flag",
                "pension_deposit_stopped_flag", "business_payroll_stopped_flag", "trustee_change_flag", "repeat_complaint_flag",
                "relationship_dissatisfaction_flag", "bureau_new_mortgage_elsewhere"]
    assert round(d[binarias].fillna(0).sum(axis=1).corr(d.multi_signal_count), 2) == 0.59
    rc = d.groupby("multi_signal_count").hard_churn_6m.mean()
    assert round(100 * rc.loc[0], 1) == 2.8 and round(100 * rc.loc[7], 1) == 44.8


def test_senal_univariada(d):
    y = d.hard_churn_6m.astype(int)
    def auc(c):
        x = d[c].astype(float)
        a = roc_auc_score(y, x.fillna(x.median()))
        return max(a, 1 - a)
    assert round(auc("multi_signal_count"), 2) == 0.69
    assert round(auc("banker_change_6m_flag"), 2) == 0.64 and round(auc("share_of_wallet"), 2) == 0.64
    lk = pd.read_csv(TABLES / "step00_leakage_screen.csv")
    assert lk["AUC A"].max() <= 0.70 and lk["AUC B"].max() <= 0.70


def test_gradiente_tamano(d):
    dec = pd.qcut(d.relationship_value.rank(method="first"), 10, labels=False)
    r = d.groupby(dec).hard_churn_6m.mean()
    assert round(100 * r.min(), 1) == 5.2 and round(100 * r.max(), 1) == 7.1


def test_pares_redundantes():
    p = pd.read_csv(TABLES / "step00_pairs.csv")
    assert len(p) == 10 and p["coincide (±0.015)"].all()


def test_sin_imposibles(df):
    assert (df[["relationship_value", "deposit_balance"]] >= 0).all().all() and (df.aum.dropna() >= 0).all()
    assert df.share_of_wallet.between(1e-12, 1).all() and (df.tenure_years >= 0).all()


def test_tablas_paso0():
    for n in ["step00_ficha", "step00_target_options", "step00_churn_rates", "step00_missing_map", "step00_leakage_screen", "step00_prohibited"]:
        assert (TABLES / f"{n}.csv").exists(), n
    cr = pd.read_csv(TABLES / "step00_churn_rates.csv")
    for t in ("A", "B"):
        x = cr[cr.target == t].set_index("segmento")
        mix = (x.loc[["HNW", "UHNW"], "base"] / x.loc["Total", "base"] * x.loc[["HNW", "UHNW"], "churn hogares %"]).sum()
        assert abs(mix - x.loc["Total", "churn hogares %"]) < 1e-9          # Σ share × tasa = cartera
