# Paso 0 · Pruebas estadísticas

**202 de 202 pruebas OK.** α = 0.01 con corrección Benjamini-Hochberg sobre todas las pruebas con p-valor. Montos en USD.

## Resumen por sección

| Sección | Pruebas | OK |
|---|---|---|
| A · Bondad de ajuste | 32 | 32 |
| B · Latentes | 12 | 12 |
| C · Target | 3 | 3 |
| D · Colas y curtosis | 72 | 72 |
| F · Dinero y medias | 26 | 26 |
| G · Sesgo | 38 | 38 |
| H · Variedad y duplicados | 7 | 7 |
| I · Semilla | 12 | 12 |

## A · Bondad de ajuste

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| KS sobre PIT: relationship_value · LogNormal truncada + cola Pareto | 0.0057 |  | 0.5410 | 0.9742 | PIT ~ U(0,1) | n = 20,000 | OK |
| Cramér-von Mises (colas): relationship_value · LogNormal truncada + cola Pareto | 0.1391 |  | 0.4245 | 0.9742 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: proporción depósitos · Beta(2,5) | 0.0081 |  | 0.2047 | 0.9742 | PIT ~ U(0,1) | n = 17,130 | OK |
| Cramér-von Mises (colas): proporción depósitos · Beta(2,5) | 0.2560 |  | 0.1809 | 0.9742 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: tenure_years (edad ≥ 68) · Gamma(2, 4.5) | 0.0194 |  | 0.0308 | 0.8253 | PIT ~ U(0,1) | n = 5,523 | OK |
| Cramér-von Mises (colas): tenure_years (edad ≥ 68) · Gamma(2, 4.5) | 0.5688 |  | 0.0267 | 0.8253 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: salary_base_annual · LogNormal ligada, piso $150k | 0.0063 |  | 0.7821 | 0.9767 | PIT ~ U(0,1) | n = 10,772 | OK |
| Cramér-von Mises (colas): salary_base_annual · LogNormal ligada, piso $150k | 0.0503 |  | 0.8742 | 0.9767 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: pension_monthly · LogNormal ligada, piso $2.5k | 0.0068 |  | 0.9054 | 0.9767 | PIT ~ U(0,1) | n = 6,801 | OK |
| Cramér-von Mises (colas): pension_monthly · LogNormal ligada, piso $2.5k | 0.0602 |  | 0.8128 | 0.9767 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: business_distribution_annual · LogNormal ligada | 0.0152 |  | 0.1693 | 0.9742 | PIT ~ U(0,1) | n = 5,287 | OK |
| Cramér-von Mises (colas): business_distribution_annual · LogNormal ligada | 0.2953 |  | 0.1394 | 0.9742 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: bono / sueldo (con bono) · 0.1 + 1.4·Beta(1.5,3) | 0.0096 |  | 0.4377 | 0.9742 | PIT ~ U(0,1) | n = 8,089 | OK |
| Cramér-von Mises (colas): bono / sueldo (con bono) · 0.1 + 1.4·Beta(1.5,3) | 0.1496 |  | 0.3908 | 0.9742 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: rendimiento dividendos · Beta(4,196) | 0.0087 |  | 0.4820 | 0.9742 | PIT ~ U(0,1) | n = 9,370 | OK |
| Cramér-von Mises (colas): rendimiento dividendos · Beta(4,196) | 0.1203 |  | 0.4941 | 0.9742 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| χ² edad entera · Normal truncada discretizada | 61.2700 | 66 | 0.6419 | 0.9742 | gl = celdas − 1 | 67 celdas tras unir esperadas < 5 | OK |
| χ² frecuencia de pago | 1.7650 | 2 | 0.4137 | 0.9742 | gl = categorías − 1 |  | OK |
| Hosmer-Lemeshow solo depósitos (p_i conocida) | 13.5792 | 10 | 0.1931 | 0.9742 | gl = g (0 parámetros estimados) | obs 0.1435 vs E[p] 0.1436 | OK |
| Binomial exacta: has_linked_business · HNW | 0.2494 |  | 0.8402 | 0.9767 | p = 0.25 | n = 18,897 | OK |
| Binomial exacta: has_linked_business · UHNW | 0.5213 |  | 0.0566 | 0.9112 | p = 0.55 | n = 1,103 | OK |
| Binomial exacta: has_trust · HNW | 0.2961 |  | 0.2433 | 0.9742 | p = 0.3 | n = 18,897 | OK |
| Binomial exacta: has_trust · UHNW | 0.7063 |  | 0.6694 | 0.9742 | p = 0.7 | n = 1,103 | OK |
| Binomial exacta: has_advisory | inversiones | 0.7036 |  | 0.3131 | 0.9742 | p = 0.7 | n = 17,130 | OK |
| Binomial exacta: has_credit_anchor | 0.3424 |  | 0.0242 | 0.8253 | p = 0.35 | n = 20,000 | OK |
| Binomial exacta: has_payroll_stream · activos | 0.7951 |  | 0.1657 | 0.9742 | p = 0.8 | n = 12,706 | OK |
| Binomial exacta: has_payroll_stream · retirados | 0.0919 |  | 0.0202 | 0.8253 | p = 0.1 | n = 7,294 | OK |
| Binomial exacta: has_pension_stream · activos | 0.0505 |  | 0.7757 | 0.9767 | p = 0.05 | n = 12,706 | OK |
| Binomial exacta: has_pension_stream · retirados | 0.8444 |  | 0.1788 | 0.9742 | p = 0.85 | n = 7,294 | OK |
| Binomial exacta: has_dividend_stream | inversiones | 0.5470 |  | 0.4290 | 0.9742 | p = 0.55 | n = 17,130 | OK |
| Binomial exacta: churn_excluded | 0.0062 |  | 0.7834 | 0.9767 | p = 0.006 | n = 20,000 | OK |
| Binomial exacta: sin_bono | nómina | 0.2491 |  | 0.8326 | 0.9767 | p = 0.25 | n = 10,772 | OK |

