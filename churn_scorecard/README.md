# churn_scorecard

Scorecard de propensión a churn (campeón WoE + logística, challenger EBM / GBM monotónico) según `docs/SPEC.md`.
Convenciones en `CLAUDE.md`; memoria del proyecto en `reports/decision_log.md`.

```bash
pip install -r requirements.txt        # versiones exactas en requirements.lock
python src/step00_profile.py           # un script por paso
python -m pytest -q                    # QC; debe estar en verde antes de cada gate
```

Estado: ver `reports/decision_log.md`.
