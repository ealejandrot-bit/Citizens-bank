# Prompt para Claude Design — Presentación ejecutiva de la valuación de Dos Chingones

> Copia todo lo que está debajo de la línea y pégalo en Claude Design. Adjunta el archivo `Dos_Chingones_Valuacion_v2.xlsx` para que pueda verificar cada cifra.

---

## ROL
Actúa como socio de una firma de valuación y diseñador de presentaciones ejecutivas. El estándar es el de un memo de comité de inversiones y una *fairness opinion*. Cada número debe poder rastrearse a su origen, cada supuesto debe estar declarado y cada limitación debe decirse sin maquillar. Escribe en español de México, con tono ejecutivo, frases cortas y cero relleno.

## OBJETIVO
Crea una presentación ejecutiva de **12 diapositivas principales + un apéndice técnico de 10–12 diapositivas** que entregue la valuación por acción de **Dos Chingones** (Guanajuato, Gto.), con sus dos unidades: **Garden** y **Presa**.

Hay dos audiencias:
1. **Socios / comité:** el cuerpo principal. Deben entender el valor, el rango y qué lo mueve en menos de 10 minutos.
2. **Revisores técnicos** (auditor, consultor externo u otra IA): el apéndice. Deben poder reproducir y cuestionar el cálculo sin hablar con nosotros.

## REGLAS NO NEGOCIABLES
- **No inventes datos.** Usa sólo las cifras de este prompt o del Excel adjunto. Si una cifra no está, escribe "N/D".
- **Mismo número, mismo valor** en todas las diapositivas. Redondea a pesos en el cuerpo y deja los decimales para el apéndice.
- **Presenta el valor como rango con un punto base**, nunca como precio único.
- **Declara la limitación principal** desde la diapositiva 2: no hay estados financieros. La utilidad es lo que se repartió a los socios.
- **Cada gráfica y tabla lleva fuente al pie**, por ejemplo: "Fuente: Dos_Chingones_Valuacion_v2.xlsx, hoja Tablita".
- **Moneda:** MXN nominales. **Fecha de corte:** datos a septiembre 2026; parámetros de mercado al 11-nov-2026.

