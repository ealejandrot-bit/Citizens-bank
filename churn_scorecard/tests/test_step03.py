"""QC del paso 3: sin duplicados, sin imposibles, mapa estructural reproducido, colas sin errores."""
import pandas as pd

from common import TABLES, eligible, load_raw


def test_controles_logicos():
    c = pd.read_csv(TABLES / "step03_checks.csv")
    assert (c["n [DATA]"] == 0).all(), c[c["n [DATA]"] > 0]


def test_elegibles_y_duplicados():
    df = load_raw()
    assert eligible(df).sum() == 19_877 and df.household_id.is_unique


def test_mapa_estructural():
    e = pd.read_csv(TABLES / "step03_structural_exceptions.csv")
    assert (e["% excepciones"] <= 3).all()
    assert (e.loc[e.variable != "pension_deposit_stopped_flag", "valor sin gatillo"] == 0).all()
    assert e.loc[e.variable == "pension_deposit_stopped_flag", "valor sin gatillo"].iloc[0] == 134


def test_colas_sin_error():
    o = pd.read_csv(TABLES / "step03_outliers.csv")
    assert (o.error == 0).all()
    assert (o["n > 0"] == o.error + o.extraordinario + o.real).all()