## B · Latentes

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| KS z_outflow ~ N(0,1) | 0.0051 |  | 0.6847 | 0.9767 | N(0,1) |  | OK |
| Curtosis (Anscombe-Glynn) z_outflow | 0.7105 |  | 0.4774 | 0.9742 | exceso = 0 | exceso = +0.0240 | OK |
| KS z_neglect ~ N(0,1) | 0.0061 |  | 0.4508 | 0.9742 | N(0,1) |  | OK |
| Curtosis (Anscombe-Glynn) z_neglect | 0.9086 |  | 0.3635 | 0.9742 | exceso = 0 | exceso = +0.0310 | OK |
| KS z_service ~ N(0,1) | 0.0059 |  | 0.4875 | 0.9742 | N(0,1) |  | OK |
| Curtosis (Anscombe-Glynn) z_service | 1.8087 |  | 0.0705 | 0.9458 | exceso = 0 | exceso = +0.0637 | OK |
| Fisher z: ρ(outflow, neglect) | -1.5214 |  | 0.1282 | 0.9742 | ρ = 0.35 | r = 0.3405 | OK |
| Fisher z: ρ(outflow, service) | -1.9947 |  | 0.0461 | 0.9112 | ρ = 0.25 | r = 0.2367 | OK |
| Fisher z: ρ(neglect, service) | -0.0614 |  | 0.9510 | 0.9815 | ρ = 0.3 | r = 0.2996 | OK |
| Mardia asimetría multivariada | 12.9553 | 10 | 0.2262 | 0.9742 | gl = p(p+1)(p+2)/6 |  | OK |
| Mardia curtosis multivariada | 2.3863 |  | 0.0170 | 0.8253 | b2 = p(p+2) = 15 |  | OK |
| KS riesgo idiosincrático ~ N(0, 0.6) | 0.0061 |  | 0.4349 | 0.9742 | N(0,σ) |  | OK |

## C · Target

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Hosmer-Lemeshow hard churn 6m | 5.1022 | 9 | 0.8253 | 0.9767 | gl = g − 1 (intercepto calibrado) |  | OK |
| Hosmer-Lemeshow soft churn 3m | 6.1398 | 9 | 0.7259 | 0.9767 | gl = g − 1 (intercepto calibrado) |  | OK |
| Eventos hard observados vs Σ p_i | 0.2418 |  | 0.8090 | 0.9767 | E[eventos] = Σp | 1200 vs 1192.6 | OK |

