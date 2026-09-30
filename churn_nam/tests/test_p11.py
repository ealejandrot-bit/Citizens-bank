"""QC de la fase 11: método elegido por ECE fuera de muestra en validación; a y b guardados; evaluación en test."""
import json

import pandas as pd

from config import P


def test_seleccion_y_parametros():
    c = pd.read_csv(P.out(11) / "calibration.csv")
    for _, r in c.iterrows():
        assert r.elegido == ("platt" if r["ECE CV Platt (pp)"] <= r["ECE CV isotónica (pp)"] else "isotonic")
    j = json.load(open(P.out(11) / "calibrators.json"))
    assert set(j) == set(c.modelo) and all("a" in v and "b" in v for v in j.values())
