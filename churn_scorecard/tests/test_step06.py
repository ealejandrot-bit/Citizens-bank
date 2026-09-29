"""QC del paso 6: univariado completo, sin fuga, sin discrepancias de signo no explicadas."""
import pandas as pd

from common import REPORTS, TABLES, candidates


def test_univariado():
    for t in ("A", "B"):
        u = pd.read_csv(TABLES / f"step06_univariate_{t}.csv")
        assert set(u.variable) == set(candidates(include_composites=True))
        sus = u[u["sospecha de fuga (AUC > 0.85 o IV > 0.50)"]]
        assert not (~sus.compuesto).any(), sus.variable.tolist()          # ninguna señal no compuesta
        assert set(sus.variable) <= {"multi_signal_count"}                # compuesto ya marcado en D0.5, fuera del campeón
    ub = pd.read_csv(TABLES / "step06_univariate_B.csv")
    assert (ub["evaluación"] != "DISCREPANCIA").all()


def test_tasas_por_bin_suman():
    for t in ("A", "B"):
        r = pd.read_csv(TABLES / f"step06_rate_by_bin_{t}.csv")
        tot = r.groupby("variable").hogares.sum()
        assert tot.nunique() == 1                    # cada variable reparte a todos los hogares de dev


def test_sospecha_documentada():
    assert "multi_signal_count" in (REPORTS / "decision_log.md").read_text()
