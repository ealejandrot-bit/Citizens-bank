"""QC del paso 8: edad fuera del modelo; prueba de proxy y marcado por tercil calculados."""
import json

import pandas as pd

from common import PROC, TABLES


def test_edad_fuera():
    v = json.loads((PROC / "step02_selected.json").read_text(encoding="utf-8"))["vars"]
    assert "age_primary" not in v and "bureau_new_mortgage_elsewhere" not in v


def test_proxy_y_tasas():
    p = pd.read_csv(TABLES / "step08_age_proxy.csv")
    assert p["AUC (CV 5)"].between(0.5, 1).all()
    a = pd.read_csv(TABLES / "step08_age_rates.csv")
    assert len(a) == 3 and a.hogares.sum() > 13000
