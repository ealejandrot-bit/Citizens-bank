"""QC del paso 2: diccionario completo y usos coherentes con las reglas."""
import pandas as pd

from common import COMPOSITES, OUTCOMES, TABLES, load_raw


def test_diccionario():
    d = pd.read_csv(TABLES / "step02_dictionary.csv")
    df = load_raw()
    assert list(d.columna) == list(df.columns) and len(d) == 62
    uso = d.set_index("columna").uso
    for c in OUTCOMES + ["household_id", "snapshot_date"]:
        assert uso[c] != "predictor", c
    for c in COMPOSITES:
        assert uso[c] == "auxiliar"
    pred = d[d.uso == "predictor"]
    assert pred["dirección esperada"].isin(["+", "−", "?"]).all()
    assert d.bloque.isin(["transaccional", "patrimonial", "relación", "producto", "servicio", "digital", "vida", "economía",
                          "compuesto", "estructural", "resultado"]).all()
    assert (d[d["missing estructural"] == "sí"].gatillo != "").all()
