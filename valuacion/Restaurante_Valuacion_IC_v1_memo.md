# [NOMBRE DEL RESTAURANTE]: valuación para Comité de Inversiones (v1)
**Centro Histórico de Guanajuato · corte de mercado: 11-nov-2026 · modelo: `Restaurante_Valuacion_IC_v1.xlsx`**
**Estatus: borrador técnico. Todos los datos operativos son supuestos de industria en naranja; el cliente no entregó datos.**

## Conclusión (escenario base ★, apertura greenfield, cheque de $7.5M)
- **Equity pre-money ponderado: −$0.88M. Rango de −$6.6M (conservador) a +$6.2M (optimista).** El proyecto apenas recupera su costo de capital: **TIR 23.4% vs Ke 26.8%**, con VPN de −$0.03M. Hoy no hay valor pre-money que pagar por el concepto. El precio defendible es el capital invertido, más un *sweat equity* para los fundadores con vesting atado a cubiertos/día.
- **Operación base:** ventas del año 2 de $17.7M y EBITDA 4-wall de 16.3%. EBITDA de la empresa: $2.58M pre-IFRS16 ($4.07M post). Prime cost de 59.2%.
- **Break-even:** 92 cubiertos/día contra 123 proyectados (colchón de 34%). Payback de 3.7 años.
- **Estrés (−25% cubiertos y +15% en food cost):** el EBITDA del año 2 pasa a −$0.55M, el EV DCF baja de $5.5M a −$5.5M y la caja mínima del año 1 queda en −$56k. **No cumple el covenant de 2 meses de costos fijos.** El escenario base sí lo cumple (caja mínima de $1.26M vs $1.20M requeridos).

## Supuestos críticos (los que mueven la decisión)
| Supuesto | Valor | Fuente / estatus |
|---|---|---|
| Ke = Rf local + βL·ERP + tamaño + CSRP | **26.8%** (Fisher USD: 26.0%) | Rf 7.20% = M-Bono 9.25% (Cetesdirecto, 09-nov-26) − default spread 2.05% (Damodaran, ajustado a Baa3) |
| βU Restaurant/Dining, re-apalancada | 0.677 → **1.387** | Promedio EUA (verificado) y Global (fuente secundaria). Se re-apalanca con D/E 150% (pasivo NIF D-5 / equity); checado contra el D/E implícito |
| ERP total México | 7.31% | Damodaran: ERP maduro 4.20% + CRP 2.46% + 0.65pp por el downgrade a Baa3 (jul-26, **no verificado**) |
| Prima por tamaño / CSRP | 5.0% / 4.5% | Kroll decil 10 histórico (**no verificado**, Kroll es de pago). CSRP desglosado en 5 componentes |
| Cubiertos/día régimen | 120 | 90 asientos; rotación 0.8/1.2/1.0; ocupación 35/50/45%. **Pendiente** de validar con el POS |
| Ticket salón (sin IVA) | $368–$383 | **Pendiente**: menú costeado |
| Food / beverage cost | 32% / 25% | Rango CANIRAC 28–35% (fuente secundaria). El IEPS es costo no acreditable |
| Renta / plazo | $120k/mes, INPC, 10 años + 5 de renovación (prob. 60%) | **Pendiente**: contrato. Fija el valor terminal de vida finita |
| CapEx inicial / preoperativos | $4.8M / $0.45M | **Pendiente**: cotizaciones compatibles con INAH |
| Múltiplo EV/EBITDA | 6.6x base → **3.98x efectivo** (−40% por tamaño); DLOM 25% | Alsea ~5.0x (**no verificado**); transacciones 8.25x (La Casa de Toño, no cerrada; Vips 2014) |
| Ponderación de métodos | DCF 50 / Comparables 30 / VC 20 / Perpetuidad 0 | La perpetuidad supone que el local dura para siempre: sólo sirve como cross-check |

## Open items para el comité (lista completa en la hoja *Data Request*)
1. **Datos de la empresa (prioridad A):** nombre, zona, monto a levantar, EEFF, ventas del POS, menú costeado, plantilla, contrato de arrendamiento, licencias y cap table. Ninguno se entregó (63 supuestos en naranja).
2. **Comparables:** la red de la sesión bloqueó BMV, SEC, stockanalysis y Damodaran. EV y EBITDA de ALSEA, CMRB, ARCO y QSR salen de resúmenes de búsqueda. El set México tiene **1 observación**. Ningún comparable tiene EV/Ventas ni EV/asiento verificable, así que no se fabricaron.
3. **Parámetros por confirmar:** beta Damodaran *Emerging Markets*, size premium de Kroll vigente, `ctryprem` de jul-2026 (Baa3), M-Bono en Banxico SIE y serie mensual de ocupación del OTEG (para calibrar la estacionalidad).
4. **Transacciones precedentes:** no hay ninguna en México/LatAm 2021–26 con EV/EBITDA divulgado oficialmente. Se dice explícitamente en la hoja.

