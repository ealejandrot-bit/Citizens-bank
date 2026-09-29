Cierra el gate $ARGUMENTS.

1. Corre `python -m pytest -q`; debe estar en verde.
2. Escribe reports/gate_$ARGUMENTS.md: tests, resumen de decisiones del bloque, preguntas para el usuario con su default.
3. Actualiza reports/decision_log.md (estado: gate $ARGUMENTS abierto, esperando respuesta).
4. Detente. No ejecutes pasos posteriores hasta que el usuario responda.