## D · Colas y curtosis

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Cola pesada en escala USD: relationship_value | 96.7549 |  |  |  | exceso > 0 (p < α) | exceso = 302.5; p = 0.0e+00 | OK |
| Cola pesada en escala USD: deposit_balance | 99.7711 |  |  |  | exceso > 0 (p < α) | exceso = 509.8; p = 0.0e+00 | OK |
| Cola pesada en escala USD: aum | 90.7043 |  |  |  | exceso > 0 (p < α) | exceso = 369.8; p = 0.0e+00 | OK |
| Cola pesada en escala USD: salary_base_annual | 38.0942 |  |  |  | exceso > 0 (p < α) | exceso = 6.6; p = 0.0e+00 | OK |
| Cola pesada en escala USD: bonus_annual | 37.7087 |  |  |  | exceso > 0 (p < α) | exceso = 10.1; p = 0.0e+00 | OK |
| Cola pesada en escala USD: pension_monthly | 26.7481 |  |  |  | exceso > 0 (p < α) | exceso = 4.7; p = 6.5e-158 | OK |
| Cola pesada en escala USD: dividend_annual | 66.7920 |  |  |  | exceso > 0 (p < α) | exceso = 333.9; p = 0.0e+00 | OK |
| Cola pesada en escala USD: business_distribution_annual | 41.4069 |  |  |  | exceso > 0 (p < α) | exceso = 44.5; p = 0.0e+00 | OK |
| Cola pesada en escala USD: recurring_income_monthly | 85.5430 |  |  |  | exceso > 0 (p < α) | exceso = 102.0; p = 0.0e+00 | OK |
| Curtosis de Φ⁻¹(PIT): relationship_value · LogNormal truncada + cola Pareto | 0.4895 |  | 0.6245 | 0.9742 | exceso = 0 | exceso = +0.0162 | OK |
| Jarque-Bera de Φ⁻¹(PIT): relationship_value · LogNormal truncada + cola Pareto | 0.2194 | 2 | 0.8961 | 0.9767 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): proporción depósitos · Beta(2,5) | 0.4417 |  | 0.6587 | 0.9742 | exceso = 0 | exceso = +0.0156 | OK |
| Jarque-Bera de Φ⁻¹(PIT): proporción depósitos · Beta(2,5) | 0.6335 | 2 | 0.7285 | 0.9767 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): tenure_years (edad ≥ 68) · Gamma(2, 4.5) | -1.0989 |  | 0.2718 | 0.9742 | exceso = 0 | exceso = -0.0728 | OK |
| Jarque-Bera de Φ⁻¹(PIT): tenure_years (edad ≥ 68) · Gamma(2, 4.5) | 1.6500 | 2 | 0.4382 | 0.9742 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): salary_base_annual · LogNormal ligada, piso $150k | -0.9344 |  | 0.3501 | 0.9742 | exceso = 0 | exceso = -0.0447 | OK |
| Jarque-Bera de Φ⁻¹(PIT): salary_base_annual · LogNormal ligada, piso $150k | 1.0889 | 2 | 0.5802 | 0.9742 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): pension_monthly · LogNormal ligada, piso $2.5k | -1.0700 |  | 0.2846 | 0.9742 | exceso = 0 | exceso = -0.0640 | OK |
| Jarque-Bera de Φ⁻¹(PIT): pension_monthly · LogNormal ligada, piso $2.5k | 1.2108 | 2 | 0.5458 | 0.9742 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): business_distribution_annual · LogNormal ligada | 0.4320 |  | 0.6657 | 0.9742 | exceso = 0 | exceso = +0.0260 | OK |
| Jarque-Bera de Φ⁻¹(PIT): business_distribution_annual · LogNormal ligada | 0.5022 | 2 | 0.7779 | 0.9767 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): bono / sueldo (con bono) · 0.1 + 1.4·Beta(1.5,3) | 1.0960 |  | 0.2731 | 0.9742 | exceso = 0 | exceso = +0.0591 | OK |
| Jarque-Bera de Φ⁻¹(PIT): bono / sueldo (con bono) · 0.1 + 1.4·Beta(1.5,3) | 1.1997 | 2 | 0.5489 | 0.9742 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): rendimiento dividendos · Beta(4,196) | 0.7116 |  | 0.4767 | 0.9742 | exceso = 0 | exceso = +0.0346 | OK |
| Jarque-Bera de Φ⁻¹(PIT): rendimiento dividendos · Beta(4,196) | 1.7059 | 2 | 0.4262 | 0.9742 | gl = 2 |  | OK |
| Curtosis log(patrimonio) del cuerpo vs teórica | -0.0295 |  | 0.9764 | 0.9845 | Normal doblemente truncada | obs -0.8704 vs teo -0.8693 | OK |
| α Pareto de la cola UHNW (MLE truncada) | 0.0195 |  | 0.9845 | 0.9845 | α = 1.5 | α̂ = 1.501 ± 0.049; n = 1,103 | OK |
| media típico vs semillas: relationship_value | 1.04e+07 |  | 0.6716 | 0.9742 | p empírico vs 200 semillas | percentil 66.4 | OK |
| media típico vs semillas: deposit_balance | 3.58e+06 |  | 0.0945 | 0.9742 | p empírico vs 200 semillas | percentil 95.3 | OK |
| media típico vs semillas: aum | 7.94e+06 |  | 0.6219 | 0.9742 | p empírico vs 200 semillas | percentil 31.1 | OK |
| media típico vs semillas: salary_base_annual | 441,213.1534 |  | 0.7015 | 0.9767 | p empírico vs 200 semillas | percentil 64.9 | OK |
| media típico vs semillas: bonus_annual | 248,775.3373 |  | 0.7512 | 0.9767 | p empírico vs 200 semillas | percentil 37.6 | OK |
| media típico vs semillas: pension_monthly | 10,522.4372 |  | 0.5025 | 0.9742 | p empírico vs 200 semillas | percentil 25.1 | OK |
| media típico vs semillas: dividend_annual | 161,385.8936 |  | 0.7811 | 0.9767 | p empírico vs 200 semillas | percentil 60.9 | OK |
| media típico vs semillas: business_distribution_annual | 859,594.6586 |  | 0.1741 | 0.9742 | p empírico vs 200 semillas | percentil 8.7 | OK |
| media típico vs semillas: recurring_income_monthly | 52,120.7119 |  | 0.2239 | 0.9742 | p empírico vs 200 semillas | percentil 11.2 | OK |
| curtosis_exceso típico vs semillas: relationship_value | 302.5097 |  | 0.4627 | 0.9742 | p empírico vs 200 semillas | percentil 23.1 | OK |
| curtosis_exceso típico vs semillas: deposit_balance | 509.8476 |  | 0.9403 | 0.9767 | p empírico vs 200 semillas | percentil 53.0 | OK |
| curtosis_exceso típico vs semillas: aum | 369.7646 |  | 0.8905 | 0.9767 | p empírico vs 200 semillas | percentil 55.5 | OK |
| curtosis_exceso típico vs semillas: salary_base_annual | 6.5936 |  | 0.2537 | 0.9742 | p empírico vs 200 semillas | percentil 12.7 | OK |
| curtosis_exceso típico vs semillas: bonus_annual | 10.0800 |  | 0.9602 | 0.9845 | p empírico vs 200 semillas | percentil 48.0 | OK |
| curtosis_exceso típico vs semillas: pension_monthly | 4.6907 |  | 0.5920 | 0.9742 | p empírico vs 200 semillas | percentil 29.6 | OK |
| curtosis_exceso típico vs semillas: dividend_annual | 333.9241 |  | 0.5920 | 0.9742 | p empírico vs 200 semillas | percentil 29.6 | OK |
| curtosis_exceso típico vs semillas: business_distribution_annual | 44.4965 |  | 0.7612 | 0.9767 | p empírico vs 200 semillas | percentil 61.9 | OK |
| curtosis_exceso típico vs semillas: recurring_income_monthly | 102.0008 |  | 0.8607 | 0.9767 | p empírico vs 200 semillas | percentil 57.0 | OK |
| curtosis_exceso_log típico vs semillas: relationship_value | 0.4929 |  | 0.6716 | 0.9742 | p empírico vs 200 semillas | percentil 33.6 | OK |
| curtosis_exceso_log típico vs semillas: deposit_balance | 0.4600 |  | 0.3831 | 0.9742 | p empírico vs 200 semillas | percentil 80.8 | OK |
| curtosis_exceso_log típico vs semillas: aum | 0.4123 |  | 0.5721 | 0.9742 | p empírico vs 200 semillas | percentil 28.6 | OK |
| curtosis_exceso_log típico vs semillas: salary_base_annual | -0.2399 |  | 0.2637 | 0.9742 | p empírico vs 200 semillas | percentil 13.2 | OK |
| curtosis_exceso_log típico vs semillas: bonus_annual | -0.2387 |  | 0.0945 | 0.9742 | p empírico vs 200 semillas | percentil 4.7 | OK |
| curtosis_exceso_log típico vs semillas: pension_monthly | -0.1932 |  | 0.3333 | 0.9742 | p empírico vs 200 semillas | percentil 16.7 | OK |
| curtosis_exceso_log típico vs semillas: dividend_annual | 0.3515 |  | 0.6119 | 0.9742 | p empírico vs 200 semillas | percentil 69.4 | OK |
| curtosis_exceso_log típico vs semillas: business_distribution_annual | 0.0470 |  | 0.6716 | 0.9742 | p empírico vs 200 semillas | percentil 66.4 | OK |
| curtosis_exceso_log típico vs semillas: recurring_income_monthly | 0.7312 |  | 0.8905 | 0.9767 | p empírico vs 200 semillas | percentil 55.5 | OK |
| L_curtosis típico vs semillas: relationship_value | 0.4449 |  | 0.7413 | 0.9767 | p empírico vs 200 semillas | percentil 37.1 | OK |
| L_curtosis típico vs semillas: deposit_balance | 0.4516 |  | 0.3234 | 0.9742 | p empírico vs 200 semillas | percentil 83.8 | OK |
| L_curtosis típico vs semillas: aum | 0.4447 |  | 0.5323 | 0.9742 | p empírico vs 200 semillas | percentil 26.6 | OK |
| L_curtosis típico vs semillas: salary_base_annual | 0.1732 |  | 0.5920 | 0.9742 | p empírico vs 200 semillas | percentil 29.6 | OK |
| L_curtosis típico vs semillas: bonus_annual | 0.1877 |  | 0.4527 | 0.9742 | p empírico vs 200 semillas | percentil 22.6 | OK |
| L_curtosis típico vs semillas: pension_monthly | 0.1603 |  | 0.2537 | 0.9742 | p empírico vs 200 semillas | percentil 12.7 | OK |
| L_curtosis típico vs semillas: dividend_annual | 0.4722 |  | 0.7313 | 0.9767 | p empírico vs 200 semillas | percentil 63.4 | OK |
| L_curtosis típico vs semillas: business_distribution_annual | 0.2769 |  | 0.8308 | 0.9767 | p empírico vs 200 semillas | percentil 58.5 | OK |
| L_curtosis típico vs semillas: recurring_income_monthly | 0.3026 |  | 0.3731 | 0.9742 | p empírico vs 200 semillas | percentil 18.7 | OK |
| hill_alpha_top1% típico vs semillas: relationship_value | 1.7761 |  | 0.3532 | 0.9742 | p empírico vs 200 semillas | percentil 82.3 | OK |
| hill_alpha_top1% típico vs semillas: deposit_balance | 1.6508 |  | 0.4826 | 0.9742 | p empírico vs 200 semillas | percentil 24.1 | OK |
| hill_alpha_top1% típico vs semillas: aum | 1.8300 |  | 0.2040 | 0.9742 | p empírico vs 200 semillas | percentil 89.8 | OK |
| hill_alpha_top1% típico vs semillas: salary_base_annual | 5.4502 |  | 0.7811 | 0.9767 | p empírico vs 200 semillas | percentil 60.9 | OK |
| hill_alpha_top1% típico vs semillas: bonus_annual | 4.5354 |  | 0.9403 | 0.9767 | p empírico vs 200 semillas | percentil 47.0 | OK |
| hill_alpha_top1% típico vs semillas: pension_monthly | 5.9259 |  | 0.9403 | 0.9767 | p empírico vs 200 semillas | percentil 47.0 | OK |
| hill_alpha_top1% típico vs semillas: dividend_annual | 1.6205 |  | 0.8209 | 0.9767 | p empírico vs 200 semillas | percentil 41.0 | OK |
| hill_alpha_top1% típico vs semillas: business_distribution_annual | 2.8553 |  | 0.4527 | 0.9742 | p empírico vs 200 semillas | percentil 22.6 | OK |
| hill_alpha_top1% típico vs semillas: recurring_income_monthly | 2.6630 |  | 0.8706 | 0.9767 | p empírico vs 200 semillas | percentil 43.5 | OK |

