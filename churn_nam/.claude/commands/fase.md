Ejecuta la fase $ARGUMENTS de docs/SPEC.md §5.

1. Lee docs/STATUS.md y config.yaml; si la fase necesita un parámetro en null o un "go" pendiente, detente y pregunta.
2. Escribe src/pNN_<nombre>.py, guarda salidas en outputs/pNN/, renderiza reports/pNN.md con src/report.py.
3. Tests en verde (corrige código, nunca el test).
4. Actualiza docs/STATUS.md; un commit por fase y push.
5. Cierra con el resumen de 6 puntos y detente hasta "go".
