Dataset sintético, corte transversal: valida pipeline y metodología, no conclusiones sobre clientes reales.

# Comparativo final · Client Pulse (3 modelos + A-lite)

Mismos 1,764 hogares del test que ningún modelo vio (fuera del desarrollo de A-lite); hard churn (A) 106 eventos, target B 238 eventos.

## Todos los métodos
| modelo | proyecto | variables | rol | PR-AUC A (justo) | lift@5% A (justo) | PR-AUC B (justo) |
|:--|:--|:--|:--|:--|:--|:--|
| EBM M2 | Modelo 2 | 12 | challenger en monitoreo (M2) | 0.2091 | 5.295 | 0.3048 |
| LightGBM | Modelo 3 · benchmark | 58 | benchmark | 0.2083 | 4.728 | 0.2965 |
| EBM M3 | Modelo 3 | 58 | champion interpretable (M3) | 0.1991 | 5.295 | 0.3122 |
| XGBoost | Modelo 3 · benchmark | 58 | benchmark | 0.1985 | 5.106 | 0.2872 |
| Logística L2 | Modelo 3 · benchmark | 58 | benchmark | 0.1975 | 5.106 | 0.3135 |
| Red neuronal NAM | Modelo 3 | 58 | challenger (no pasó el gate) | 0.1968 | 4.728 | 0.3195 |
| LightGBM monótono | Modelo 3 | 58 | challenger interpretable | 0.1939 | 4.728 | 0.3042 |
| Scorecard M1 | Modelo 1 | 8 | operativo (M1) | 0.1906 | 4.728 | 0.3037 |
| A-lite | Modelo 1 previo | 5 | referencia ejecutiva | 0.1534 | 4.16 | 0.2625 |

## Hallazgos
- Todos los modelos completos quedan en un rango estrecho de PR-AUC en hard churn (0.191 a 0.209) en los mismos 1,764 hogares (106 eventos): la complejidad casi no agrega.
- A-lite, con 5 variables, encuentra menos churners (PR-AUC 0.153; -0.056 frente al mejor, EBM M2) y también tiene el menor lift en el 5% más riesgoso (4.16 frente a 4.73–5.30); su ventaja es ser el más simple de explicar.
- La red neuronal (NAM) no reemplaza a A-lite: mejora la PR-AUC en +0.043 (IC95 +0.003 a +0.090) pero el IC del lift@5% (-0.67 a +1.64) incluye 0.
- El EBM del Modelo 2 cumplió 6 de 8 criterios para reemplazar al scorecard y quedó como challenger: la ganancia no alcanzó los umbrales.
- Con 5% de hogares en alerta, por cada 100 alertas: EBM 31.8 churners, red neuronal 28.4, A-lite 25.0.
- Una regla simple de 2 o más señales visibles captura 97 churners en 393 hogares; el EBM, al mismo volumen, 104: el modelo le gana por poco.

## Recomendación
- Operar con el scorecard (M1) o el EBM: aditivos, auditables y en el tope de desempeño.
- Usar A-lite para explicar el modelo a la alta dirección (5 variables), sabiendo que detecta menos churners que los modelos completos.
- No llevar la red neuronal ni los árboles de caja negra a producción: no mejoran lo suficiente para justificar su complejidad.
- Medir el efecto de las acciones con el grupo de control del 12.5% antes de invertir en más modelado.

## Limitaciones
- Dataset sintético y un solo corte (sin OOT): valida el método, no resultados de clientes reales.
- La comparación contra A-lite se hace en 1,764 hogares con 106 eventos de hard churn: intervalos amplios.
- UHNW tiene muy pocos eventos: sus resultados solo se reportan.
- La red neuronal fue al gate sin terminar de converger (decisión del usuario).

_Cifras leídas de churn_nam/outputs (p10–p13), churn_ml, churn_scorecard y scorecard; generado por src/final_report.py._