## F · Dinero y medias

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| USD válido: relationship_value | 9.04e+08 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $903,973,258 | OK |
| USD válido: deposit_balance | 4.20e+08 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $419,923,775 | OK |
| USD válido: aum | 7.73e+08 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $773,011,258 | OK |
| USD válido: salary_base_annual | 2.65e+06 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $2,645,329 | OK |
| USD válido: bonus_annual | 2.42e+06 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $2,417,736 | OK |
| USD válido: pension_monthly | 53,462.4600 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $53,462 | OK |
| USD válido: dividend_annual | 1.58e+07 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $15,794,163 | OK |
| USD válido: business_distribution_annual | 1.67e+07 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $16,691,167 | OK |
| USD válido: recurring_income_monthly | 2.00e+06 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $2,000,230 | OK |
| USD válido: value_lost_6m | 6.61e+08 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $660,692,164 | OK |
| Media = teórica: relationship_value | 0.4320 |  | 0.6657 | 0.9742 | t de una muestra | obs 10,381,939.7866 vs teo 10,306,614.6886 | OK |
| Media = teórica: proporción depósitos (inversión) | 1.4751 |  | 0.1402 | 0.9742 | t de una muestra | obs 0.2875 vs teo 0.2857 | OK |
| Media = teórica: tenure_years (edad ≥ 68) | 1.6343 |  | 0.1022 | 0.9742 | t de una muestra | obs 9.1385 vs teo 9.0000 | OK |
| Media = teórica: age_primary | -0.4752 |  | 0.6346 | 0.9742 | t de una muestra | obs 60.4834 vs teo 60.5228 | OK |
| Banda de negocio: relationship_value_mean | 1.04e+07 |  |  |  | [5,000,000, 15,000,000] |  | OK |
| Banda de negocio: relationship_value_median | 4.84e+06 |  |  |  | [3,000,000, 8,000,000] |  | OK |
| Banda de negocio: deposit_share_mean | 0.2875 |  |  |  | [0.2, 0.45] |  | OK |
| Banda de negocio: salary_base_annual_median | 378,819.2100 |  |  |  | [250,000, 600,000] |  | OK |
| Banda de negocio: bonus_to_salary_mean | 0.4230 |  |  |  | [0.3, 0.8] |  | OK |
| Banda de negocio: pension_monthly_median | 9,280.5500 |  |  |  | [5,000, 15,000] |  | OK |
| Banda de negocio: dividend_yield_mean | 0.0200 |  |  |  | [0.015, 0.025] |  | OK |
| Banda de negocio: recurring_income_monthly_median | 33,515.6200 |  |  |  | [15,000, 60,000] |  | OK |
| Banda de negocio: age_primary_mean | 60.4834 |  |  |  | [55, 65] |  | OK |
| Banda de negocio: tenure_years_mean | 8.9860 |  |  |  | [6, 12] |  | OK |
| Banda de negocio: hard_churn_6m_rate | 0.0604 |  |  |  | [0.03, 0.1] |  | OK |
| Banda de negocio: soft_churn_3m_rate | 0.0883 |  |  |  | [0.05, 0.15] |  | OK |

