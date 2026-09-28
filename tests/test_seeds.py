import copy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from synthetic.population import build_population
from synthetic.seeds import SeedManager

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


def small_cfg(n=3000, seed=None):
    cfg = copy.deepcopy(CFG)
    cfg["n_households"] = n
    if seed is not None:
        cfg["master_seed"] = seed
    return cfg


def test_stream_depends_only_on_seed_and_name():
    a = SeedManager(7).rng("x").random(5)
    s = SeedManager(7)
    s.rng("otro_antes")  # pedir otro flujo antes no debe alterar "x"
    b = s.rng("x").random(5)
    np.testing.assert_array_equal(a, b)


def test_distinct_names_and_seeds_give_distinct_streams():
    s = SeedManager(7)
    assert not np.array_equal(s.rng("a").random(5), s.rng("b").random(5))
    assert not np.array_equal(SeedManager(7).rng("a").random(5), SeedManager(8).rng("a").random(5))


def test_duplicate_stream_name_is_rejected():
    s = SeedManager(1)
    s.rng("pop.age")
    with pytest.raises(KeyError):
        s.rng("pop.age")


@pytest.mark.parametrize("bad", [-1, 1.5, "1"])
def test_invalid_master_seed(bad):
    with pytest.raises(ValueError):
        SeedManager(bad)


def test_population_is_reproducible():
    b1, t1 = build_population(small_cfg(), SeedManager(CFG["master_seed"]))
    b2, t2 = build_population(small_cfg(), SeedManager(CFG["master_seed"]))
    pd.testing.assert_frame_equal(b1, b2)
    pd.testing.assert_frame_equal(t1, t2)


def test_population_changes_with_master_seed():
    b1, _ = build_population(small_cfg(seed=1), SeedManager(1))
    b2, _ = build_population(small_cfg(seed=2), SeedManager(2))
    assert not b1["relationship_value"].equals(b2["relationship_value"])


def test_changing_one_distribution_leaves_other_columns_untouched():
    """Cambiar un parámetro (edad) no debe mover columnas con flujo propio (p. ej. trust)."""
    cfg2 = small_cfg()
    cfg2["population"]["age_mean"] += 5
    b1, t1 = build_population(small_cfg(), SeedManager(CFG["master_seed"]))
    b2, t2 = build_population(cfg2, SeedManager(CFG["master_seed"]))
    assert not b1["age_primary"].equals(b2["age_primary"])
    for col in ["relationship_value", "has_investments", "has_trust", "has_linked_business"]:
        pd.testing.assert_series_equal(b1[col], b2[col])
    pd.testing.assert_series_equal(t1["z_outflow"], t2["z_outflow"])
