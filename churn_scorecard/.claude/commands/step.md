Ejecuta el paso $ARGUMENTS de docs/SPEC.md.

1. Lee reports/decision_log.md. Si el paso depende de un gate no aprobado, detente y dilo.
2. Escribe o actualiza src/step$ARGUMENTS_<nombre>.py (usa src/common.py) y ejecútalo.
3. Escribe tests/test_step$ARGUMENTS.py con los controles del paso y corre `python -m pytest -q`. Si falla, detente y reporta.
4. Redacta reports/step$ARGUMENTS.md desde las tablas generadas (estructura de .claude/rules/reporting.md).
5. Registra decisiones y preguntas en reports/decision_log.md.
6. Si el paso cierra bloque (0, 4, 11, 14, 17), ejecuta /gate y detente.