## G · Sesgo

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Independencia Spearman: relationship_value ⟂ age_primary | -0.0034 |  | 0.6311 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: relationship_value ⟂ tenure_years | 0.0054 |  | 0.4413 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: bonus_share ⟂ salary_base_annual | 0.0025 |  | 0.7931 | 0.9767 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: div_yield ⟂ aum | 0.0115 |  | 0.2669 | 0.9742 | ρ = 0 | n = 9,370 | OK |
| Independencia Spearman: has_credit_anchor ⟂ relationship_value | 0.0064 |  | 0.3677 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: age_primary ⟂ has_credit_anchor | -0.0128 |  | 0.0693 | 0.9458 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ relationship_value | -1.41e-04 |  | 0.9841 | 0.9845 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ age_primary | 0.0091 |  | 0.1983 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ tenure_years | 0.0022 |  | 0.7596 | 0.9767 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ salary_base_annual | 7.57e-04 |  | 0.9373 | 0.9767 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: z_outflow ⟂ has_investments | -0.0058 |  | 0.4137 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ has_trust | -0.0072 |  | 0.3092 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ relationship_value | 7.50e-04 |  | 0.9155 | 0.9767 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ age_primary | 0.0079 |  | 0.2641 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ tenure_years | -0.0049 |  | 0.4923 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ salary_base_annual | 0.0107 |  | 0.2668 | 0.9742 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: z_neglect ⟂ has_investments | -7.73e-04 |  | 0.9130 | 0.9767 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ has_trust | -5.49e-04 |  | 0.9381 | 0.9767 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ relationship_value | -0.0042 |  | 0.5549 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ age_primary | 0.0157 |  | 0.0267 | 0.8253 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ tenure_years | 0.0021 |  | 0.7642 | 0.9767 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ salary_base_annual | 0.0127 |  | 0.1858 | 0.9742 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: z_service ⟂ has_investments | -0.0110 |  | 0.1189 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ has_trust | 0.0137 |  | 0.0519 | 0.9112 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ relationship_value | 0.0044 |  | 0.5296 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ age_primary | 0.0095 |  | 0.1777 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ tenure_years | 0.0138 |  | 0.0505 | 0.9112 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ salary_base_annual | -0.0051 |  | 0.5934 | 0.9742 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ has_investments | -0.0062 |  | 0.3808 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ has_trust | -0.0079 |  | 0.2648 | 0.9742 | ρ = 0 | n = 20,000 | OK |
| Target ⟂ frecuencia de pago (con nómina) | 2.0072 | 2 | 0.3666 | 0.9742 | gl = (r−1)(c−1) |  | OK |
| Target ⟂ advisory (con inversiones) | 1.3515 | 1 | 0.2450 | 0.9742 | gl = (r−1)(c−1) |  | OK |
| Target ⟂ dividendos (con inversiones) | 0.3503 | 1 | 0.5540 | 0.9742 | gl = (r−1)(c−1) |  | OK |
| Target ⟂ trust (HNW) | 0.0134 | 1 | 0.9077 | 0.9767 | gl = (r−1)(c−1) |  | OK |
| Target ⟂ negocio vinculado (HNW) | 0.0399 | 1 | 0.8416 | 0.9767 | gl = (r−1)(c−1) |  | OK |
| Efecto diseñado: crédito ancla reduce riesgo | -0.1505 |  |  |  | signo correcto y p < α | Δ índice = -0.151; p = 8.1e-24 | OK |
| Efecto diseñado: UHNW aumenta riesgo | 0.1278 |  |  |  | signo correcto y p < α | Δ índice = +0.128; p = 7.5e-05 | OK |
| Efecto diseñado: antigüedad reduce riesgo | -0.0731 |  |  |  | ρ < 0 y p < α | p = 5.5e-25 | OK |