## DISEÑO
- **Estilo:** consultoría élite, sobrio. Fondo claro, un color primario azul marino (#1F3864) y un acento único para "base ★". Rojo sólo para alertas.
- **Encabezados:** cada diapositiva lleva un *titular de acción*, una frase que diga la conclusión, no el tema. Ejemplo: "Dos Chingones vale ~$84k por acción; el rango refleja la caída reciente de márgenes".
- **Formato:** máximo 3 bullets por diapositiva en el cuerpo principal. Tablas limpias, sin bordes pesados.
- **Gráficas:** football field horizontal para el rango, líneas para la tendencia de ventas y margen, tornado para la sensibilidad.
- **Numeración y pie:** número de diapositiva y la leyenda "Confidencial — preparado para los socios de Dos Chingones".

## DATOS DE LA VALUACIÓN

### Resultado: valor por acción (100 acciones, 1 acción = 1%)
| Unidad | Base ★ | Mínimo | Máximo | Valor total base |
|---|---|---|---|---|
| Garden | $63,457 | $51,147 | $69,502 | $6,345,725 |
| Presa | $20,350 | $14,739 | $25,273 | $2,034,954 |
| **Total Dos Chingones** | **$83,807** | **$65,886** | **$94,775** | **$8,380,679** |

### Histórico: ventanas de 12 meses que terminan en septiembre
| Concepto | Oct-23 – Sep-24 | Oct-24 – Sep-25 | Oct-25 – Sep-26 (LTM) | Var. último año | CAGR 2 años |
|---|---|---|---|---|---|
| Ventas Garden | $10,895,997 | $12,626,410 | $11,885,772 | −5.9% | +4.4% |
| Utilidad Garden (repartos) | $1,805,136 | $2,194,137 | $1,497,745 | −31.7% | −8.9% |
| Ventas Presa | $6,993,536 | $8,293,172 | $6,407,854 | −22.7% | −4.3% |
| Utilidad Presa | N/D | $827,236* | $432,670 | −47.7% | N/D |

*Presa tiene utilidad desde dic-2024; ese año son 10 meses anualizados.

### Márgenes netos (utilidad / ventas)
| Unidad | Histórico completo | Oct-24 – Sep-25 | LTM | Últimos 6 meses | Últimos 3 meses |
|---|---|---|---|---|---|
| Garden | 15.7% | 17.4% | 12.6% | 11.5% | 9.3% |
| Presa | 8.4% | 9.9% | 6.8% | 4.9% | 3.6% |

Alertas: en septiembre 2026 el margen fue de 3.9% en Garden y 0.1% en Presa.

### Proyección base (5 años)
| | LTM | Año 1 | Año 2 | Año 3 | Año 4 | Año 5 |
|---|---|---|---|---|---|---|
| Ventas Garden | $11.89M | $11.19M | $11.11M | $11.62M | $12.14M | $12.69M |
| Utilidad Garden (margen 11.5%) | $1.37M | $1.29M | $1.28M | $1.34M | $1.40M | $1.46M |
| Ventas Presa | $6.41M | $6.13M | $6.14M | $6.42M | $6.71M | $7.01M |
| Utilidad Presa (margen 6.8%) | $0.43M | $0.41M | $0.41M | $0.43M | $0.45M | $0.47M |

### Valuación por método (base ★)
| Unidad | DCF | Múltiplo P/U (4x) | Ponderado 50/50 | % del DCF en valor terminal |
|---|---|---|---|---|
| Garden | $7,221,505 | $5,469,944 | $6,345,725 | 46.6% |
| Presa | $2,339,228 | $1,730,680 | $2,034,954 | 46.7% |

### Escenarios (valor ponderado por unidad)
| Unidad | Optimista | Base ★ | Conservador |
|---|---|---|---|
| Garden | $6,950,184 | $6,345,725 | $5,114,712 |
| Presa | $2,527,338 | $2,034,954 | $1,473,918 |

### Sensibilidad (total por acción, base $83,807)
| Variable | Cambio | Valor por acción | Δ |
|---|---|---|---|
| Tasa de descuento | −3 pts (18.6%) | $93,946 | +12% |
| Tasa de descuento | +3 pts (24.6%) | $76,705 | −8.5% |
| Múltiplo P/U | 3x | $74,810 | −11% |
| Múltiplo P/U | 5x | $92,812 | +11% |
| Crecimiento de largo plazo | 4.0% / 5.04% nominal | $82,501 / $85,204 | ±1.7% |
| Margen (repartos) | ±10% | — | ±10% |

### Valor por socio (base ★)
| Socio | % | Valor total | Rango |
|---|---|---|---|
| Alma | 1% | $83,807 | $65,886 – $94,775 |
| Anabel | 2% | $167,614 | $131,772 – $189,550 |
| Alejandro | 2% | $167,614 | $131,772 – $189,550 |
| María Ester | 2% | $167,614 | $131,772 – $189,550 |
| Adrián | 3% | $251,421 | $197,658 – $284,325 |
| Alma Galland | 4% | $335,228 | $263,544 – $379,100 |
| José Luis | 4% | $335,228 | $263,544 – $379,100 |
| Resto de los socios | 82% | $6,872,157 | $5,402,652 – $7,771,550 |

## ESTRUCTURA — CUERPO PRINCIPAL (12 diapositivas)
1. **Portada:** "Dos Chingones — Valuación por acción". Guanajuato, Gto. · Corte sep-2026 · Confidencial.
2. **Resumen ejecutivo:** valor base de $83,807 por acción (rango $65,886 – $94,775); qué aporta cada unidad; la limitación principal en una línea; la recomendación.
3. **La tablita:** valor por acción por unidad y total (tabla de resultado) más un football field horizontal.
4. **Qué valuamos y con qué información:** 37 meses (sep-2023 a sep-2026) de ventas y repartos a socios por unidad. Por qué usar lo repartido es una medida válida: es dinero que efectivamente salió del negocio, el equivalente a un modelo de descuento de dividendos.
5. **La historia de Garden:** ventas estables (CAGR +4.4%, pero −5.9% en el último año) y margen que baja de 17.4% a 11.5%. Gráfica de líneas.
6. **La historia de Presa:** arrancó con márgenes de 15–19% (dic-24 a feb-25); las ventas cayeron 23% y el margen bajó a ~5%. Mensaje: la caída de ventas con costos fijos se multiplica en la utilidad.
7. **Cómo proyectamos:** ventas × margen. Garden usa datos recientes (caída del último año y margen de 6 meses); Presa usa la tendencia de 2 años y el margen LTM. Declara que las reglas son distintas por decisión de los socios y que el Excel permite cambiarlas.
8. **Métodos y ponderación:** DCF 50% y múltiplo P/U 50%, con el valor de cada uno por unidad. Por qué no se usaron otros métodos (sin EBITDA, sin deuda, sin comparables verificables).
9. **Tasa de descuento de 21.6%:** construcción en escalera (Rf local, beta × ERP, tamaño, riesgo específico) explicada en lenguaje simple.
10. **Escenarios y sensibilidad:** tabla de escenarios y gráfica tornado. Mensaje: ningún supuesto razonable, cambiado solo, mueve el valor más de ~12%.
11. **Valor por socio:** tabla por socio con base y rango.
12. **Riesgos, limitaciones y siguientes pasos:**
    - Riesgos: tendencia de margen a la baja, Presa en su nivel más bajo, sin estados financieros, número de acciones supuesto.
    - Siguientes pasos: estados de resultados, capital social real, política de reinversión, sueldos de socios, inventario de activos de Presa, asientos y ticket por unidad.

## ESTRUCTURA — APÉNDICE TÉCNICO (para auditor, consultor o IA)
Título de sección: "Apéndice — Metodología, supuestos y reproducibilidad".

**A1. Alcance y estándar.** Propósito: precio de referencia entre socios. Base de valor: valor razonable, participación minoritaria, sin descuento por liquidez (DLOM 0%). Moneda, fechas de corte, y la declaración de que no es una opinión auditada.

**A2. Fuentes de datos.** Archivo original de repartos mensuales (hoja Original, columnas P–S). Hallazgos de calidad de datos:
- Marzo 2025 de Garden (celda R22) suma el acumulado de Juan Luis, un posible doble conteo de $3,915.
- Abril 2025 de Garden es un promedio, no un dato real.
- Presa no tiene utilidad antes de dic-2024.

**A3. Definición de "utilidad neta".** Suma mensual de lo repartido a todos los socios (100%) en Garden; cifra capturada en Presa. Implicaciones: es flujo al accionista; supone que no hay deuda y que lo reinvertido equivale a la depreciación. Riesgo: si no se aparta dinero para renovación, la utilidad está sobreestimada.

**A4. Fórmulas del modelo.** Escríbelas explícitas:
- Ventas: Año 1 = LTM × (1 + g₁); Año 2 = Año 1 × (1 + (g₁ + g_LP)/2); Años 3–5 = año previo × (1 + g_LP)
- Utilidad: Uₜ = Ventasₜ × margen del escenario
- DCF: Σ Uₜ/(1+Ke)ᵗ + [U₅ × (1+g_LP)/(Ke − g_LP)]/(1+Ke)⁵
- Múltiplo: Ventas LTM × margen × 4.0
- Valor = 50% DCF + 50% múltiplo; por acción = valor × (1 − DLOM)/100

**A5. Tasa de descuento (Ke = 21.6%), con fuente y fecha:**
| Componente | Valor | Fuente |
|---|---|---|
| M-Bono 10 años | 9.25% | Cetesdirecto, 09-nov-2026 (fuente secundaria) |
| Default spread soberano | 2.05% | Damodaran ene-2026 (1.62%) ajustado por la baja de Moody's a Baa3 (may-2026) |
| Rf local = M-Bono − default spread | 7.20% | Evita contar dos veces el riesgo país |
| βU Restaurant/Dining | 0.677 | Damodaran ene-2026, promedio EUA (0.739) y Global (0.615) |
| D/E de la industria | 27% | Damodaran, incluye arrendamientos |
| βL (Hamada, ISR 30%) | 0.805 | βU × (1 + 0.7 × 0.27) |
| ERP total México | 7.31% | ERP maduro 4.20% + CRP 3.11% (Damodaran; ajuste de jul-2026 no verificado) |
| Prima por tamaño | 5.0% | Kroll CRSP decil 10, histórico (no verificado; Kroll es de pago) |
| Riesgo específico | 3.5% | Persona clave 1.0, concentración turística 1.0, historial corto 0.5, regulatorio Centro Histórico 0.5, seguridad 0.5 |
| **Ke** | **21.6%** | 7.20% + 0.805 × 7.31% + 5.0% + 3.5% |

**A6. Crecimiento y escenarios.**
- Crecimiento de largo plazo: inflación 4.0% (instrucción de los socios; meta Banxico 3% ±1; INPC oct-2026 3.75%) + 0.5% real = 4.52% nominal.
- Reglas de margen:
  - Regla 1 (Garden): optimista = LTM, base = 6 meses, conservador = 3 meses.
  - Regla 2 (Presa): optimista = promedio histórico, base = LTM, conservador = 6 meses.

**A7. Múltiplo P/U de 4x.** Justificación: negocios privados pequeños de hospitalidad en México se ubican en 3–5x. Referencia: EV/EBITDA de mercado ~6.6x (Alsea ~5.0x no verificado; transacciones La Casa de Toño >8x no cerrada; Vips 2014 ~8.5x) menos 40% por tamaño.

**A8. Métodos considerados y descartados.**
- Comparables EV/EBITDA: no hay EBITDA.
- APV: no hay deuda.
- Valor de activos: falta inventario; pendiente como piso de Presa.
- VC Method y perpetuidad: no incluidos en esta versión, pero aplicables.

**A9. Validaciones del modelo.** Checks automáticos, todos en VERDADERO:
- Los % de socios suman 100%.
- Ke > g.
- Total = Garden + Presa.
- Mínimo ≤ base ≤ máximo.
- Las ventas LTM cuadran con la hoja Original.
- Los pesos suman 100%.
- El Excel recalcula sin errores.

**A10. Limitaciones e información pendiente.** Tabla de lo que falta, con su impacto:
- Estados financieros.
- Capital social real.
- Política de reinversión.
- Sueldos de socios.
- Deuda.
- Contrato de renta.
- Activos de Presa.
- Asientos, ticket y días de operación.

**A11. Guía de reproducibilidad.**
- La hoja Tablita contiene todos los supuestos editables.
- Mapa de hojas: Tablita → Valuación Total → Valuación Garden / Presa → Histórico → Supuestos → Checks → Original.
- Un revisor puede cambiar cualquier supuesto y ver el efecto en la tablita.

**A12. Glosario.** LTM, CAGR, DCF, Ke, P/U, DLOM, valor terminal, beta, ERP, CRP.

## ENTREGABLE
- Presentación lista para exportar a PDF y PowerPoint.
- En las notas del orador de cada diapositiva principal, 2–3 frases de guion para quien presente.
- **Última diapositiva:** "Cómo revisar esta valuación". Lista de 5 preguntas que un revisor debería hacerse, cada una con la diapositiva del apéndice que la responde:
  1. ¿La utilidad usada es representativa? → A3
  2. ¿La tasa es razonable? → A5
  3. ¿Por qué reglas distintas por unidad? → A6
  4. ¿Qué tan sensible es el valor? → diapositiva 10
  5. ¿Qué falta para que sea definitiva? → A10