## QA
- Recalculado con LibreOffice: **5,385 fórmulas y 0 errores**.
- **32 de 32 checks en VERDADERO**: cap table = 100%, fuentes = usos, motor ↔ hojas de método, etiquetas ↔ inputs, payback ↔ FCF acumulado, pasivo NIF D-5 = 0 al vencer el contrato, WACC > g, Ke local ≈ Fisher.
- **Robustez:** los checks también pasan con el escenario activo en Estrés y con el valor terminal en Gordon.

**Reconciliación** (hoja *Reconciliación*; las 18 cifras coinciden):

| Cifra | Valor | Origen |
|---|---|---|
| EV DCF base | $5,457,380 | `Escenarios!D276` |
| EV Gordon base | $5,786,124 | `Escenarios!D275` |
| Equity por comparables | $437,864 | `Escenarios!D296` |
| Post-money VC | $2,549,084 | `Escenarios!D306` |
| Ke | 26.84% | `Supuestos!B49` |
| TIR del proyecto | 23.4% | `P&L y FCF!B103` |
| VPN | −$32,620 | `P&L y FCF!B104` |
| Break-even | 91.9 cubiertos/día | `P&L y FCF!B116` |
| Pre-money concluido | −$875,134 | `Resumen!E12` |

## Correcciones respecto a la base Shivai v6
- **Beta:** se desapalanca con Hamada y el D/E de mercado de los comparables, y se re-apalanca con la estructura objetivo de la empresa. En la base se usaba el equity del inversionista como D/E.
- **Rf:** M-Bono 10 años neto de default spread, con el ERP total de México. Así no se cuenta dos veces el riesgo país. En la base se usaba CETES 28d.
- **D&A:** se separan EBITDA, D&A y EBIT. Se elimina el supuesto "EBITDA ≈ EBIT".
- **Iliquidez:** se aplica una sola vez, vía DLOM sobre el equity. En la base estaba en el WACC y además en el múltiplo.
- **Simulación de préstamo y APV:** se eliminaron. La empresa es all-equity, así que no hay escudo fiscal que valuar con APV.
- **Valor terminal:** se acota a la vida del arrendamiento y se marca alerta si pasa de 70% del EV (base: 3.7%).
- **Capital de trabajo:** se modela por días (inventario, cobro y pago). Sale negativo.

## Las 5 preguntas más duras del comité
1. **"¿Por qué pagar por un concepto con VPN ≈ 0?"** El modelo responde que no hay que hacerlo: pre-money base ≤ 0 y zona de negociación limitada al capital invertido (Resumen H). ✅
2. **"Un Ke de 26.8% es arbitrario."** Cada componente tiene fuente, el Fisher USD (26.0%) lo cruza y las tablas de sensibilidad muestran WACC ±4pp. ✅ Hay un riesgo de doble conteo entre size premium y CSRP: se mitigó al dejar el decil 10z (11.4%) fuera del caso base. ⚠
3. **"¿Los múltiplos de comparables son verificables?"** **No del todo**: el set México tiene 1 observación no verificada. Por eso pesan 30% y se marcan como open item. ⚠ **No resuelto.**
4. **"¿Qué pasa si el arrendador no renueva?"** El valor terminal de vida finita usa probabilidad de renovación por escenario y aporta sólo 3.7% del EV. El contrato es condición precedente. ✅
5. **"¿Alcanza la caja en un mal año?"** En base sí. **En estrés no:** la caja mínima es de −$56k. El modelo lo dice y lo convierte en condición de cierre (tramos y reserva adicional). ✅

## Tres condiciones precedentes al cierre
1. Licencia de alcoholes, uso de suelo y dictamen INAH / imagen urbana emitidos antes de desembolsar el tramo de obra.
2. Contrato de arrendamiento firmado por un plazo igual o mayor al modelado, con opción de renovación, incremento topado a INPC y derecho de preferencia.
3. Due diligence independiente que valide los supuestos en naranja (POS, menú costeado, plantilla y cotizaciones de CapEx), y nueva corrida del modelo con esos datos.