## H · Variedad y duplicados

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Filas duplicadas exactas (sin id) | 0.0000 |  |  |  | = 0 |  | OK |
| Vectores latentes duplicados | 0.0000 |  |  |  | = 0 |  | OK |
| Repeticiones de monto por redondeo: relationship_value | 1.0000 |  |  |  | ≤ Poisson(λ) p99.9 | obs 1 vs esperadas λ = 0.2 (máx 2) | OK |
| Repeticiones de monto por redondeo: salary_base_annual | 2.0000 |  |  |  | ≤ Poisson(λ) p99.9 | obs 2 vs esperadas λ = 1.0 (máx 5) | OK |
| Repeticiones de monto por redondeo: pension_monthly | 14.0000 |  |  |  | ≤ Poisson(λ) p99.9 | obs 14 vs esperadas λ = 15.2 (máx 29) | OK |
| Repeticiones de monto por redondeo: business_distribution_annual | 0.0000 |  |  |  | ≤ Poisson(λ) p99.9 | obs 0 vs esperadas λ = 0.1 (máx 2) | OK |
| Pares casi idénticos (dist < 0.01 d.e., mismas banderas) | 0.0000 |  |  |  | = 0 | distancia mínima al vecino = 0.0517 | OK |

## I · Semilla

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Semilla no atípica: tasa hard 6m | 0.0604 |  | 0.8706 | 0.9767 | percentil en rango | percentil 56 | OK |
| Semilla no atípica: tasa soft 3m | 0.0883 |  | 0.3085 | 0.9742 | percentil en rango | percentil 15 | OK |
| Semilla no atípica: AUC techo | 0.8508 |  | 0.7612 | 0.9767 | percentil en rango | percentil 62 | OK |
| Semilla no atípica: media relationship_value | 1.04e+07 |  | 0.6716 | 0.9742 | percentil en rango | percentil 66 | OK |
| Semilla no atípica: mediana relationship_value | 4.84e+06 |  | 0.5821 | 0.9742 | percentil en rango | percentil 71 | OK |
| Semilla no atípica: share UHNW | 0.0551 |  | 0.2040 | 0.9742 | percentil en rango | percentil 90 | OK |
| Semilla no atípica: mediana sueldo | 378,819.2100 |  | 0.9801 | 0.9845 | percentil en rango | percentil 49 | OK |
| Semilla no atípica: curtosis log valor | 0.4929 |  | 0.6716 | 0.9742 | percentil en rango | percentil 34 | OK |
| Semilla no atípica: L-curtosis valor | 0.4449 |  | 0.7413 | 0.9767 | percentil en rango | percentil 37 | OK |
| Semilla no atípica: Hill α valor | 1.7761 |  | 0.3532 | 0.9742 | percentil en rango | percentil 82 | OK |
| p-valores entre semillas ~ U(0,1): KS p relationship_value | 0.0742 |  | 0.2106 | 0.9742 | generador sin sesgo sistemático |  | OK |
| p-valores entre semillas ~ U(0,1): KS p sueldo | 0.0420 |  | 0.8572 | 0.9767 | generador sin sesgo sistemático |  | OK |

