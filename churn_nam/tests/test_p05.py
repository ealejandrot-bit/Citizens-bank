"""QC de la fase 5: EDA solo en dev, deciles completos con IC, clusters de redundancia coherentes."""
import json

import pandas as pd

from config import P


def test_solo_dev_y_deciles():
    s = json.load(open(P.out(5) / "summary.json"))
    assert s["hogares dev"] == 13631 and s["eventos A dev"] == 817
    d = pd.read_csv(P.out(5) / "decile_rates.csv")
    for (f, t), g in d.groupby(["feature", "target"]):
        assert g.hogares.sum() == (13631 if t == "A" else 13482), (f, t)
    assert (d["IC95 inf %"] <= d["tasa %"]).all() and (d["tasa %"] <= d["IC95 sup %"]).all()


def test_redundancia():
    c = pd.read_csv(P.out(5) / "redundancy_clusters.csv")
    assert (c["máx |ρ| dentro del cluster"] >= 0.70).all()