## Perfil de colas por columna (USD, valores > 0)

|                              |          n |          media |       mediana |             sd |   asimetría |   curtosis_exceso |   curtosis_exceso_log |   L_asimetría |   L_curtosis |   p99/p50 |   hill_alpha_top1% |
|:-----------------------------|-----------:|---------------:|--------------:|---------------:|------------:|------------------:|----------------------:|--------------:|-------------:|----------:|-------------------:|
| relationship_value           | 20,000.000 | 10,381,939.787 | 4,841,540.750 | 24,658,658.091 |      13.788 |           302.510 |                 0.493 |         0.610 |        0.445 |    19.116 |              1.776 |
| deposit_balance              | 20,000.000 |  3,581,436.986 | 1,551,416.205 |  9,768,177.429 |      17.746 |           509.848 |                 0.460 |         0.613 |        0.452 |    20.437 |              1.651 |
| aum                          | 17,130.000 |  7,939,874.841 | 3,696,462.085 | 18,748,549.054 |      14.475 |           369.765 |                 0.412 |         0.608 |        0.445 |    19.603 |              1.830 |
| salary_base_annual           | 10,772.000 |    441,213.153 |   378,819.210 |    245,516.576 |       1.979 |             6.594 |                -0.240 |         0.288 |        0.173 |     3.429 |              5.450 |
| bonus_annual                 |  8,089.000 |    248,775.337 |   194,590.050 |    197,742.739 |       2.358 |            10.080 |                -0.239 |         0.315 |        0.188 |     4.971 |              4.535 |
| pension_monthly              |  6,801.000 |     10,522.437 |     9,280.550 |      5,450.636 |       1.640 |             4.691 |                -0.193 |         0.242 |        0.160 |     3.087 |              5.926 |
| dividend_annual              |  9,370.000 |    161,385.894 |    66,637.705 |    441,890.891 |      14.731 |           333.924 |                 0.352 |         0.634 |        0.472 |    22.613 |              1.620 |
| business_distribution_annual |  5,287.000 |    859,594.659 |   568,138.960 |    990,179.319 |       4.897 |            44.497 |                 0.047 |         0.435 |        0.277 |     8.115 |              2.855 |
| recurring_income_monthly     | 18,656.000 |     52,120.712 |    33,515.620 |     69,652.953 |       6.936 |           102.001 |                 0.731 |         0.448 |        0.303 |     9.653 |              2.663 |

## Grados de libertad de la t-Student (estudio para los Pasos 1+)

Réplicas de n = 20,000. La curtosis de exceso teórica de t(ν) es 6/(ν−4): infinita para ν ≤ 4.

|   ν |   curtosis_exceso_teórica |   curtosis_muestral_mediana |   curtosis_muestral_p5 |   curtosis_muestral_p95 |   CV_curtosis |   ν_MLE_media |   ν_MLE_sesgo_% |   ν_MLE_p5 |   ν_MLE_p95 |
|----:|--------------------------:|----------------------------:|-----------------------:|------------------------:|--------------:|--------------:|----------------:|-----------:|------------:|
|   4 |                   inf     |                      10.513 |                  6.027 |                  43.298 |         1.983 |         4.000 |          -0.004 |      3.821 |       4.160 |
|   5 |                     6.000 |                       4.285 |                  2.869 |                   9.714 |         0.451 |         4.991 |          -0.179 |      4.731 |       5.309 |
|   6 |                     3.000 |                       2.536 |                  2.015 |                   3.817 |         0.199 |         5.956 |          -0.727 |      5.590 |       6.276 |
|   8 |                     1.500 |                       1.402 |                  1.160 |                   1.842 |         0.247 |         7.996 |          -0.055 |      7.335 |       8.908 |

## Semilla de producción vs 200 semillas de referencia

| métrica                    |   semilla producción |          ref p5 |     ref mediana |         ref p95 |   percentil |
|:---------------------------|---------------------:|----------------:|----------------:|----------------:|------------:|
| tasa hard 6m               |               0.0604 |          0.0579 |          0.0601 |          0.0626 |     56.4677 |
| tasa soft 3m               |               0.0883 |          0.0870 |          0.0901 |          0.0931 |     15.4229 |
| AUC techo                  |               0.8508 |          0.8398 |          0.8494 |          0.8574 |     61.9403 |
| media relationship_value   |      10,381,939.7866 | 10,051,001.5217 | 10,311,227.4587 | 10,617,421.3939 |     66.4179 |
| mediana relationship_value |       4,841,540.7500 |  4,740,295.3707 |  4,821,827.8150 |  4,895,271.0785 |     70.8955 |
| share UHNW                 |               0.0551 |          0.0505 |          0.0534 |          0.0557 |     89.8010 |
| mediana sueldo             |         378,819.2100 |    374,547.1790 |    378,902.8325 |    382,859.2432 |     49.0050 |
| curtosis log valor         |               0.4929 |          0.3987 |          0.5338 |          0.6498 |     33.5821 |
| L-curtosis valor           |               0.4449 |          0.4324 |          0.4493 |          0.4655 |     37.0647 |
| Hill α valor               |               1.7761 |          1.5148 |          1.6599 |          1.8458 |     82.3383 |
| KS p relationship_value    |               0.5410 |          0.0404 |          0.5224 |          0.9494 |     50.4975 |
| KS p sueldo                |               0.7821 |          0.0488 |          0.5211 |          0.9407 |     78.8557 |

## Variedad

- combinaciones de banderas: 298
- la más común (%): 5.0850
- distancia al vecino p1: 0.1669
- distancia al vecino mediana: 0.5288
