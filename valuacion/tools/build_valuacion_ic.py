# -*- coding: utf-8 -*-
"""Generador del modelo de valuación IC — restaurante Guanajuato capital.
Replica la arquitectura de Shivai_Valuacion_v6_corregido.xlsx con correcciones."""
import sys, datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.chart import BarChart, Reference
from openpyxl.worksheet.datavalidation import DataValidation

OUT = sys.argv[1]
wb = openpyxl.Workbook(); wb.remove(wb.active)
FONT = 'Arial'
BLUE, GREEN, BLACK, GREY, WHITE = '0000FF', '008000', '000000', '595959', 'FFFFFF'
NAVY = '1F3864'
F_HDR = PatternFill('solid', fgColor=NAVY); F_SEC = PatternFill('solid', fgColor='D9E1F2')
F_PEND = PatternFill('solid', fgColor='FCE4D6'); F_KEY = PatternFill('solid', fgColor='E2EFDA')
F_ALERT = PatternFill('solid', fgColor='FFC7CE')
CUR = '$#,##0;($#,##0);"-"'; CUR2 = '$#,##0.00;($#,##0.00);"-"'; PCT = '0.0%;(0.0%);"-"'; PCT2 = '0.00%;(0.00%);"-"'
MULT = '0.0"x"'; NUM = '#,##0;(#,##0);"-"'; NUM1 = '#,##0.0;(#,##0.0);"-"'; DEC = '0.00'; DEC4 = '0.0000'
PEND_TXT = 'Supuesto pendiente de validar'
N = 10  # años de proyección
YC = [CL(2 + t) for t in range(0, N + 1)]  # B=año0, C..L años 1..10

def q(name): return "'" + name.replace("'", "''") + "'!"

def W(ws, addr, v, fmt=None, bold=False, kind=None, fill=None, size=10, italic=False, wrap=False, align=None, color=None):
    c = ws[addr]
    c.value = v
    if color is None:
        if kind == 'input': color = BLUE
        elif isinstance(v, str) and v.startswith('='): color = GREEN if '!' in v else BLACK
        elif isinstance(v, (int, float, datetime.date)) and not isinstance(v, bool): color = BLUE
        else: color = BLACK
    c.font = Font(name=FONT, bold=bold, color=color, size=size, italic=italic)
    if fmt: c.number_format = fmt
    if fill: c.fill = fill
    if wrap or align: c.alignment = Alignment(horizontal=align, vertical='top', wrap_text=wrap)
    return c

def title(ws, t, sub):
    W(ws, 'A1', t, bold=True, size=14, color=NAVY)
    W(ws, 'A2', sub, italic=True, color=GREY)
    W(ws, 'A3', 'Convención: azul = input editable · negro = fórmula · verde = vínculo entre hojas · fondo naranja = ' + PEND_TXT, italic=True, color=GREY, size=8)

def sec(ws, r, t, ncol=8):
    for c in range(1, ncol + 1): ws.cell(r, c).fill = F_SEC
    W(ws, f'A{r}', t, bold=True, fill=F_SEC)

def hdr(ws, r, labels, start=1):
    for j, h in enumerate(labels):
        c = ws.cell(r, start + j); c.value = h
        c.font = Font(name=FONT, bold=True, color=WHITE); c.fill = F_HDR
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

def widths(ws, d):
    for k, v in d.items(): ws.column_dimensions[k].width = v

# ======================================================================================
# 1. SUPUESTOS
# ======================================================================================
S = wb.create_sheet('Supuestos'); SN = q('Supuestos')
R = {}          # registro de celdas
PENDING = []    # (label, ref, fuente)
title(S, '=Supuestos!$B$6&" — MODELO INTEGRAL DE VALUACIÓN  |  Supuestos & Inputs"',
      'Cifras en MXN nominales, sin IVA, sin propinas. Fecha de corte de mercado: 11-nov-2026. Toda celda fuera de inputs es fórmula viva.')
widths(S, {'A': 60, 'B': 15, 'C': 15, 'D': 15, 'E': 15, 'F': 12, 'G': 90, 'H': 30})
r = 5
def row_in(key, label, val, fmt=None, unit='', src='', pend=False, status=None, kind='input'):
    global r
    W(S, f'A{r}', label)
    c = W(S, f'B{r}', val, fmt, kind=kind if not (isinstance(val, str) and val.startswith('=')) else None,
          fill=F_PEND if pend else None)
    W(S, f'F{r}', unit, color=GREY)
    W(S, f'G{r}', src, italic=True, color=GREY, wrap=False)
    st = status if status else (PEND_TXT if pend else '')
    if st: W(S, f'H{r}', st, color='C65911' if pend else GREY, bold=pend, fill=F_PEND if pend else None)
    R[key] = f'{SN}$B${r}'
    if pend: PENDING.append((label, f'Supuestos!B{r}', src))
    r += 1
    return R[key]

def row_f(key, label, formula, fmt=None, unit='', src='', bold=False, fill=None):
    global r
    W(S, f'A{r}', label, bold=bold)
    W(S, f'B{r}', formula, fmt, bold=bold, fill=fill)
    W(S, f'F{r}', unit, color=GREY); W(S, f'G{r}', src, italic=True, color=GREY)
    R[key] = f'{SN}$B${r}'; r += 1
    return R[key]

def section(t):
    global r
    r += 1; sec(S, r, t); r += 1

hdr(S, 4, ['Variable', 'Valor', '', '', '', 'Unidad', 'Fuente / razón (fecha de corte)', 'Estatus'])
# ---- A. Identificación
sec(S, r, 'A. IDENTIFICACIÓN Y CONTROL DEL MODELO'); r += 1
row_in('name', 'Nombre del restaurante', '[NOMBRE DEL RESTAURANTE]', pend=True, src='Input del cliente — no proporcionado en el brief.')
row_in('zone', 'Ubicación', 'Centro Histórico — [ZONA], Guanajuato, Gto.', pend=True, src='Input del cliente — no proporcionado en el brief.')
row_in('cut', 'Fecha de corte de la valuación', datetime.date(2026, 11, 11), 'dd-mmm-yyyy', src='Fecha de corte de datos de mercado.')
row_in('base_year', 'Año base (Año 0 = cierre 2026 / inversión)', 2026, '0', src='Año 1 de proyección = año base + 1.')
row_in('gf', '¿Greenfield? (1 = apertura nueva con ramp-up y CapEx inicial; 0 = en operación)', 1, '0', pend=True,
       src='Brief menciona CapEx inicial, monto a levantar y ramp-up → se asume apertura. Confirmar con el cliente.')
row_in('scen', 'Escenario activo en hojas de detalle (1 Optimista · 2 Base ★ · 3 Conservador · 4 Estrés)', 2, '0',
       src='Las hojas de método muestran el escenario activo; Resumen y Escenarios calculan los 4 en paralelo.')
dv = DataValidation(type='whole', operator='between', formula1='1', formula2='4'); S.add_data_validation(dv); dv.add(R['scen'].split('!')[1].replace('$', ''))
row_in('mid', 'Convención de medio año en descuento (1 = sí, 0 = fin de año)', 1, '0',
       src='Práctica estándar en fairness opinions: los flujos de un restaurante ocurren a lo largo del año.')
row_in('tv_method', 'Método de valor terminal base (1 = vida finita por arrendamiento ★, 2 = Gordon perpetuo)', 1, '0',
       src='Base = vida finita: el negocio no sobrevive a su local; Gordon se presenta como cota superior.')

# ---- B. Costo de capital
section('B. COSTO DE CAPITAL — CAPM MÉXICO EN MXN (enfoque local: Rf M-Bono neto de default spread + β × ERP total México)')
W(S, f'A{r}', 'Enfoque: el M-Bono 10a ya incluye el default spread soberano. Para no contarlo dos veces, se resta el default spread y se suma el ERP total de México '
             '(ERP maduro + CRP) de Damodaran. Así el riesgo país entra una sola vez, escalado a riesgo accionario. Cross-check en USD (Fisher) abajo.',
  italic=True, color=GREY, size=8); r += 1
row_in('mbono', 'M-Bono 10 años (rendimiento)', 0.0925, PCT2, src='Cetesdirecto, tabla Bonos M, 09-nov-2026 (Banxico SIE no accesible desde la sesión). Rango 2026: 8.95%–9.45%.',
       status='Fuente secundaria — verificar en Banxico SIE')
row_in('ds_jan', 'Default spread soberano México (Damodaran, ene-2026, Baa2)', 0.0162, PCT2, src='Damodaran ctryprem, ene-2026 (vía buscador; acceso directo bloqueado).', status='Fuente secundaria — verificar')
row_in('crp_jan', 'Country Risk Premium México (Damodaran, ene-2026)', 0.0246, PCT2, src='Damodaran ctryprem ene-2026: 1.62% × 1.52 (σ acciones/σ bonos). Coincide con UPI 22-ene-2026.', status='Verificado (2 fuentes)')
row_in('crp_adj', 'Ajuste CRP por downgrade Moody\'s Baa2→Baa3 (20-may-2026)', 0.0065, PCT2,
       src='ERP total México jul-2026 = 7.31% (reportado) vs 6.69% ene-2026, menos −0.03pp de cambio en ERP maduro → +0.65pp.', pend=True)
row_f('scalar', 'Escalar σ acciones / σ bonos (implícito)', f'={R["crp_jan"]}/{R["ds_jan"]}', DEC, src='Derivado de las dos celdas anteriores.')
row_f('ds', 'Default spread ajustado (Baa3)', f'={R["ds_jan"]}+{R["crp_adj"]}/{R["scalar"]}', PCT2)
row_f('rf', 'Rf local libre de default = M-Bono − default spread', f'={R["mbono"]}-{R["ds"]}', PCT2, bold=True)
row_in('erp_m', 'ERP de mercado maduro (Damodaran implied ERP EUA)', 0.042, PCT2, src='Damodaran, 01-oct-2026 = 4.20% (inicio 2026: 4.23%). Base consistente con bono a 10 años (no mezclar con Kroll 5.0% sobre UST 20a).', status='Fuente secundaria — verificar')
row_f('crp', 'CRP México ajustado', f'={R["crp_jan"]}+{R["crp_adj"]}', PCT2)
row_f('erp', 'ERP total México = ERP maduro + CRP', f'={R["erp_m"]}+{R["crp"]}', PCT2, bold=True)
W(S, f'A{r}', 'Beta — Hamada: desapalancar con D/E de MERCADO de comparables; re-apalancar con estructura objetivo de la empresa', bold=True); r += 1
row_in('bl_us', 'β apalancada Restaurant/Dining EUA (64 firmas)', 0.92, DEC, src='Damodaran Betas.html, ene-2026 (dos snippets idénticos).', status='Verificado (2 fuentes)')
row_in('de_us', 'D/E de mercado Restaurant/Dining EUA (incluye arrendamientos)', 0.2722, PCT, src='Damodaran Betas.html, ene-2026. Damodaran capitaliza arrendamientos como deuda desde 2019.', status='Verificado (2 fuentes)')
row_in('t_us', 'Tasa efectiva comparables EUA', 0.0992, PCT, src='Damodaran Betas.html, ene-2026.', status='Verificado (2 fuentes)')
row_f('bu_us', 'β desapalancada EUA = βL / (1 + (1−t)·D/E)', f'={R["bl_us"]}/(1+(1-{R["t_us"]})*{R["de_us"]})', DEC4)
row_in('bl_gl', 'β apalancada Restaurant/Dining Global (410 firmas)', 0.75, DEC, src='Damodaran tabla Global (vía buscador; fecha ene-25/ene-26 en conflicto). Emerging Markets no localizado.', status='Fuente secundaria — verificar EM')
row_in('de_gl', 'D/E de mercado Restaurant/Dining Global', 0.2601, PCT, src='Damodaran tabla Global.', status='Fuente secundaria — verificar')
row_in('t_gl', 'Tasa efectiva comparables Global', 0.1521, PCT, src='Damodaran tabla Global.', status='Fuente secundaria — verificar')
row_f('bu_gl', 'β desapalancada Global', f'={R["bl_gl"]}/(1+(1-{R["t_gl"]})*{R["de_gl"]})', DEC4)
row_f('bu', 'β desapalancada aplicada (promedio EUA / Global)', f'=AVERAGE({R["bu_us"]},{R["bu_gl"]})', DEC4, bold=True,
      src='Sin dato EM verificable: promedio de EUA (mercado maduro, más profundo) y Global (incluye EM).')
row_in('isr', 'ISR — tasa corporativa', 0.30, PCT, src='LISR art. 9.', status='Verificado (ley)')
row_in('de_lease', 'D/E objetivo para re-apalancar = (deuda fin. + pasivo arrendamiento NIF D-5) / equity', 1.50, PCT, pend=True,
       src='Consistencia con Damodaran (D/E con arrendamientos) y con FCF pre-IFRS16 (la renta queda dentro del flujo → el equity carga el apalancamiento operativo del local). Validado contra el D/E implícito en hoja Checks.')
row_f('bl', 'β re-apalancada empresa = βU × (1 + (1−t)·D/E objetivo)', f'={R["bu"]}*(1+(1-{R["isr"]})*{R["de_lease"]})', DEC4, bold=True)
W(S, f'A{r}', 'Primas adicionales (sin iliquidez: la iliquidez se aplica una sola vez vía DLOM sobre el equity)', bold=True); r += 1
row_in('size', 'Prima por tamaño (Kroll CRSP decil 10)', 0.05, PCT2, pend=True,
       src='Kroll Navigator (de pago) no accesible. Decil 10 histórico ~4.7–5.6%; decil 10z ~11.4% (Pepperdine JEF 2025) se usa como sensibilidad, no en base, para no duplicar con CSRP.')
W(S, f'A{r}', 'CSRP — riesgo específico (desglose; juicio del valuador, sin plugs):', bold=True); r += 1
row_in('csrp1', '  a) Unidad única, sin historial operativo (greenfield)', 0.015, PCT2, pend=True, src='Sin datos POS ni EEFF; riesgo de ejecución de apertura. Baja a 0.5% si hay ≥24 meses de historia auditada.')
row_in('csrp2', '  b) Dependencia de persona clave (chef / socio operador)', 0.01, PCT2, pend=True, src='Típico en restaurantes independientes; mitigable con key-man insurance y non-compete.')
row_in('csrp3', '  c) Concentración de demanda (Cervantino, Semana Santa, estudiantes UG)', 0.01, PCT2, pend=True, src='OTEG: ocupación hotelera dic-25 37% vs Cervantino 2026 60% → alta volatilidad mensual.')
row_in('csrp4', '  d) Regulatorio Centro Histórico (INAH, licencia de alcoholes, PC)', 0.005, PCT2, pend=True, src='Zona de Monumentos (UNESCO 1988): obra, fachada, anuncios y terraza requieren autorización INAH/municipal.')
row_in('csrp5', '  e) Seguridad regional', 0.005, PCT2, pend=True, src='ENVIPE 2025: Guanajuato 3er lugar nacional en percepción de inseguridad (88.5%); ENSU 3T-26 ciudad de Guanajuato 59.5% (no verificado).')
row_f('csrp', 'CSRP total', f'=SUM({R["csrp1"]}:{R["csrp5"]})', PCT2, bold=True)
row_f('ke', 'Ke = Rf local + βL × ERP total + prima tamaño + CSRP', f'={R["rf"]}+{R["bl"]}*{R["erp"]}+{R["size"]}+{R["csrp"]}', PCT2, bold=True, fill=F_KEY)
row_in('d_fin', 'Deuda financiera objetivo / (D+E)', 0.0, PCT, src='All-equity: sin deuda financiera. Por eso no se presenta APV como método separado (no hay escudo fiscal que valuar).')
row_in('kd', 'Kd antes de impuestos (si hubiera deuda)', 0.125, PCT2, pend=True, src='TIIE 28d + ~5.5pp spread PyME. Irrelevante con deuda = 0.')
row_f('wacc', 'WACC = Ke·E/V + Kd·(1−t)·D/V', f'={R["ke"]}*(1-{R["d_fin"]})+{R["kd"]}*(1-{R["isr"]})*{R["d_fin"]}', PCT2, bold=True, fill=F_KEY,
      src='← Tasa de descuento del FCF pre-IFRS16 (la renta es costo operativo).')
W(S, f'A{r}', 'Cross-check en USD (Fisher) — no se usa en el cálculo, valida que el enfoque local no esté sesgado', bold=True); r += 1
row_in('ust', 'UST 10 años', 0.0486, PCT2, src='FRED DGS10 / Advisor Perspectives, 06-nov-2026.', status='Verificado (2 fuentes)')
row_in('inf_mx', 'Inflación esperada largo plazo México', 0.035, PCT2, pend=True, src='Meta Banxico 3% ±1; INPC oct-2026 3.75%; encuesta Banxico cierre-2026 3.88%. Expectativa 5–8a no verificada → 3.5%.')
row_in('inf_us', 'Inflación esperada largo plazo EUA (breakeven 10a)', 0.0227, PCT2, src='FRED T10YIE, 06-nov-2026.', status='Fuente secundaria — verificar')
row_f('ke_usd', 'Ke USD = UST + βL × (ERP maduro + CRP) + tamaño + CSRP', f'={R["ust"]}+{R["bl"]}*({R["erp_m"]}+{R["crp"]})+{R["size"]}+{R["csrp"]}', PCT2)
row_f('ke_fisher', 'Ke USD convertido a MXN = (1+Ke$)·(1+πMX)/(1+πUS) − 1', f'=(1+{R["ke_usd"]})*(1+{R["inf_mx"]})/(1+{R["inf_us"]})-1', PCT2)
row_f('ke_gap', 'Diferencia Ke local − Ke Fisher (pp)', f'={R["ke"]}-{R["ke_fisher"]}', PCT2, src='Debe ser < ±1.5pp (ver Checks).')
row_in('g_real', 'Crecimiento real terminal', 0.0, PCT, src='Restaurante maduro de una unidad: sin crecimiento real perpetuo defendible.')
row_f('g', 'g terminal nominal = (1+π LP)·(1+g real) − 1', f'=(1+{R["inf_mx"]})*(1+{R["g_real"]})-1', PCT2, bold=True)

# ---- C. Ronda y fuentes/usos
section('C. RONDA DE INVERSIÓN — FUENTES Y USOS')
row_in('monto', 'Monto a levantar (equity cash de inversionista)', 7500000, CUR, pend=True, src='No proporcionado en el brief ([PEGAR AQUÍ]). Dimensionado para CapEx + preoperativos + depósito + reserva.')
row_in('cash0', 'Caja existente de la empresa antes de la ronda', 0, CUR, pend=True, src='Data Request #7.')
row_in('debt0', 'Deuda financiera existente', 0, CUR, pend=True, src='Data Request #7.')
row_in('inkind', 'Aportaciones in-kind (si aplican; detalle en Cap Table)', 0, CUR, pend=True, src='El brief dice "si aplican". Si > 0 requiere avalúo independiente.')
W(S, f'A{r}', 'CapEx inicial (usos)', bold=True); W(S, f'B{r}', 'Monto', bold=True); W(S, f'C{r}', 'Vida útil (años)', bold=True); r += 1
cap_rows = []
def capex(key, label, amt, life, src):
    global r
    W(S, f'A{r}', label); W(S, f'B{r}', amt, CUR, kind='input', fill=F_PEND)
    if isinstance(life, str): W(S, f'C{r}', life, '0')
    else: W(S, f'C{r}', life, '0', kind='input')
    W(S, f'G{r}', src, italic=True, color=GREY); W(S, f'H{r}', PEND_TXT, color='C65911', bold=True, fill=F_PEND)
    PENDING.append((label, f'Supuestos!B{r}', src)); cap_rows.append(r); R[key] = f'{SN}$B${r}'; r += 1
term_row_placeholder = None
capex('cx_obra', '  Obra civil y adaptación del local (con lineamientos INAH)', 2000000, 'TERM', 'Benchmark: ~$6.5k/m². Vida = plazo del arrendamiento (mejoras en local arrendado).')
capex('cx_coc', '  Equipo de cocina y barra', 1400000, 5, 'Vida fiscal: LISR art. 35 restaurantes 20% (fuente secundaria) → 5 años.')
capex('cx_mob', '  Mobiliario, decoración e iluminación', 800000, 10, 'LISR art. 34 fr. III: 10% → 10 años.')
capex('cx_ti', '  Cómputo, POS, audio y CCTV', 250000, 3, 'LISR art. 34 fr. VII: 30% → ~3 años.')
capex('cx_lic', '  Licencias y permisos (alcoholes, uso de suelo, PC, INAH)', 350000, 5, 'Licencia de alcoholes en Guanajuato: costo y plazo por validar con el municipio.')
R['cx_range'] = f'{SN}$B${cap_rows[0]}:$B${cap_rows[-1]}'; R['life_range'] = f'{SN}$C${cap_rows[0]}:$C${cap_rows[-1]}'
row_f('capex0', 'Total CapEx inicial', f'=SUM({R["cx_range"]})', CUR, bold=True)
row_in('preop', 'Gastos preoperativos (nómina pre-apertura, capacitación, lanzamiento)', 450000, CUR, pend=True, src='Benchmark ~1.5 meses de nómina + marketing de lanzamiento. Se reconoce como gasto en Año 0 (genera pérdida fiscal amortizable).')
row_in('dep_m', 'Depósito en garantía de renta (meses)', 2, '0', pend=True, src='Práctica de mercado 1–3 meses. Se recupera al término del contrato.')
uses_start = r
row_f('dep_amt', 'Depósito en garantía ($)', '=0', CUR)  # se reescribe tras definir renta
row_f('uses_ex', 'Usos sin reserva = CapEx + preoperativos + depósito', '=0', CUR)
row_f('reserve', 'Reserva de caja operativa (residual de la ronda)', '=0', CUR, bold=True, src='Debe cubrir el covenant mínimo de caja (ver Checks / Resumen).')

# ---- D. Revenue build-up
section('D. REVENUE BUILD-UP (bottom-up): cubiertos/día = asientos × rotación × ocupación')
row_in('seats', 'Asientos', 90, NUM, pend=True, src='Data Request #4 (layout). Típico restaurante de servicio completo en casona del Centro.')
row_in('m2', 'Superficie total (m²)', 300, NUM, pend=True, src='Contrato de arrendamiento / planos.')
row_in('days', 'Días de operación al año', 360, NUM, pend=True, src='Operación 7 días; ~5 cierres (1-ene, Viernes Santo, 25-dic, mantenimiento).')
hdr(S, r, ['Por turno', 'Desayuno', 'Comida', 'Cena', '', 'Unidad', 'Fuente / razón', 'Estatus']); r += 1
def daypart(key, label, vals, fmt, unit, src):
    global r
    W(S, f'A{r}', label)
    for j, v in enumerate(vals): W(S, f'{"BCD"[j]}{r}', v, fmt, kind='input', fill=F_PEND)
    W(S, f'F{r}', unit, color=GREY); W(S, f'G{r}', src, italic=True, color=GREY)
    W(S, f'H{r}', PEND_TXT, color='C65911', bold=True, fill=F_PEND)
    R[key] = [f'{SN}${c}${r}' for c in 'BCD']; PENDING.append((label, f'Supuestos!B{r}:D{r}', src)); r += 1
daypart('turns', 'Rotación (turnos por servicio)', [0.8, 1.2, 1.0], DEC, 'x', 'Benchmark servicio completo: 1.0–1.5 comida, 0.8–1.2 cena. Validar con POS.')
daypart('occ', 'Ocupación promedio de asientos por turno', [0.35, 0.50, 0.45], PCT, '%', 'Supuesto conservador; ocupación hotelera ciudad ~37–60% (OTEG dic-25 / Cervantino-26).')
daypart('tf', 'Ticket promedio alimentos por cubierto (sin IVA)', [150, 260, 300], CUR, 'MXN', 'Menú con costeo pendiente (Data Request #3).')
daypart('tb', 'Ticket promedio bebidas por cubierto (sin IVA)', [50, 110, 170], CUR, 'MXN', 'Mezcla alcohol / no alcohol por validar.')
row_in('deliv', 'Ventas delivery (apps) como % de ventas de alimentos en salón', 0.06, PCT, pend=True, src='Centro Histórico: demanda turística en sitio → delivery bajo.')
row_in('card', '% de ventas en salón cobradas con tarjeta', 0.75, PCT, pend=True, src='Turismo + estudiantes; validar con cortes de terminal.')
row_in('g_price', 'Incremento anual de precios (ticket)', 0.04, PCT, pend=True, src='INPC oct-2026 3.75%; servicios de alimentación por encima del general.')
row_in('g_r_early', 'Crecimiento real de cubiertos, años 2–3 (maduración)', 0.03, PCT, pend=True, src='Maduración típica post-apertura; 0 si el negocio ya opera.')
row_in('g_r_late', 'Crecimiento real de cubiertos, años 4+', 0.0, PCT, src='Capacidad física del local limita crecimiento real.')
hdr(S, r, ['Mes', 'Índice estacional', 'Ramp-up apertura', '', '', '', 'Razón (estacionalidad Guanajuato capital)', 'Estatus']); r += 1
season = [('Ene', 0.80, 0.55, 'Cuesta de enero; regreso a clases UG (>48k alumnos) a mitad de mes.'),
          ('Feb', 0.85, 0.60, 'Temporada baja.'),
          ('Mar', 1.00, 0.65, 'Puente de marzo; arranque de Semana Santa (fecha móvil).'),
          ('Abr', 1.10, 0.70, 'Semana Santa / Pascua: 71k visitantes en 2025.'),
          ('May', 0.90, 0.75, 'Fin de semestre UG.'),
          ('Jun', 0.85, 0.80, 'Vacaciones UG desde ~12-jun: baja demanda estudiantil.'),
          ('Jul', 1.05, 0.85, 'Vacaciones de verano: turismo nacional.'),
          ('Ago', 1.00, 0.88, 'Verano / regreso a clases UG ~3-ago.'),
          ('Sep', 0.90, 0.91, 'Fiestas patrias; temporada media.'),
          ('Oct', 1.35, 0.94, 'Festival Internacional Cervantino: >386k asistentes y $519.9M de derrama (2026).'),
          ('Nov', 1.10, 0.97, 'Día de Muertos, puente revolucionario; nov-25 ocupación hotelera 53%.'),
          ('Dic', 1.10, 1.00, 'Vacaciones decembrinas; dic-25 ocupación 37% pero alta afluencia local fin de año.')]
s0 = r
for m, si, ru, why in season:
    W(S, f'A{r}', m); W(S, f'B{r}', si, DEC, kind='input', fill=F_PEND); W(S, f'C{r}', ru, PCT, kind='input', fill=F_PEND)
    W(S, f'G{r}', why, italic=True, color=GREY); W(S, f'H{r}', PEND_TXT, color='C65911', bold=True, fill=F_PEND); r += 1
R['season'] = f'{SN}$B${s0}:$B${r-1}'; R['ramp'] = f'{SN}$C${s0}:$C${r-1}'
PENDING.append(('Índices de estacionalidad mensual y curva de ramp-up', f'Supuestos!B{s0}:C{r-1}', 'Serie mensual OTEG de ocupación hotelera no accesible; reemplazar con ventas POS.'))
row_f('season_avg', 'Promedio de índices estacionales (se normaliza a 1.0 en el modelo)', f'=AVERAGE({R["season"]})', DEC)

# ---- E. Costos
section('E. ESTRUCTURA DE COSTOS')
row_in('fc', 'Food cost (% de ventas de alimentos)', 0.32, PCT, pend=True, src='Benchmark México 28–35% (calculadora atribuida a CANIRAC, no verificada); EUA servicio completo 28–35%.')
row_in('bc', 'Beverage cost (% de ventas de bebidas, IEPS incluido en costo)', 0.25, PCT, pend=True,
       src='IEPS (LIEPS art. 2-I-A: ≤14°GL 26.5%, 14–20°GL 30%, >20°GL 53%) lo causa productor/importador; el restaurante no lo acredita → es costo.')
W(S, f'A{r}', 'Plantilla (nómina bruta mensual por puesto)', bold=True); W(S, f'B{r}', 'Plazas', bold=True); W(S, f'C{r}', 'Sueldo mensual', bold=True); r += 1
staff = [('Gerente general', 1, 28000), ('Chef ejecutivo', 1, 30000), ('Cocineros de línea', 4, 13000), ('Ayudantes de cocina', 4, 10000),
         ('Lavaloza / limpieza', 3, 9600), ('Meseros (sueldo base; propinas fuera de nómina)', 8, 9600), ('Bartender', 2, 11000), ('Hostess / caja', 2, 10000)]
st0 = r
for p, h, s in staff:
    W(S, f'A{r}', '  ' + p); W(S, f'B{r}', h, NUM, kind='input', fill=F_PEND); W(S, f'C{r}', s, CUR, kind='input', fill=F_PEND)
    W(S, f'H{r}', PEND_TXT, color='C65911', bold=True, fill=F_PEND); r += 1
PENDING.append(('Plantilla y sueldos', f'Supuestos!B{st0}:C{r-1}', 'Salario mínimo 2026 $315.04/día (+13%, CONASAMI) ≈ $9,577/mes: piso de sueldos.'))
R['heads'] = f'{SN}$B${st0}:$B${r-1}'; R['sal'] = f'{SN}$C${st0}:$C${r-1}'
row_f('headcount', 'Plantilla total (personas)', f'=SUM({R["heads"]})', NUM)
row_f('nomina', 'Nómina bruta anual base (Año 1)', f'=SUMPRODUCT({R["heads"]},{R["sal"]})*12', CUR)
row_in('agu', 'Aguinaldo (días)', 15, '0', src='LFT art. 87.', status='Verificado (ley)')
row_in('vac', 'Vacaciones primer año (días)', 12, '0', src='LFT reforma DOF 27-dic-2022, vigente 2023.', status='Verificado (ley)')
row_in('pvac', 'Prima vacacional', 0.25, PCT, src='LFT art. 80.', status='Verificado (ley)')
row_f('integ', 'Factor de integración = 1 + aguinaldo/365 + vacaciones × prima/365', f'=1+{R["agu"]}/365+{R["vac"]}*{R["pvac"]}/365', DEC4)
row_in('ss', 'Cuotas patronales IMSS + SAR (2%) + INFONAVIT (5%) sobre salario integrado', 0.275, PCT, pend=True, src='Rango 25–30% para salarios bajos (Praxium 2026, fuente secundaria). Confirmar con cálculo SUA de la plantilla real.')
row_in('isn', 'Impuesto sobre Nómina — Estado de Guanajuato', 0.03, PCT, src='Ley de Hacienda del Estado de Guanajuato, 3% sin cambio para 2026 (2 fuentes).', status='Verificado (2 fuentes)')
row_f('carga', 'Factor de costo laboral total = integración × (1 + cuotas + ISN)', f'={R["integ"]}*(1+{R["ss"]}+{R["isn"]})', DEC4, bold=True)
row_in('wage_g', 'Incremento salarial anual', 0.06, PCT, pend=True, src='Salario mínimo +13% en 2026; se asume convergencia a ~6% nominal (presión sobre margen vs precios +4%).')
row_in('rent_m', 'Renta mensual (sin IVA)', 120000, CUR, pend=True, src='Contrato de arrendamiento (Data Request #5). ~$400/m² en Centro Histórico (por validar).')
row_in('rent_esc', 'Incremento anual de renta', 0.04, PCT, pend=True, src='Cláusula típica: INPC anual.')
row_in('term', 'Plazo remanente del arrendamiento (años, ≤ 10 por horizonte del modelo)', 10, '0', pend=True, src='Contrato de arrendamiento.')
row_in('renew', 'Años de renovación probable al vencimiento', 5, '0', pend=True, src='Opción de renovación en contrato (si existe).')
row_in('ibr', 'Tasa incremental de financiamiento (NIF D-5 / IFRS 16)', 0.12, PCT2, pend=True, src='TIIE + spread PyME garantizado; usada sólo para el pasivo por arrendamiento.')
row_in('fee', 'Comisión terminal bancaria (% de ventas con tarjeta)', 0.018, PCT2, pend=True, src='TPV bancaria 0.65–0.70% + IVA; agregadores (Clip 3.6%, MP 3.5%). Mezcla supuesta 1.8%.')
row_in('dcomm', 'Comisión apps de delivery (% de venta delivery)', 0.27, PCT, pend=True, src='Rappi ~23%, Uber Eats / DiDi ~30% (+IVA acreditable).')
row_in('roy', 'Regalías / franquicia (% de ventas)', 0.0, PCT, src='Restaurante independiente: no aplica. Capturar si es franquicia.')
row_in('o_util', 'Energía, gas y agua (% ventas)', 0.045, PCT, pend=True, src='Benchmark industria 3–5%.')
row_in('o_mkt', 'Marketing (% ventas)', 0.02, PCT, pend=True, src='Benchmark 1–3%.')
row_in('o_mant', 'Mantenimiento y reparaciones (% ventas)', 0.015, PCT, pend=True, src='Benchmark 1–2%; casona histórica puede requerir más.')
row_in('o_sup', 'Desechables, limpieza y blancos (% ventas)', 0.015, PCT, pend=True, src='Benchmark.')
row_in('o_oth', 'Otros variables (% ventas)', 0.01, PCT, pend=True, src='Música, flores, mermas no capturadas.')
row_in('admin_m', 'Gastos fijos administrativos mensuales (contador, legal, software, seguros, seguridad)', 45000, CUR, pend=True, src='Cotizaciones por validar.')
row_in('ovh_m', 'Overhead fuera del restaurante (dirección / socio administrador) mensual', 25000, CUR, pend=True, src='Separa EBITDA 4-wall de EBITDA empresa.')

# ---- F. CapEx recurrente y capital de trabajo
section('F. CAPEX RECURRENTE, D&A Y CAPITAL DE TRABAJO (días, no % genérico)')
row_in('mx_pct', 'CapEx de mantenimiento (% ventas)', 0.02, PCT, pend=True, src='Benchmark industria 1.5–3%.')
row_in('mx_life', 'Vida útil CapEx de mantenimiento (años)', 5, '0', src='Mezcla equipo / mobiliario.')
row_in('rf_n', 'Refresh (remodelación) cada N años', 6, '0', pend=True, src='Brief: refresh cada 5–7 años.')
row_in('rf_pct', 'Refresh: % del CapEx inicial (indexado a inflación)', 0.35, PCT, pend=True, src='Remodelación parcial: mobiliario, imagen, equipo.')
row_in('rf_life', 'Vida útil del refresh (años)', 5, '0', src='')
row_in('inv_d', 'Días de inventario (sobre costo de alimentos y bebidas)', 7, '0', pend=True, src='Perecederos; vinos y licores elevan el promedio.')
row_in('ar_card', 'Días de cobro tarjeta', 2, '0', pend=True, src='Liquidación bancaria T+1/T+2.')
row_in('ar_del', 'Días de cobro apps de delivery', 7, '0', pend=True, src='Liquidación semanal típica.')
row_in('ap_d', 'Días de pago a proveedores (costo F&B + gastos variables)', 30, '0', pend=True, src='Crédito de proveedores 15–45 días → capital de trabajo negativo.')
row_in('ptu', 'PTU', 0.10, PCT, src='LFT art. 117 / LISR art. 9.', status='Verificado (ley)')
row_in('ptu_cap', 'Tope PTU (meses de salario)', 3, '0', src='LFT art. 127 fr. VIII (reforma 2021): máx. 3 meses o promedio 3 años.', status='Verificado (ley)')
row_in('iva', 'IVA (informativo: ventas modeladas sin IVA)', 0.16, PCT, src='LIVA art. 1. Neutro en flujo (acreditable).', status='Verificado (ley)')

# ---- G. Escenarios
section('G. ESCENARIOS (el Resumen calcula los 4 en paralelo)')
hdr(S, r, ['Driver', 'Optimista', 'Base ★', 'Conservador', 'Estrés', '', 'Razón', '']); r += 1
def scen(key, label, vals, fmt, why, pend=False):
    global r
    W(S, f'A{r}', label)
    for j, v in enumerate(vals):
        W(S, f'{"BCDE"[j]}{r}', v, fmt, kind='input' if not (isinstance(v, str) and v.startswith('=')) else None, fill=F_PEND if pend else None)
    W(S, f'G{r}', why, italic=True, color=GREY)
    if pend: W(S, f'H{r}', PEND_TXT, color='C65911', bold=True, fill=F_PEND)
    R[key] = f'{SN}$B${r}:$E${r}'; r += 1
scen('f_cov', 'Factor de cubiertos (ocupación)', [1.10, 1.00, 0.90, 0.75], DEC, 'Estrés del brief: −25% cubiertos.', True)
scen('f_tk', 'Factor de ticket', [1.05, 1.00, 0.95, 1.00], DEC, 'Poder de precio vs. sensibilidad estudiantil.', True)
scen('f_fc', 'Ajuste relativo a food & beverage cost', [-0.05, 0.0, 0.05, 0.15], PCT, 'Estrés del brief: +15% food cost (relativo: 32% → 36.8%).', True)
scen('f_w', 'Ajuste a WACC (pp)', [-0.01, 0.0, 0.015, 0.0], PCT, 'Estrés es operativo: WACC sin cambio para aislar efecto.')
scen('f_g', 'Ajuste a g terminal (pp)', [0.005, 0.0, -0.01, 0.0], PCT, '')
scen('prob', 'Probabilidad de renovación del arrendamiento', [0.80, 0.60, 0.40, 0.60], PCT, 'Depende de cláusula de renovación y relación con el arrendador.', True)
scen('mult', 'Múltiplo EV/EBITDA (post-IFRS16) de referencia', ['=Comparables!$C$22', '=Comparables!$C$23', '=Comparables!$C$24', '=Comparables!$C$23'], MULT, 'Ver hoja Comparables, bloque B.')
scen('size_d', 'Descuento por tamaño sobre el múltiplo', [0.30, 0.40, 0.50, 0.40], PCT, 'Officer (2007) descuento de 15–30% en adquisiciones de privadas vs. públicas; unidad única ⇒ extremo alto.', True)
scen('dlom', 'DLOM (sobre equity)', [0.20, 0.25, 0.30, 0.25], PCT, 'Restricted stock: SEC IIS media 26%; Stout/FMV 13% (pagan dividendos) – 22% (no pagan); pre-IPO Emory ~44–48% sobreestima. Base 25%.', True)
scen('irr', 'TIR objetivo inversionista (VC Method)', [0.30, 0.35, 0.40, 0.35], PCT, 'PE/VC México para negocio de una unidad: 30–40%.', True)
R['scen_row0'] = r
row_in('vc_n', 'Horizonte de salida VC Method (años)', 5, '0', src='Salida al año 5 (antes del refresh del año 6).')
row_in('cov_m', 'Covenant de caja mínima (meses de costos fijos)', 2, '0', pend=True, src='Covenant propuesto para el acuerdo de inversión.')
section('H. PONDERACIÓN DE MÉTODOS (justificación en Resumen)')
row_in('w_dcf', 'DCF (vida finita) ★', 0.50, PCT, src='Único método que captura ramp-up, estructura de costos, capital de trabajo negativo y vida del local.')
row_in('w_cmp', 'Comparables EV/EBITDA', 0.30, PCT, src='Ancla de mercado, pero comparables son cadenas con escala; ajustados por tamaño y DLOM.')
row_in('w_vc', 'VC Method', 0.20, PCT, src='Refleja el precio que pagaría un inversionista financiero; sensible al múltiplo de salida.')
row_in('w_perp', 'Perpetuidad', 0.0, PCT, src='Versión simplificada del DCF que ignora el fin del arrendamiento → sólo cross-check (0%).')
row_f('w_sum', 'Suma de ponderaciones', f'=SUM({R["w_dcf"]}:{R["w_perp"]})', PCT)

# ---- D. Comparables (inputs)
section('I. MÚLTIPLOS COMPARABLES — INPUTS (EV incluye pasivo por arrendamiento; EBITDA post-IFRS16)')
hdr(S, r, ['Empresa / transacción', 'EV/EBITDA LTM', 'Set', 'Fecha', '', '', 'Fuente', 'Estatus']); r += 1
comps = [('Alsea (ALSEA*) — México', 5.0, 'MX', 'jul–oct 2026', 'Multiples.vc 4.2x (19-jul-26); otras fuentes 4.7–5.8x → punto medio 5.0x. ND/EBITDA 2.5x 3T-26.', 'NO VERIFICADO'),
         ('CMR (CMRB) — México', None, 'MX', '3T-26', 'EBITDA 3T-26 $195.7M (margen 18.9%) BMV; capitalización no obtenida.', 'NO VERIFICADO — N/D'),
         ('Grupo Gigante / Toks (GIGANTE*) — México', None, 'EXCL', '2026', 'Conglomerado (Office Depot, Petco, inmobiliario): no es comparable limpio. Excluido.', 'Excluido'),
         ('Arcos Dorados (ARCO) — LatAm', None, 'MX', '2T-26', 'Deuda neta fin. $692M (1.1x); resultados 3T-26 el 12-nov-26. Múltiplo no obtenido.', 'NO VERIFICADO — N/D'),
         ('Darden (DRI) — EUA', 14.3, 'US', '06-nov-26', 'Fox Business; rango 13.2–16.6x entre fuentes.', 'Fuente secundaria'),
         ('Texas Roadhouse (TXRH) — EUA', 17.2, 'US', 'jun-26', 'Rango 16.5–18.9x entre fuentes.', 'Fuente secundaria'),
         ('Restaurant Brands Intl (QSR) — EUA', None, 'US', '3T-26', 'Deuda neta $12,614M; EBITDA aj. 9M-26 $2,345M; EV no obtenido.', 'NO VERIFICADO — N/D'),
         ('Damodaran Restaurant/Dining EUA (64 firmas, industria)', 17.49, 'IND', 'ene-26', 'vebitda.html (EBITDA positivo). Referencia, no entra a la mediana.', 'Fuente secundaria'),
         ('Transacción: La Casa de Toño ← Grupo Gigante (2026, no cerrada)', 8.0, 'TX', 'ago-26', 'Bloomberg (fuentes anónimas): ">8x EBITDA ajustado", ~US$400M. Sin acuerdo vinculante.', 'NO VERIFICADO'),
         ('Transacción: Vips México ← Alsea (2014)', 8.5, 'TX', '2014', 'Cálculo: $8,200M / EBITDA 2012 $963M. Antigüedad > 5 años.', 'Cálculo propio')]
c0 = r
for nm, m, sset, fecha, src, stt in comps:
    W(S, f'A{r}', nm)
    if m is not None: W(S, f'B{r}', m, MULT, kind='input')
    else: W(S, f'B{r}', 'N/D', color=GREY)
    W(S, f'C{r}', sset, kind='input', align='center'); W(S, f'D{r}', fecha, color=GREY)
    W(S, f'G{r}', src, italic=True, color=GREY); W(S, f'H{r}', stt, color='C65911' if 'VERIF' in stt else GREY, bold='VERIF' in stt); r += 1
R['comp_mult'] = f'{SN}$B${c0}:$B${r-1}'; R['comp_set'] = f'{SN}$C${c0}:$C${r-1}'; R['comp_c0'] = c0; R['comp_c1'] = r - 1
W(S, f'A{r}', 'Sets: MX = México/LatAm cotizada · US = EUA cotizada (sólo referencia de escala) · TX = transacción precedente · IND = industria · EXCL = excluido.', italic=True, color=GREY, size=8); r += 1

# Rellenar fórmulas que dependían de renta
def setf(key, formula):
    a = R[key].split('!')[1].replace('$', '')
    S[a].value = formula
setf('dep_amt', f'={R["dep_m"]}*{R["rent_m"]}')
setf('uses_ex', f'={R["capex0"]}+{R["preop"]}+{R["dep_amt"]}')
setf('reserve', f'={R["monto"]}+{R["cash0"]}-IF({R["gf"]}=1,{R["uses_ex"]},0)')
# vida de obra = plazo del arrendamiento
S[f'C{cap_rows[0]}'].value = f'=MIN(10,{R["term"]})'; S[f'C{cap_rows[0]}'].font = Font(name=FONT, color=BLACK)
S.freeze_panes = 'B5'

def SC(key, scen_ref):
    return f'INDEX({R[key]},1,{scen_ref})'

# ======================================================================================
# 2. MOTOR (P&L, NIF D-5, CapEx, CT, FCF, mensual)
# ======================================================================================
def engine(ws, r0, scen_ref, label):
    """Escribe el motor completo a partir de la fila r0. Devuelve dict de filas."""
    P = q(ws.title)
    rows = {}
    rr = [r0]
    def line(key, lab, fn, fmt=CUR, y0=None, bold=False, fill=None, years=True):
        rw = rr[0]
        W(ws, f'A{rw}', lab, bold=bold, fill=fill)
        if y0 is not None: W(ws, f'B{rw}', y0, fmt, bold=bold, fill=fill)
        if years:
            for t in range(1, N + 1):
                c, p = YC[t], YC[t - 1]
                W(ws, f'{c}{rw}', fn(c, p, t, rw), fmt, bold=bold, fill=fill)
        rows[key] = rw; rr[0] += 1
        return rw
    def gap(): rr[0] += 1
    def subsec(t):
        sec(ws, rr[0], t, 13); rr[0] += 1
    # encabezado
    hdr(ws, rr[0], ['Concepto ($MXN)', 'Año 0'] + [''] * N + ['Total / nota'])
    for t in range(1, N + 1):
        W(ws, f'{YC[t]}{rr[0]}', f'=TEXT({R["base_year"]}+{t},"0")', bold=True, color=WHITE, fill=F_HDR, align='center')
    W(ws, f'B{rr[0]}', f'=TEXT({R["base_year"]},"0")', bold=True, color=WHITE, fill=F_HDR, align='center')
    rows['hdr'] = rr[0]; rr[0] += 1
    W(ws, f'A{rr[0]}', 'Escenario de este bloque'); W(ws, f'B{rr[0]}', scen_ref if scen_ref.startswith('=') else f'={scen_ref}', '0')
    W(ws, f'C{rr[0]}', f'=CHOOSE(B{rr[0]},"Optimista","Base ★","Conservador","Estrés")', bold=True)
    rows['scen'] = rr[0]; SCN = f'$B${rr[0]}'; rr[0] += 1
    sc = lambda k: SC(k, SCN)
    line('t', 'Año de proyección (t)', lambda c, p, t, rw: f'={p}{rw}+1', '0', y0=0)
    T = lambda c: f'{c}${rows["t"]}'
    subsec('A. REVENUE BUILD-UP')
    line('ramp', 'Factor ramp-up (año 1 = Σ estacionalidad × ramp / Σ estacionalidad)',
         lambda c, p, t, rw: f'=IF(AND({T(c)}=1,{R["gf"]}=1),SUMPRODUCT({R["season"]},{R["ramp"]})/SUM({R["season"]}),1)', PCT)
    line('greal', 'Índice de cubiertos por crecimiento real',
         lambda c, p, t, rw: f'=IF({T(c)}=1,1,{p}{rw}*(1+IF({T(c)}<=3,{R["g_r_early"]},{R["g_r_late"]})))', DEC4)
    line('pidx', 'Índice de precios', lambda c, p, t, rw: f'=(1+{R["g_price"]})^({T(c)}-1)', DEC4)
    for j, dp in enumerate(['desayuno', 'comida', 'cena']):
        line(f'cov{j}', f'Cubiertos/día — {dp} (asientos × rotación × ocupación × factor)',
             lambda c, p, t, rw, j=j: f'={R["seats"]}*{R["turns"][j]}*{R["occ"][j]}*{sc("f_cov")}', NUM1)
    line('covday', 'Cubiertos/día totales (régimen, antes de ramp-up)', lambda c, p, t, rw: f'=SUM({c}{rows["cov0"]}:{c}{rows["cov2"]})', NUM1, bold=True)
    line('covyr', 'Cubiertos/año', lambda c, p, t, rw: f'={c}{rows["covday"]}*{R["days"]}*{c}{rows["ramp"]}*{c}{rows["greal"]}', NUM)
    vol = lambda c: f'{R["days"]}*{c}{rows["ramp"]}*{c}{rows["greal"]}*{c}{rows["pidx"]}*{sc("f_tk")}'
    line('rf_food', 'Ventas alimentos salón', lambda c, p, t, rw: '=(' + '+'.join(f'{c}{rows[f"cov{j}"]}*{R["tf"][j]}' for j in range(3)) + f')*{vol(c)}', y0=None)
    line('rf_bev', 'Ventas bebidas salón', lambda c, p, t, rw: '=(' + '+'.join(f'{c}{rows[f"cov{j}"]}*{R["tb"][j]}' for j in range(3)) + f')*{vol(c)}')
    line('rf_del', 'Ventas delivery (apps)', lambda c, p, t, rw: f'={c}{rows["rf_food"]}*{R["deliv"]}')
    line('rev', 'VENTAS NETAS (sin IVA, sin propinas)', lambda c, p, t, rw: f'=SUM({c}{rows["rf_food"]}:{c}{rows["rf_del"]})', bold=True, fill=F_KEY)
    line('ticket', 'Ticket promedio salón por cubierto', lambda c, p, t, rw: f'=IFERROR(({c}{rows["rf_food"]}+{c}{rows["rf_bev"]})/{c}{rows["covyr"]},0)')
    line('mixbev', 'Mix bebidas / ventas salón', lambda c, p, t, rw: f'=IFERROR({c}{rows["rf_bev"]}/({c}{rows["rf_food"]}+{c}{rows["rf_bev"]}),0)', PCT)
    subsec('B. ESTADO DE RESULTADOS — PRE-IFRS 16 (renta como gasto operativo)')
    line('c_food', '(−) Costo de alimentos (salón + delivery)', lambda c, p, t, rw: f'=({c}{rows["rf_food"]}+{c}{rows["rf_del"]})*{R["fc"]}*(1+{sc("f_fc")})')
    line('c_bev', '(−) Costo de bebidas (incluye IEPS no acreditable)', lambda c, p, t, rw: f'={c}{rows["rf_bev"]}*{R["bc"]}*(1+{sc("f_fc")})')
    line('gp', 'Utilidad bruta', lambda c, p, t, rw: f'={c}{rows["rev"]}-{c}{rows["c_food"]}-{c}{rows["c_bev"]}', bold=True)
    line('gpm', '  Margen bruto %', lambda c, p, t, rw: f'=IFERROR({c}{rows["gp"]}/{c}{rows["rev"]},0)', PCT)
    line('labor', '(−) Nómina total (IMSS, INFONAVIT, SAR, ISN, aguinaldo, prima vacacional)', lambda c, p, t, rw: f'={R["nomina"]}*{R["carga"]}*(1+{R["wage_g"]})^({T(c)}-1)')
    line('prime', 'Prime cost (F&B + nómina)', lambda c, p, t, rw: f'={c}{rows["c_food"]}+{c}{rows["c_bev"]}+{c}{rows["labor"]}')
    line('primep', '  Prime cost % (meta < 60–65%)', lambda c, p, t, rw: f'=IFERROR({c}{rows["prime"]}/{c}{rows["rev"]},0)', PCT, bold=True)
    line('rent', '(−) Renta', lambda c, p, t, rw: f'={R["rent_m"]}*12*(1+{R["rent_esc"]})^({T(c)}-1)')
    line('x_fee', '(−) Comisiones terminal bancaria', lambda c, p, t, rw: f'=({c}{rows["rf_food"]}+{c}{rows["rf_bev"]})*{R["card"]}*{R["fee"]}')
    line('x_del', '(−) Comisiones apps de delivery', lambda c, p, t, rw: f'={c}{rows["rf_del"]}*{R["dcomm"]}')
    line('x_roy', '(−) Regalías / franquicia', lambda c, p, t, rw: f'={c}{rows["rev"]}*{R["roy"]}')
    for k, lab in [('o_util', 'Energía, gas y agua'), ('o_mkt', 'Marketing'), ('o_mant', 'Mantenimiento'), ('o_sup', 'Desechables y limpieza'), ('o_oth', 'Otros variables')]:
        line(k, f'(−) {lab}', lambda c, p, t, rw, k=k: f'={c}{rows["rev"]}*{R[k]}')
    line('admin', '(−) Gastos fijos administrativos', lambda c, p, t, rw: f'={R["admin_m"]}*12*{c}{rows["pidx"]}')
    line('ebitda4', 'EBITDA 4-WALL (pre-IFRS 16)', lambda c, p, t, rw: f'={c}{rows["gp"]}-{c}{rows["labor"]}-SUM({c}{rows["rent"]}:{c}{rows["admin"]})', bold=True, fill=F_KEY)
    line('ebitda4m', '  Margen EBITDA 4-wall %', lambda c, p, t, rw: f'=IFERROR({c}{rows["ebitda4"]}/{c}{rows["rev"]},0)', PCT)
    line('ovh', '(−) Overhead fuera del restaurante', lambda c, p, t, rw: f'={R["ovh_m"]}*12*{c}{rows["pidx"]}')
    line('preop', '(−) Gastos preoperativos', lambda c, p, t, rw: '=0', y0=f'=IF({R["gf"]}=1,{R["preop"]},0)')
    line('ebitda', 'EBITDA EMPRESA (pre-IFRS 16)', lambda c, p, t, rw: f'={c}{rows["ebitda4"]}-{c}{rows["ovh"]}-{c}{rows["preop"]}',
         y0=None, bold=True, fill=F_KEY)
    ws[f'B{rows["ebitda"]}'] = f'=-B{rows["preop"]}'; ws[f'B{rows["ebitda"]}'].number_format = CUR; ws[f'B{rows["ebitda"]}'].font = Font(name=FONT, bold=True)
    line('ebitdam', '  Margen EBITDA empresa %', lambda c, p, t, rw: f'=IFERROR({c}{rows["ebitda"]}/{c}{rows["rev"]},0)', PCT)
    subsec('C. CAPEX Y D&A (D&A material: no aplica "EBITDA ≈ EBIT")')
    line('cx0', 'CapEx inicial', lambda c, p, t, rw: '=0', y0=f'=IF({R["gf"]}=1,{R["capex0"]},0)')
    line('cxm', 'CapEx de mantenimiento', lambda c, p, t, rw: f'={c}{rows["rev"]}*{R["mx_pct"]}', y0=0)
    line('cxr', 'CapEx refresh (remodelación)', lambda c, p, t, rw: f'=IF(MOD({T(c)},{R["rf_n"]})=0,{R["rf_pct"]}*{R["capex0"]}*{c}{rows["pidx"]},0)', y0=0)
    line('da0', 'D&A CapEx inicial (línea recta por categoría)', lambda c, p, t, rw: f'=SUMPRODUCT({R["cx_range"]}/{R["life_range"]}*({R["life_range"]}>={T(c)}))')
    tr = f'$C${rows["t"]}:$L${rows["t"]}'
    line('dam', 'D&A CapEx de mantenimiento', lambda c, p, t, rw: f'=SUMPRODUCT(({tr}<={T(c)})*({tr}>{T(c)}-{R["mx_life"]})*$C${rows["cxm"]}:$L${rows["cxm"]})/{R["mx_life"]}')
    line('dar', 'D&A refresh', lambda c, p, t, rw: f'=SUMPRODUCT(({tr}<={T(c)})*({tr}>{T(c)}-{R["rf_life"]})*$C${rows["cxr"]}:$L${rows["cxr"]})/{R["rf_life"]}')
    line('da', 'D&A total', lambda c, p, t, rw: f'=SUM({c}{rows["da0"]}:{c}{rows["dar"]})', bold=True, y0=0)
    line('ebit', 'EBIT (pre-IFRS 16)', lambda c, p, t, rw: f'={c}{rows["ebitda"]}-{c}{rows["da"]}', bold=True, y0=f'=B{rows["ebitda"]}-B{rr[0]-1}')
    line('ptu', '(−) PTU 10% (tope 3 meses de salario, LFT 127)', lambda c, p, t, rw: f'=MIN({R["ptu"]}*MAX(0,{c}{rows["ebit"]}),{R["nomina"]}*(1+{R["wage_g"]})^({T(c)}-1)*{R["ptu_cap"]}/12)', y0=0)
    line('ebt', 'Utilidad antes de ISR', lambda c, p, t, rw: f'={c}{rows["ebit"]}-{c}{rows["ptu"]}', y0=f'=B{rows["ebit"]}-B{rr[0]-1}')
    line('nol_o', 'Pérdidas fiscales por amortizar — inicio', lambda c, p, t, rw: f'={p}{rw+1}', y0=0)
    line('nol_c', 'Pérdidas fiscales por amortizar — cierre (LISR art. 57)',
         lambda c, p, t, rw: f'=MAX(0,{c}{rows["nol_o"]}-MAX(0,{c}{rows["ebt"]}))+MAX(0,-{c}{rows["ebt"]})',
         y0=f'=MAX(0,B{rows["nol_o"]}-MAX(0,B{rows["ebt"]}))+MAX(0,-B{rows["ebt"]})')
    line('isr', '(−) ISR 30% (después de amortizar pérdidas)', lambda c, p, t, rw: f'=MAX(0,{c}{rows["ebt"]}-{c}{rows["nol_o"]})*{R["isr"]}', y0=0)
    line('nopat', 'NOPAT (utilidad operativa después de PTU e ISR, sin deuda)', lambda c, p, t, rw: f'={c}{rows["ebt"]}-{c}{rows["isr"]}', bold=True,
         y0=f'=B{rows["ebt"]}-B{rr[0]-1}')
    subsec('D. CAPITAL DE TRABAJO (días) — típicamente NEGATIVO en restaurantes')
    line('inv', 'Inventario', lambda c, p, t, rw: f'=({c}{rows["c_food"]}+{c}{rows["c_bev"]})/365*{R["inv_d"]}', y0=0)
    line('ar', 'Cuentas por cobrar (tarjeta + apps)', lambda c, p, t, rw: f'=(({c}{rows["rf_food"]}+{c}{rows["rf_bev"]})*{R["card"]}*{R["ar_card"]}+{c}{rows["rf_del"]}*{R["ar_del"]})/365', y0=0)
    line('ap', 'Proveedores', lambda c, p, t, rw: f'=({c}{rows["c_food"]}+{c}{rows["c_bev"]}+SUM({c}{rows["o_util"]}:{c}{rows["o_oth"]}))/365*{R["ap_d"]}', y0=0)
    line('nwc', 'Capital de trabajo neto', lambda c, p, t, rw: f'={c}{rows["inv"]}+{c}{rows["ar"]}-{c}{rows["ap"]}', bold=True, y0=0)
    line('dnwc', 'Δ Capital de trabajo (+ = uso de caja)', lambda c, p, t, rw: f'={c}{rows["nwc"]}-{p}{rows["nwc"]}', y0=0)
    subsec('E. FREE CASH FLOW DEL PROYECTO (no apalancado, pre-IFRS 16)')
    line('f_nopat', 'NOPAT', lambda c, p, t, rw: f'={c}{rows["nopat"]}', y0=f'=B{rows["nopat"]}')
    line('f_da', '(+) D&A', lambda c, p, t, rw: f'={c}{rows["da"]}', y0=f'=B{rows["da"]}')
    line('f_cx', '(−) CapEx total (inicial + mantenimiento + refresh)', lambda c, p, t, rw: f'={c}{rows["cx0"]}+{c}{rows["cxm"]}+{c}{rows["cxr"]}', y0=f'=B{rows["cx0"]}+B{rows["cxm"]}+B{rows["cxr"]}')
    line('f_nwc', '(−) Δ Capital de trabajo', lambda c, p, t, rw: f'={c}{rows["dnwc"]}', y0=f'=B{rows["dnwc"]}')
    line('f_dep', '(−) Depósito en garantía (+ recuperación al vencer el contrato)', lambda c, p, t, rw: f'=-IF({T(c)}={R["term"]},{R["dep_amt"]},0)',
         y0=f'=IF({R["gf"]}=1,{R["dep_amt"]},0)')
    line('fcf', 'FREE CASH FLOW', lambda c, p, t, rw: f'={c}{rows["f_nopat"]}+{c}{rows["f_da"]}-{c}{rows["f_cx"]}-{c}{rows["f_nwc"]}-{c}{rows["f_dep"]}',
         y0=f'=B{rows["f_nopat"]}+B{rows["f_da"]}-B{rows["f_cx"]}-B{rows["f_nwc"]}-B{rows["f_dep"]}', bold=True, fill=F_KEY)
    line('fcf_cum', 'FCF acumulado (incluye Año 0)', lambda c, p, t, rw: f'={p}{rw}+{c}{rows["fcf"]}', y0=f'=B{rows["fcf"]}')
    subsec('F. VISTA NIF D-5 / IFRS 16 (arrendamiento capitalizado)')
    line('l_rent', 'Pagos de renta dentro del plazo contractual', lambda c, p, t, rw: f'=IF({T(c)}<={R["term"]},{c}{rows["rent"]},0)')
    line('l_int', 'Interés del pasivo por arrendamiento', lambda c, p, t, rw: f'={p}{rw+1}*{R["ibr"]}')
    line('l_bal', 'Pasivo por arrendamiento — saldo final', lambda c, p, t, rw: f'={p}{rw}+{c}{rows["l_int"]}-{c}{rows["l_rent"]}',
         y0=f'=NPV({R["ibr"]},C{rr[0]-2}:L{rr[0]-2})')
    line('l_rou', 'Depreciación del derecho de uso', lambda c, p, t, rw: f'=IF({T(c)}<={R["term"]},$B${rows["l_bal"]}/{R["term"]},0)')
    line('ebitda_post', 'EBITDA POST-IFRS 16 (= pre + renta capitalizada)', lambda c, p, t, rw: f'={c}{rows["ebitda"]}+{c}{rows["l_rent"]}', bold=True, fill=F_KEY)
    line('ebit_post', 'EBIT post-IFRS 16', lambda c, p, t, rw: f'={c}{rows["ebitda_post"]}-{c}{rows["da"]}-{c}{rows["l_rou"]}')
    line('ebt_post', 'Utilidad antes de impuestos post-IFRS 16 (EBIT − interés arrendamiento − PTU)', lambda c, p, t, rw: f'={c}{rows["ebit_post"]}-{c}{rows["l_int"]}-{c}{rows["ptu"]}')
    line('ebt_diff', 'Diferencia vs. pre-IFRS16 (efecto de carga anticipada; suma ≈ 0 en el plazo)', lambda c, p, t, rw: f'={c}{rows["ebt_post"]}-{c}{rows["ebt"]}')
    # ---- mensual año 1
    rr[0] += 1
    sec(ws, rr[0], 'G. FLUJO MENSUAL AÑO 1 — COVENANT DE CAJA (estacionalidad normalizada × ramp-up)', 15); rr[0] += 1
    hdr(ws, rr[0], ['Concepto', 'Apertura'] + [f'Mes {m}' for m in range(1, 13)] + ['Total'])
    rows['m_hdr'] = rr[0]; rr[0] += 1
    MC = [CL(3 + m) for m in range(12)]  # C..N
    def mline(key, lab, fn, fmt=CUR, op=None, tot=True, bold=False):
        rw = rr[0]; W(ws, f'A{rw}', lab, bold=bold)
        if op is not None: W(ws, f'B{rw}', op, fmt, bold=bold)
        for m in range(12):
            W(ws, f'{MC[m]}{rw}', fn(MC[m], CL(2 + m), m, rw), fmt, bold=bold)
        if tot: W(ws, f'O{rw}', f'=SUM(C{rw}:N{rw})', fmt, bold=bold)
        rows[key] = rw; rr[0] += 1
    seas = R['season'].split('!')[1].replace('$', '')
    s_col, s_r0 = 'B', int(seas.split(':')[0][1:])
    rp_r0 = s_r0
    mline('m_si', 'Índice estacional normalizado', lambda c, p, m, rw: f'={SN}$B${s_r0+m}/{R["season_avg"]}', DEC, tot=False)
    mline('m_ru', 'Ramp-up', lambda c, p, m, rw: f'=IF({R["gf"]}=1,{SN}$C${rp_r0+m},1)', PCT, tot=False)
    mline('m_rev', 'Ventas', lambda c, p, m, rw: f'=$C${rows["rev"]}/$C${rows["ramp"]}/12*{c}{rows["m_si"]}*{c}{rows["m_ru"]}')
    var_y1 = f'($C${rows["c_food"]}+$C${rows["c_bev"]}+SUM($C${rows["x_fee"]}:$C${rows["o_oth"]}))/$C${rows["rev"]}'
    mline('m_var', '(−) Costos variables (F&B, comisiones, gastos % ventas)', lambda c, p, m, rw: f'={c}{rows["m_rev"]}*{var_y1}')
    fix_y1 = f'($C${rows["labor"]}+$C${rows["rent"]}+$C${rows["admin"]}+$C${rows["ovh"]})/12'
    mline('m_fix', '(−) Costos fijos (nómina, renta, administración, overhead)', lambda c, p, m, rw: f'={fix_y1}')
    mline('m_ebitda', 'EBITDA mensual', lambda c, p, m, rw: f'={c}{rows["m_rev"]}-{c}{rows["m_var"]}-{c}{rows["m_fix"]}', bold=True)
    mline('m_cx', '(−) CapEx de mantenimiento', lambda c, p, m, rw: f'={c}{rows["m_rev"]}*{R["mx_pct"]}')
    mline('m_cash', 'Caja al cierre del mes (ISR: año 1 cubierto por pérdidas fiscales; CT negativo no se acredita → conservador)',
          lambda c, p, m, rw: f'={p}{rw}+{c}{rows["m_ebitda"]}-{c}{rows["m_cx"]}', op=f'={R["monto"]}+{R["cash0"]}+$B${rows["fcf"]}', tot=False, bold=True)
    rw = rr[0]
    W(ws, f'A{rw}', 'Caja mínima del año 1'); W(ws, f'B{rw}', f'=MIN(B{rows["m_cash"]}:N{rows["m_cash"]})', CUR, bold=True); rows['m_min'] = rw; rw += 1
    W(ws, f'A{rw}', 'Covenant requerido (meses de costo fijo)'); W(ws, f'B{rw}', f'={R["cov_m"]}*C{rows["m_fix"]}', CUR); rows['m_req'] = rw; rw += 1
    W(ws, f'A{rw}', '¿Cumple covenant de caja?'); W(ws, f'B{rw}', f'=B{rows["m_min"]}>=B{rows["m_req"]}', bold=True); rows['m_ok'] = rw; rw += 1
    rr[0] = rw
    rows['end'] = rr[0]
    return rows

def E(eng, key, t):   # referencia a celda del motor
    return f'{eng["P"]}${YC[t]}${eng["rows"][key]}'
def ER(eng, key, t0=1, t1=N):
    return f'{eng["P"]}${YC[t0]}${eng["rows"][key]}:${YC[t1]}${eng["rows"][key]}'

# ======================================================================================
# 3. BLOQUES DE VALUACIÓN reutilizables (mismas fórmulas en hojas de detalle y en Escenarios)
# ======================================================================================
def block_dcf(ws, r0, eng, scen_ref, detail=True):
    P = eng['P']; rows = {}; r_ = r0
    sc = lambda k: SC(k, scen_ref)
    def put(key, lab, f, fmt=CUR, bold=False, fill=None, note=None):
        nonlocal r_
        W(ws, f'A{r_}', lab, bold=bold, fill=fill); W(ws, f'D{r_}', f, fmt, bold=bold, fill=fill)
        if note: W(ws, f'E{r_}', note, italic=True, color=GREY)
        rows[key] = r_; r_ += 1
        return f'$D${rows[key]}'
    w = put('w', 'WACC del escenario', f'={R["wacc"]}+{sc("f_w")}', PCT2)
    g = put('g', 'g terminal del escenario', f'={R["g"]}+{sc("f_g")}', PCT2)
    # tabla de flujos
    hdr(ws, r_, ['Concepto'] + [f'=TEXT({R["base_year"]}+{t},"0")' for t in range(1, N + 1)] + ['Σ'], start=1)
    for t in range(1, N + 1): ws.cell(r_, 1 + t).value = f'=TEXT({R["base_year"]}+{t},"0")'
    rows['th'] = r_; r_ += 1
    W(ws, f'A{r_}', 'FCF'); [W(ws, f'{CL(1+t)}{r_}', f'={E(eng,"fcf",t)}', CUR) for t in range(1, N + 1)]
    W(ws, f'{CL(N+2)}{r_}', f'=SUM(B{r_}:{CL(N+1)}{r_})', CUR); rows['fcf'] = r_; r_ += 1
    W(ws, f'A{r_}', 'Factor de descuento 1/(1+WACC)^(t − 0.5·medio año)')
    [W(ws, f'{CL(1+t)}{r_}', f'=1/(1+{w})^({E(eng,"t",t)}-0.5*{R["mid"]})', DEC4) for t in range(1, N + 1)]; rows['df'] = r_; r_ += 1
    W(ws, f'A{r_}', 'Valor presente del FCF')
    [W(ws, f'{CL(1+t)}{r_}', f'={CL(1+t)}{rows["fcf"]}*{CL(1+t)}{rows["df"]}', CUR) for t in range(1, N + 1)]
    W(ws, f'{CL(N+2)}{r_}', f'=SUM(B{r_}:{CL(N+1)}{r_})', CUR, bold=True); rows['pv'] = r_; r_ += 1
    r_ += 1
    spv = put('spv', 'Σ VP de FCF explícitos (años 1–10)', f'={CL(N+2)}{rows["pv"]}')
    base_ex = put('b_ex', 'FCF normalizado año 10 antes de crecimiento = NOPAT + D&A − CapEx mant. − refresh anualizado',
                  f'={E(eng,"nopat",N)}+{E(eng,"da",N)}-{E(eng,"cxm",N)}-{R["rf_pct"]}*{R["capex0"]}*{E(eng,"pidx",N)}/{R["rf_n"]}')
    f11 = put('f11', 'FCF año 11 = FCF normalizado × (1+g) − capital de trabajo × g', f'={base_ex}*(1+{g})-{E(eng,"nwc",N)}*{g}')
    tvg = put('tvg', '(b) VT Gordon perpetuo = FCF₁₁ / (WACC − g)', f'=IF({w}>{g},{f11}/({w}-{g}),0)')
    n1 = put('n1', 'Años remanentes de contrato después del año 10', f'=MAX(0,{R["term"]}-{N})', '0')
    ann = lambda n: f'{f11}*(1-((1+{g})/(1+{w}))^({n}))/({w}-{g})'
    tvf = put('tvf', '(a) VT vida finita = anualidad creciente del plazo + prob. renovación × anualidad de renovación',
              f'={ann(n1)}+{sc("prob")}*({ann(f"{n1}+{R["renew"]}")}-{ann(n1)})')
    tvs = put('tvs', 'Valor terminal del método base seleccionado', f'=IF({R["tv_method"]}=1,{tvf},{tvg})', bold=True)
    dfn = f'1/(1+{w})^{N}'
    pvtv = put('pvtv', 'VP del valor terminal (descontado al cierre del año 10)', f'={tvs}*{dfn}')
    ev = put('ev', 'ENTERPRISE VALUE — DCF (método base)', f'={spv}+{pvtv}', bold=True, fill=F_KEY)
    evg = put('evg', 'EV con Gordon perpetuo (referencia)', f'={spv}+{tvg}*{dfn}')
    evf = put('evf', 'EV con vida finita (referencia)', f'={spv}+{tvf}*{dfn}')
    ptv = put('ptv', '% del EV que viene del valor terminal', f'=IFERROR({pvtv}/{ev},0)', PCT, bold=True)
    put('ptv_al', 'Alerta: % VT > 70%', f'=IF({ptv}>0.7,"⚠ ALERTA: VT > 70% del EV","OK (≤ 70%)")', None)
    adj = f'{E(eng,"fcf",0)}-{R["debt0"]}+{R["cash0"]}'
    put('adj', '(+) FCF Año 0 (CapEx inicial, preoperativos, depósito) − deuda + caja pre-ronda', f'={adj}')
    pre_m = put('pre_m', 'Equity pre-money (base comercializable, minoritario)', f'={ev}+{adj}')
    pre = put('pre', 'Equity pre-money después de DLOM', f'=IF({pre_m}>0,{pre_m}*(1-{sc("dlom")}),{pre_m})', bold=True, fill=F_KEY)
    preg = put('preg', 'Equity pre-money Gordon (después de DLOM)', f'=IF({evg}+{adj}>0,({evg}+{adj})*(1-{sc("dlom")}),{evg}+{adj})')
    put('post', 'Equity post-money = pre + cash + in-kind', f'={pre}+{R["monto"]}+{R["inkind"]}')
    rows['end'] = r_
    return rows

def block_comps(ws, r0, eng, scen_ref, wref):
    rows = {}; r_ = r0; sc = lambda k: SC(k, scen_ref)
    def put(key, lab, f, fmt=CUR, bold=False, fill=None, note=None):
        nonlocal r_
        W(ws, f'A{r_}', lab, bold=bold, fill=fill); W(ws, f'D{r_}', f, fmt, bold=bold, fill=fill)
        if note: W(ws, f'E{r_}', note, italic=True, color=GREY)
        rows[key] = r_; r_ += 1; return f'$D${r_-1}'
    w = wref
    m = put('m', 'Múltiplo EV/EBITDA de referencia (post-IFRS16)', f'={sc("mult")}', MULT)
    sz = put('sz', 'Descuento por tamaño', f'={sc("size_d")}', PCT)
    me = put('me', 'Múltiplo efectivo = múltiplo × (1 − descuento tamaño)', f'={m}*(1-{sz})', MULT, bold=True)
    eb = put('eb', 'EBITDA post-IFRS16 año 2 (primer año estabilizado; forward al cierre del año 1)', f'={E(eng,"ebitda_post",2)}')
    ev1 = put('ev1', 'EV al cierre del año 1 (incluye pasivo por arrendamiento)', f'={me}*{eb}')
    ll = put('ll', '(−) Pasivo por arrendamiento al cierre del año 1 (definición consistente con el múltiplo)', f'={E(eng,"l_bal",1)}')
    eq1 = put('eq1', 'Equity al cierre del año 1', f'={ev1}-{ll}')
    pv1 = put('pv1', '(+) VP del FCF del año 1 (incluye renta pagada)', f'={E(eng,"fcf",1)}/(1+{w})^(1-0.5*{R["mid"]})')
    put('ev0', 'EV equivalente hoy (pre-IFRS16) = VP equity año 1 + VP FCF año 1', f'={eq1}/(1+{w})+{pv1}', bold=True, fill=F_KEY)
    ev0 = f'$D${r_-1}'
    adj = f'{E(eng,"fcf",0)}-{R["debt0"]}+{R["cash0"]}'
    pre_m = put('pre_m', 'Equity pre-money (comercializable) = EV + FCF año 0 − deuda + caja', f'={ev0}+{adj}')
    put('pre', 'Equity pre-money después de DLOM', f'=IF({pre_m}>0,{pre_m}*(1-{sc("dlom")}),{pre_m})', bold=True, fill=F_KEY)
    put('hair', 'Haircut total vs. múltiplo de mercado = 1 − (1−tamaño)(1−DLOM)', f'=1-(1-{sz})*(1-{sc("dlom")})', PCT)
    rows['end'] = r_; return rows

def block_vc(ws, r0, eng, scen_ref):
    rows = {}; r_ = r0; sc = lambda k: SC(k, scen_ref)
    def put(key, lab, f, fmt=CUR, bold=False, fill=None):
        nonlocal r_
        W(ws, f'A{r_}', lab, bold=bold, fill=fill); W(ws, f'D{r_}', f, fmt, bold=bold, fill=fill)
        rows[key] = r_; r_ += 1; return f'$D${r_-1}'
    n = R['vc_n']
    eb = put('eb', 'EBITDA post-IFRS16 en el año de salida', f'=INDEX({ER(eng,"ebitda_post")},1,{n})')
    mx = put('mx', 'Múltiplo de salida = múltiplo × (1 − descuento tamaño)', f'={SC("mult",scen_ref)}*(1-{SC("size_d",scen_ref)})', MULT)
    evx = put('evx', 'EV de salida', f'={eb}*{mx}')
    llx = put('llx', '(−) Pasivo por arrendamiento en la salida', f'=INDEX({ER(eng,"l_bal")},1,{n})')
    eqx = put('eqx', 'Equity de salida (FCF intermedio se distribuye como dividendo; no se suma → conservador)', f'={evx}-{llx}', bold=True)
    irr = put('irr', 'TIR objetivo del inversionista', f'={sc("irr")}', PCT)
    post = put('post', 'Post-money hoy = Equity salida / (1+TIR)^n (la TIR ya incorpora iliquidez: sin DLOM)', f'={eqx}/(1+{irr})^{n}', bold=True, fill=F_KEY)
    put('pre', 'Pre-money hoy = post − cash − in-kind', f'={post}-{R["monto"]}-{R["inkind"]}', bold=True, fill=F_KEY)
    put('own', 'Participación requerida por el inversionista = cash / post', f'=IF({post}<={R["monto"]},"n.s. (>100%)",{R["monto"]}/{post})', PCT)
    rows['end'] = r_; return rows

def block_perp(ws, r0, eng, scen_ref, wref, gref):
    rows = {}; r_ = r0; sc = lambda k: SC(k, scen_ref)
    def put(key, lab, f, fmt=CUR, bold=False, fill=None):
        nonlocal r_
        W(ws, f'A{r_}', lab, bold=bold, fill=fill); W(ws, f'D{r_}', f, fmt, bold=bold, fill=fill)
        rows[key] = r_; r_ += 1; return f'$D${r_-1}'
    w = wref; g = gref
    b = put('b', 'FCF normalizado año 3 (estabilizado) = NOPAT + D&A − CapEx mant. − refresh anualizado − CT × g',
            f'={E(eng,"nopat",3)}+{E(eng,"da",3)}-{E(eng,"cxm",3)}-{R["rf_pct"]}*{R["capex0"]}*{E(eng,"pidx",3)}/{R["rf_n"]}-{E(eng,"nwc",3)}*{g}')
    pv12 = put('pv12', 'VP FCF años 1–2 (ramp-up)', f'={E(eng,"fcf",1)}/(1+{w})^(1-0.5*{R["mid"]})+{E(eng,"fcf",2)}/(1+{w})^(2-0.5*{R["mid"]})')
    v0 = put('v0', 'EV sin crecimiento = VP años 1–2 + [FCF₃ / WACC] / (1+WACC)²', f'={pv12}+{b}/{w}/(1+{w})^2', bold=True)
    vg = put('vg', 'EV Gordon-Shapiro = VP años 1–2 + [FCF₃ / (WACC − g)] / (1+WACC)²', f'={pv12}+IF({w}>{g},{b}/({w}-{g}),0)/(1+{w})^2', bold=True, fill=F_KEY)
    adj = f'{E(eng,"fcf",0)}-{R["debt0"]}+{R["cash0"]}'
    put('pre0', 'Equity pre-money sin crecimiento (después de DLOM)', f'=IF({v0}+{adj}>0,({v0}+{adj})*(1-{sc("dlom")}),{v0}+{adj})')
    put('pre', 'Equity pre-money Gordon (después de DLOM)', f'=IF({vg}+{adj}>0,({vg}+{adj})*(1-{sc("dlom")}),{vg}+{adj})', bold=True, fill=F_KEY)
    rows['end'] = r_; return rows

# ======================================================================================
# 4. HOJAS EN ORDEN
# ======================================================================================
PL = wb.create_sheet('P&L y FCF')
title(PL, '=Supuestos!$B$6&" — P&L, NIF D-5 Y FREE CASH FLOW PROYECTADO (10 años)"', 'Motor del modelo para el escenario activo (Supuestos → escenario activo). Cifras en MXN nominales.')
widths(PL, {'A': 70, **{CL(i): 14 for i in range(2, 16)}})
ENG = {'P': q('P&L y FCF')}
ENG['rows'] = engine(PL, 5, f'={R["scen"]}', 'activo')
er = ENG['rows']
PL.freeze_panes = 'B6'

DCF = wb.create_sheet('DCF Valuación')
title(DCF, 'MÉTODO 1 — DCF / FCF DESCONTADO  |  valor terminal acotado a la vida del arrendamiento',
      'Escenario activo. FCF pre-IFRS16 (renta como costo) descontado al WACC; equity = EV + FCF año 0 − deuda + caja; DLOM al equity.')
widths(DCF, {'A': 78, **{CL(i): 14 for i in range(2, 13)}})
sec(DCF, 5, 'A. FLUJOS, VALOR TERMINAL Y EV', 12)
DR = block_dcf(DCF, 6, ENG, f'{q("P&L y FCF")}$B${er["scen"]}')

# P&L: métricas
r_ = er['end'] + 1
sec(PL, r_, 'H. MÉTRICAS DEL PROYECTO', 13); r_ += 1
mr = {}
def pm(key, lab, f, fmt=CUR, bold=False, note=''):
    global r_
    W(PL, f'A{r_}', lab, bold=bold); W(PL, f'B{r_}', f, fmt, bold=bold); W(PL, f'C{r_}', note, italic=True, color=GREY)
    mr[key] = r_; r_ += 1
W(PL, f'A{r_}', 'FCF + valor terminal (para TIR)')
for t in range(0, N + 1):
    c = YC[t]
    W(PL, f'{c}{r_}', f'={c}{er["fcf"]}' + (f'+{q("DCF Valuación")}$D${DR["tvs"]}' if t == N else ''), CUR)
mr['fcf_tv'] = r_; r_ += 1
pm('wacc', 'WACC del escenario', f'={q("DCF Valuación")}$D${DR["w"]}', PCT2)
pm('irr', 'TIR del proyecto (FCF año 0–10 + VT)', f'=IFERROR(IRR(B{mr["fcf_tv"]}:L{mr["fcf_tv"]}),"N/A")', PCT, True)
pm('npv', 'VPN al WACC = EV DCF + FCF año 0', f'={q("DCF Valuación")}$D${DR["ev"]}+B{er["fcf"]}', CUR, True)
pm('neg', 'Años con FCF acumulado negativo (incluye año 0)', f'=COUNTIF(B{er["fcf_cum"]}:L{er["fcf_cum"]},"<0")', '0')
pm('payback', 'Payback (años, interpolado; desde el año 0)',
   f'=IF(B{r_-1}>{N},"> {N} años",IF(B{r_-1}=0,0,B{r_-1}-1+(-INDEX(B{er["fcf_cum"]}:L{er["fcf_cum"]},1,B{r_-1}))/INDEX(B{er["fcf"]}:L{er["fcf"]},1,B{r_-1}+1)))', DEC, True)
W(PL, f'A{r_}', 'UNIT ECONOMICS — año 2 (primer año estabilizado)', bold=True); r_ += 1
y2 = 'D'
pm('ue_cov', 'Cubiertos/día (con ramp-up y crecimiento)', f'={y2}{er["covyr"]}/{R["days"]}', NUM1)
pm('ue_tk', 'Ticket promedio salón', f'={y2}{er["ticket"]}', CUR)
pm('ue_rpc', 'Venta total por cubierto (incluye delivery)', f'=IFERROR({y2}{er["rev"]}/{y2}{er["covyr"]},0)', CUR)
var2 = f'({y2}{er["c_food"]}+{y2}{er["c_bev"]}+SUM({y2}{er["x_fee"]}:{y2}{er["o_oth"]}))'
pm('ue_var', 'Costo variable por cubierto (F&B, comisiones, gastos % ventas)', f'=IFERROR({var2}/{y2}{er["covyr"]},0)', CUR)
pm('ue_cm', 'Margen de contribución por cubierto', f'=B{r_-2}-B{r_-1}', CUR, True)
pm('ue_cmp', 'Margen de contribución %', f'=IFERROR(B{r_-1}/B{r_-3},0)', PCT)
pm('ue_fix4', 'Costos fijos 4-wall anuales (nómina + renta + administración)', f'={y2}{er["labor"]}+{y2}{er["rent"]}+{y2}{er["admin"]}', CUR)
pm('be4', 'BREAK-EVEN EBITDA 4-wall (cubiertos/día)', f'=IFERROR(B{r_-1}/B{mr["ue_cm"]}/{R["days"]},0)', NUM1, True)
pm('be', 'Break-even EBITDA empresa (cubiertos/día, incluye overhead)', f'=IFERROR((B{mr["ue_fix4"]}+{y2}{er["ovh"]})/B{mr["ue_cm"]}/{R["days"]},0)', NUM1)
pm('be_cush', 'Colchón: cubiertos/día año 2 ÷ break-even empresa − 1', f'=IFERROR(B{mr["ue_cov"]}/B{r_-1}-1,0)', PCT, True)
pm('sqm', 'Ventas por m² (año 2)', f'={y2}{er["rev"]}/{R["m2"]}', CUR)
pm('seat', 'Ventas por asiento (año 2)', f'={y2}{er["rev"]}/{R["seats"]}', CUR)
pm('lab_pct', 'Nómina % ventas (año 2)', f'=IFERROR({y2}{er["labor"]}/{y2}{er["rev"]},0)', PCT)
pm('rent_pct', 'Renta % ventas (año 2; benchmark 8–12%)', f'=IFERROR({y2}{er["rent"]}/{y2}{er["rev"]},0)', PCT)

# DCF: sensibilidad WACC × g
r_ = DR['end'] + 1
sec(DCF, r_, 'B. SENSIBILIDAD — EV DCF (método de VT base)  |  WACC × g', 12); r_ += 1
w0 = f'$D${DR["w"]}'; g0 = f'$D${DR["g"]}'
W(DCF, f'A{r_}', 'g \\ WACC (desviación vs. escenario)', bold=True)
wd = [-0.04, -0.02, 0, 0.02, 0.04]; gd = [-0.01, -0.005, 0, 0.005, 0.01]
for j, d in enumerate(wd): W(DCF, f'{CL(2+j)}{r_}', f'={w0}+({d})', PCT, bold=True)
sens_hdr = r_; r_ += 1
fcfr = f'$B${DR["fcf"]}:${CL(N+1)}${DR["fcf"]}'
tr = f'{ER(ENG,"t")}'
for i, d in enumerate(gd):
    W(DCF, f'A{r_}', f'={g0}+({d})', PCT, bold=True)
    for j in range(5):
        wc = f'{CL(2+j)}${sens_hdr}'; gc = f'$A{r_}'
        f11 = f'($D${DR["b_ex"]}*(1+{gc})-{E(ENG,"nwc",N)}*{gc})'
        ann = lambda n: f'{f11}*(1-((1+{gc})/(1+{wc}))^({n}))/({wc}-{gc})'
        n1 = f'$D${DR["n1"]}'
        tvf = f'({ann(n1)}+{SC("prob", q("P&L y FCF")+"$B$"+str(er["scen"]))}*({ann(n1+"+"+R["renew"])}-{ann(n1)}))'
        tvg = f'({f11}/({wc}-{gc}))'
        f = f'=SUMPRODUCT({fcfr},1/(1+{wc})^({tr}-0.5*{R["mid"]}))+IF({R["tv_method"]}=1,{tvf},{tvg})/(1+{wc})^{N}'
        W(DCF, f'{CL(2+j)}{r_}', f, CUR, fill=F_KEY if (i == 2 and j == 2) else None)
    r_ += 1
W(DCF, f'A{r_}', 'Celda central (verde) = EV del escenario activo (validado en Checks). Rango WACC ±4pp, g ±1pp.', italic=True, color=GREY); DR['sens_c'] = f'D{sens_hdr+3}'; r_ += 2
sec(DCF, r_, 'C. LECTURA PARA COMITÉ', 12); r_ += 1
dtxt = [f'="• Base = VT de vida finita: plazo remanente "&TEXT({R["term"]},"0")&" años + "&TEXT({R["renew"]},"0")&" años de renovación con prob. "&TEXT({SC("prob",q("P&L y FCF")+"$B$"+str(er["scen"]))},"0%")&". Un restaurante no vale más allá de su local."',
        f'="• Gordon perpetuo daría EV de "&TEXT($D${DR["evg"]},"$#,##0")&" vs "&TEXT($D${DR["evf"]},"$#,##0")&" con vida finita: la diferencia es valor que depende de renovar el contrato indefinidamente."',
        f'="• % del EV en valor terminal: "&TEXT($D${DR["ptv"]},"0.0%")&" → "&$D${DR["ptv_al"]}',
        '="• Iliquidez se aplica una sola vez (DLOM al equity); el WACC no lleva prima de iliquidez para evitar doble conteo (corrección vs. base Shivai)."']
for tx in dtxt: W(DCF, f'A{r_}', tx); r_ += 1

# ---- Comparables
CP = wb.create_sheet('Comparables')
title(CP, 'MÉTODO 2 — COMPARABLES EV/EBITDA  |  restaurantes México / EUA y transacciones precedentes',
      'EV incluye pasivo por arrendamiento ⇒ se aplica a EBITDA post-IFRS16 y se resta el pasivo por arrendamiento (definición consistente).')
widths(CP, {'A': 70, 'B': 14, 'C': 14, 'D': 16, 'E': 60, 'F': 14, 'G': 14})
sec(CP, 5, 'A. SET DE COMPARABLES (vínculo a Supuestos, bloque I)', 7)
hdr(CP, 6, ['Empresa / transacción', 'Set', 'EV/EBITDA LTM', 'MX/LatAm', 'Transacción', 'EUA', 'Industria'])
rr0 = 7
for i in range(R['comp_c1'] - R['comp_c0'] + 1):
    sr = R['comp_c0'] + i; rw = rr0 + i
    W(CP, f'A{rw}', f'={SN}A{sr}'); W(CP, f'B{rw}', f'={SN}C{sr}'); W(CP, f'C{rw}', f'=IF(ISNUMBER({SN}B{sr}),{SN}B{sr},"N/D")', MULT)
    for col, code in zip('DEFG', ['MX', 'TX', 'US', 'IND']):
        W(CP, f'{col}{rw}', f'=IF(AND(B{rw}="{code}",ISNUMBER(C{rw})),C{rw},"")', MULT)
last = rr0 + R['comp_c1'] - R['comp_c0']
sr_ = last + 2
W(CP, f'A{sr_}', 'Mediana por set', bold=True)
for col in 'DEFG': W(CP, f'{col}{sr_}', f'=IFERROR(MEDIAN({col}{rr0}:{col}{last}),"N/D")', MULT, bold=True)
W(CP, f'A{sr_+1}', 'Observaciones válidas por set')
for col in 'DEFG': W(CP, f'{col}{sr_+1}', f'=COUNT({col}{rr0}:{col}{last})', '0')
W(CP, f'A{sr_+2}', '⚠ Set México con 1 observación verificable (Alsea, no verificada): el múltiplo es un rango de juicio, no un dato estadístico. Open item #1.', italic=True, color='C65911')
assert sr_ + 2 < 21
r_ = 21
sec(CP, r_, 'B. SELECCIÓN DE MÚLTIPLO POR ESCENARIO', 7); r_ += 0
W(CP, f'A22', 'Optimista = mediana de transacciones precedentes (prima de control incluida)'); W(CP, 'C22', f'=E{sr_}', MULT, bold=True)
W(CP, f'A23', 'Base ★ = promedio (mediana cotizadas MX/LatAm, mediana transacciones)'); W(CP, 'C23', f'=AVERAGE(D{sr_},E{sr_})', MULT, bold=True)
W(CP, f'A24', 'Conservador = mediana cotizadas MX/LatAm'); W(CP, 'C24', f'=D{sr_}', MULT, bold=True)
W(CP, 'A25', '="EUA ("&TEXT(F' + str(sr_) + ',"0.0x")&") e industria Damodaran ("&TEXT(G' + str(sr_) + ',"0.0x")&") sólo como referencia: escala, crecimiento y liquidez no trasladables a una unidad en Guanajuato."', italic=True, color=GREY)
sec(CP, 27, 'C. VALUACIÓN POR COMPARABLES — ESCENARIO ACTIVO', 7)
CR = block_comps(CP, 28, ENG, f'{q("P&L y FCF")}$B${er["scen"]}', f'{q("DCF Valuación")}$D${DR["w"]}')
r_ = CR['end'] + 1
W(CP, f'A{r_}', 'Cross-check EV/Ventas: N/D — ningún comparable con EV/Ventas verificable en la fecha de corte (open item).', italic=True, color='C65911'); r_ += 1
W(CP, f'A{r_}', 'EV implícito por asiento (empresa)'); W(CP, f'D{r_}', f'=D{CR["ev0"]}/{R["seats"]}', CUR); CR['evseat'] = r_; r_ += 1
W(CP, f'A{r_}', 'EV/asiento de comparables: N/D — no hay asientos por unidad reportados por Alsea/CMR; no se fabrica el dato.', italic=True, color='C65911'); r_ += 2
sec(CP, r_, 'D. TRANSACCIONES PRECEDENTES (México / LatAm)', 7); r_ += 1
for tx in ['• No se encontró ninguna transacción de restaurantes en México/LatAm 2021–2026 con EV/EBITDA divulgado oficialmente.',
           '• La Casa de Toño ← Grupo Gigante (2026): ">8x EBITDA ajustado", ~US$400M (Bloomberg, fuentes anónimas); sin acuerdo vinculante a ago-2026.',
           '• Vips México ← Alsea (2014): ~8.5x EBITDA 2012 (cálculo propio con montos públicos). Fuera de ventana de 5 años.',
           '• Contexto: EY mediana M&A consumo 2025 ~8.5x; analista citado por El CEO: restaurantes 6–7x. Ambos no verificados.']:
    W(CP, f'A{r_}', tx); r_ += 1

# ---- Perpetuidad
PP = wb.create_sheet('Perpetuidad')
title(PP, 'MÉTODO 3 — PERPETUIDAD (sin crecimiento y Gordon-Shapiro)', 'Dos etapas: VP de los años de ramp-up + perpetuidad sobre FCF normalizado del año 3. Ignora el fin del arrendamiento ⇒ cota superior.')
widths(PP, {'A': 82, 'B': 14, 'C': 14, 'D': 16, 'E': 14, 'F': 14, 'G': 14})
sec(PP, 5, 'A–B. PERPETUIDAD — ESCENARIO ACTIVO', 7)
PR = block_perp(PP, 6, ENG, f'{q("P&L y FCF")}$B${er["scen"]}', f'{q("DCF Valuación")}$D${DR["w"]}', f'{q("DCF Valuación")}$D${DR["g"]}')
r_ = PR['end'] + 1
sec(PP, r_, 'C. SENSIBILIDAD — EV GORDON  |  WACC × g', 7); r_ += 1
W(PP, f'A{r_}', 'g \\ WACC', bold=True)
w0 = f'{q("DCF Valuación")}$D${DR["w"]}'; g0 = f'{q("DCF Valuación")}$D${DR["g"]}'
for j, d in enumerate(wd): W(PP, f'{CL(2+j)}{r_}', f'={w0}+({d})', PCT, bold=True)
ph = r_; r_ += 1
for i, d in enumerate(gd):
    W(PP, f'A{r_}', f'={g0}+({d})', PCT, bold=True)
    for j in range(5):
        wc = f'{CL(2+j)}${ph}'; gc = f'$A{r_}'
        b = f'({E(ENG,"nopat",3)}+{E(ENG,"da",3)}-{E(ENG,"cxm",3)}-{R["rf_pct"]}*{R["capex0"]}*{E(ENG,"pidx",3)}/{R["rf_n"]}-{E(ENG,"nwc",3)}*{gc})'
        f = f'={E(ENG,"fcf",1)}/(1+{wc})^(1-0.5*{R["mid"]})+{E(ENG,"fcf",2)}/(1+{wc})^(2-0.5*{R["mid"]})+{b}/({wc}-{gc})/(1+{wc})^2'
        W(PP, f'{CL(2+j)}{r_}', f, CUR, fill=F_KEY if (i == 2 and j == 2) else None)
    r_ += 1
PR['sens_c'] = f'D{ph+3}'

# ---- Cap Table
CT = wb.create_sheet('Cap Table')
title(CT, 'CAP TABLE POST-MONEY + APORTACIONES IN-KIND (si aplican)', 'Pre-money concluido (Resumen) + cash + in-kind = post-money. Las aportaciones in-kind no afectan el FCF.')
widths(CT, {'A': 46, 'B': 40, 'C': 16, 'D': 16, 'E': 16, 'F': 16, 'G': 16})
sec(CT, 5, 'A. APORTACIÓN IN-KIND — COMPONENTES', 7)
hdr(CT, 6, ['Componente', 'Descripción', '% del total', 'Valor MXN', 'Método de valuación'])
ik = [('Marca / know-how / recetas', 'Propiedad intelectual del concepto', 0.0, 'Exceso de utilidades (avalúo)'),
      ('Mobiliario / equipo aportado', 'Activos físicos existentes', 0.0, 'Valor razonable (avalúo)'),
      ('Derechos de arrendamiento / licencias', 'Cesión de contrato o licencia de alcoholes', 0.0, 'Valor de mercado')]
for i, (a, b, p, m) in enumerate(ik):
    rw = 7 + i
    W(CT, f'A{rw}', a); W(CT, f'B{rw}', b, color=GREY); W(CT, f'C{rw}', p, PCT, kind='input', fill=F_PEND)
    W(CT, f'D{rw}', f'=C{rw}*{R["inkind"]}', CUR); W(CT, f'E{rw}', m, color=GREY)
W(CT, 'A10', 'TOTAL IN-KIND', bold=True); W(CT, 'C10', '=SUM(C7:C9)', PCT, bold=True); W(CT, 'D10', '=SUM(D7:D9)', CUR, bold=True)
W(CT, 'A11', '=IF(' + R['inkind'] + '=0,"In-kind = 0: no aplica. Si se captura, los % deben sumar 100% (Check).","Requiere avalúo independiente antes del cierre.")', italic=True, color=GREY)
sec(CT, 13, 'B. CAP TABLE POST-MONEY POR MÉTODO (escenario base)', 7)
hdr(CT, 14, ['Accionista', 'Tipo', 'Concluido ★', 'DCF', 'Comparables', 'VC Method', ''])
CT_ROWS = {'pre': 15, 'cash': 16, 'ik': 17, 'post': 18}
W(CT, 'A15', 'Fundadores / accionistas actuales (pre-money)'); W(CT, 'B15', 'Equity existente + sweat equity', color=GREY)
W(CT, 'A16', 'Inversionista (cash)'); W(CT, 'B16', 'Cash', color=GREY)
W(CT, 'A17', 'Aportantes in-kind'); W(CT, 'B17', 'In-kind', color=GREY)
W(CT, 'A18', 'TOTAL POST-MONEY ($)', bold=True)
W(CT, 'A20', '% Fundadores', bold=True); W(CT, 'A21', '% Inversionista cash', bold=True); W(CT, 'A22', '% In-kind', bold=True); W(CT, 'A23', 'Suma (debe ser 100%)', bold=True)
sec(CT, 25, 'C. CONDICIONES LEGALES PARA INSTRUMENTAR', 7)
for i, tx in enumerate(['✅ Aumento de capital en escritura (Asamblea Extraordinaria) y registro en libro de accionistas (LGSM).',
                        '✅ Acciones preferentes o serie B para el inversionista con liquidation preference 1x no participante.',
                        '✅ Acuerdo de accionistas: drag-along, tag-along, ROFR, anti-dilución (weighted average) y lista de decisiones reservadas.',
                        '✅ Desembolso por tramos atados a hitos: licencia de alcoholes y autorización INAH/municipal antes del tramo de obra.',
                        '⚠ In-kind (si aplica): avalúo independiente + contrato de aportación; revisar implicaciones de ISR con asesor fiscal.',
                        '⚠ Key-man insurance y no competencia para chef / socio operador; vesting de sweat equity a 4 años.']):
    W(CT, f'A{26+i}', tx)

# ---- VC Method
VC = wb.create_sheet('VC Method')
title(VC, 'MÉTODO 4 — VC METHOD  |  valor desde la salida esperada', 'Post-money hoy = Equity de salida / (1+TIR objetivo)^n. Pre-money = post − cash − in-kind.')
widths(VC, {'A': 78, 'B': 14, 'C': 14, 'D': 16, 'E': 16, 'F': 16, 'G': 16, 'H': 16})
sec(VC, 5, 'A. SALIDA — ESCENARIO ACTIVO', 8)
VR = block_vc(VC, 6, ENG, f'{q("P&L y FCF")}$B${er["scen"]}')
r_ = VR['end'] + 1
sec(VC, r_, 'B. PERFILES DE INVERSIONISTA — TIR OBJETIVO → PARTICIPACIÓN Y VALUACIÓN', 8); r_ += 1
hdr(VC, r_, ['Perfil', 'TIR objetivo', '(1+TIR)^n', 'Post-money hoy', 'Pre-money hoy', '% inversionista', '% fundadores', '']); r_ += 1
VR['prof0'] = r_
for lab, irr in [('Family office / estratégico', 0.25), ('PE México (bajo riesgo)', 0.30), ('PE / VC México ★', 0.35), ('VC early stage', 0.40), ('VC agresivo', 0.50)]:
    W(VC, f'A{r_}', lab); W(VC, f'B{r_}', irr, PCT, kind='input'); W(VC, f'C{r_}', f'=(1+B{r_})^{R["vc_n"]}', DEC)
    W(VC, f'D{r_}', f'=$D${VR["eqx"]}/C{r_}', CUR); W(VC, f'E{r_}', f'=D{r_}-{R["monto"]}-{R["inkind"]}', CUR)
    W(VC, f'F{r_}', f'=IF(D{r_}<={R["monto"]},"n.s.",{R["monto"]}/D{r_})', PCT); W(VC, f'G{r_}', f'=IF(D{r_}<={R["monto"]},"n.s.",E{r_}/D{r_})', PCT); r_ += 1
W(VC, f'A{r_}', 'Si % fundadores es negativo, la salida esperada no alcanza para justificar el cheque a esa TIR.', italic=True, color=GREY); r_ += 2
sec(VC, r_, 'C. SENSIBILIDAD — POST-MONEY HOY  |  múltiplo de salida efectivo × TIR', 8); r_ += 1
W(VC, f'A{r_}', 'Múltiplo \\ TIR', bold=True)
irrs = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
for j, x in enumerate(irrs): W(VC, f'{CL(2+j)}{r_}', x, PCT, bold=True, kind='input')
vh = r_; r_ += 1
for mlt in [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]:
    W(VC, f'A{r_}', mlt, MULT, bold=True, kind='input')
    for j in range(6):
        W(VC, f'{CL(2+j)}{r_}', f'=($D${VR["eb"]}*$A{r_}-$D${VR["llx"]})/(1+{CL(2+j)}${vh})^{R["vc_n"]}', CUR)
    r_ += 1
r_ += 1
sec(VC, r_, 'D. RETORNO DEL INVERSIONISTA AL PRECIO CONCLUIDO (escenario activo; dividendos = FCF positivo × % participación)', 8); r_ += 1
hdr(VC, r_, ['Concepto', 'Año 0'] + [f'Año {t}' for t in range(1, 6)] + [''], start=1); r_ += 1
W(VC, f'A{r_}', '% participación del inversionista (precio concluido, Cap Table; acotado a 0–100%)'); W(VC, f'B{r_}', f'=MAX(0,MIN(1,{q("Cap Table")}C21))', PCT); VR['own_c'] = r_; r_ += 1
W(VC, f'A{r_}', 'Flujo del inversionista (− inversión, + dividendos, + salida)')
W(VC, f'B{r_}', f'=-{R["monto"]}', CUR)
for t in range(1, 6):
    W(VC, f'{CL(2+t)}{r_}', f'=MAX(0,{E(ENG,"fcf",t)})*$B${VR["own_c"]}' + (f'+$D${VR["eqx"]}*$B${VR["own_c"]}' if t == 5 else ''), CUR)
VR['flow'] = r_; r_ += 1
W(VC, f'A{r_}', 'TIR del inversionista'); W(VC, f'B{r_}', f'=IFERROR(IRR(B{VR["flow"]}:G{VR["flow"]}),"N/A")', PCT, bold=True); VR['inv_irr'] = r_; r_ += 1
W(VC, f'A{r_}', 'MOIC del inversionista'); W(VC, f'B{r_}', f'=SUM(C{VR["flow"]}:G{VR["flow"]})/{R["monto"]}', MULT, bold=True); VR['moic'] = r_; r_ += 1
W(VC, f'A{r_}', 'Nota: horizonte de 5 años = salida antes del refresh del año 6; la vida del contrato limita el múltiplo de salida.', italic=True, color=GREY)

# ======================================================================================
# 5. ESCENARIOS (4 motores en paralelo)
# ======================================================================================
ES = wb.create_sheet('Escenarios')
title(ES, 'ESCENARIOS — 4 motores completos en paralelo (Optimista · Base ★ · Conservador · Estrés)',
      'Mismo generador de fórmulas que las hojas de detalle. El bloque del escenario activo se valida contra las hojas de método en Checks.')
widths(ES, {'A': 74, **{CL(i): 14 for i in range(2, 16)}})
SCEN = {}
r_ = 5
for s in range(1, 5):
    sec(ES, r_, f'══ ESCENARIO {s} ══', 15); r_ += 1
    rows = engine(ES, r_, f'={s}', str(s))
    eng = {'P': q('Escenarios'), 'rows': rows}
    r_ = rows['end'] + 1
    sref = f'$B${rows["scen"]}'
    sec(ES, r_, 'Valuación del escenario — DCF', 12); r_ += 1
    d = block_dcf(ES, r_, eng, sref); r_ = d['end'] + 1
    sec(ES, r_, 'Valuación del escenario — Comparables', 12); r_ += 1
    c = block_comps(ES, r_, eng, sref, f'$D${d["w"]}'); r_ = c['end'] + 1
    sec(ES, r_, 'Valuación del escenario — VC Method', 12); r_ += 1
    v = block_vc(ES, r_, eng, sref); r_ = v['end'] + 1
    sec(ES, r_, 'Valuación del escenario — Perpetuidad', 12); r_ += 1
    p = block_perp(ES, r_, eng, sref, f'$D${d["w"]}', f'$D${d["g"]}'); r_ = p['end'] + 2
    SCEN[s] = {'eng': eng, 'dcf': d, 'cmp': c, 'vc': v, 'perp': p}
ESN = q('Escenarios')
def es(s, blk, key): return f'{ESN}$D${SCEN[s][blk][key]}'
def esE(s, key, t): return E(SCEN[s]['eng'], key, t)

# ======================================================================================
# 6. RESUMEN
# ======================================================================================
RS = wb.create_sheet('Resumen')
wb.move_sheet('Resumen', offset=-(len(wb.sheetnames) - 8))  # después de VC Method
title(RS, '="RESUMEN EJECUTIVO — VALUACIÓN INTEGRAL "&UPPER(Supuestos!$B$6)&"  |  "&Supuestos!$B$7',
      'Para Comité de Inversiones. Equity = pre-money, después de DLOM (salvo VC Method, cuya TIR ya incorpora iliquidez). MXN.')
widths(RS, {'A': 44, 'B': 17, 'C': 17, 'D': 17, 'E': 17, 'F': 17, 'G': 17, 'H': 17, 'I': 40})
sec(RS, 5, 'A. TABLA CONSOLIDADA — MÉTODO × ESCENARIO (EV y equity pre-money)', 9)
hdr(RS, 6, ['Método', 'EV Optimista', 'Equity Optimista', 'EV Base ★', 'Equity Base ★', 'EV Conservador', 'Equity Conservador', 'Peso', 'Nota'])
methods = [('1. DCF — VT vida finita ★', 'dcf', 'evf', None, R['w_dcf'], 'Método principal'),
           ('1b. DCF — VT Gordon (referencia)', 'dcf', 'evg', 'preg', None, 'Cota superior: supone renovar el local a perpetuidad'),
           ('2. Comparables EV/EBITDA', 'cmp', 'ev0', 'pre', R['w_cmp'], 'Múltiplo ajustado por tamaño; DLOM'),
           ('3. VC Method', 'vc', 'post', 'pre', R['w_vc'], 'EV = post-money implícito; sin DLOM'),
           ('4. Perpetuidad Gordon (cross-check)', 'perp', 'vg', 'pre', R['w_perp'], 'Ignora fin del arrendamiento')]
RSR = {}
for i, (lab, blk, evk, eqk, wref, note) in enumerate(methods):
    rw = 7 + i; W(RS, f'A{rw}', lab, bold=wref is not None and blk == 'dcf')
    for j, s in enumerate([1, 2, 3]):
        if blk == 'dcf' and evk == 'evf':
            W(RS, f'{CL(2+2*j)}{rw}', f'={es(s,"dcf","evf")}', CUR)
            # equity con VT finita: re-calcular desde evf
            adj = es(s, 'dcf', 'adj'); dl = SC('dlom', f'{ESN}$B${SCEN[s]["eng"]["rows"]["scen"]}')
            W(RS, f'{CL(3+2*j)}{rw}', f'=IF({es(s,"dcf","evf")}+{adj}>0,({es(s,"dcf","evf")}+{adj})*(1-{dl}),{es(s,"dcf","evf")}+{adj})', CUR, bold=j == 1)
        else:
            W(RS, f'{CL(2+2*j)}{rw}', f'={es(s,blk,evk)}', CUR)
            W(RS, f'{CL(3+2*j)}{rw}', f'={es(s,blk,eqk)}', CUR, bold=j == 1)
    if wref: W(RS, f'H{rw}', f'={wref}', PCT)
    else: W(RS, f'H{rw}', 0, PCT, color=GREY)
    W(RS, f'I{rw}', note, italic=True, color=GREY); RSR[blk + evk] = rw
rw = 12
W(RS, f'A{rw}', 'VALOR CONCLUIDO (ponderado)', bold=True, fill=F_KEY)
for j, col in enumerate(['C', 'E', 'G']):
    W(RS, f'{col}{rw}', f'=SUMPRODUCT({col}7:{col}11,$H$7:$H$11)', CUR, bold=True, fill=F_KEY)
W(RS, f'H{rw}', '=SUM(H7:H11)', PCT, bold=True, fill=F_KEY); RSR['concl'] = rw
W(RS, 'A13', '="Escenarios: Optimista (cubiertos ×"&TEXT(INDEX(' + R['f_cov'] + ',1,1),"0.00")&", múltiplo "&TEXT(INDEX(' + R['mult'] + ',1,1),"0.0x")&") · Base ★ (WACC "&TEXT(' + es(2, 'dcf', 'w') + ',"0.0%")&", g "&TEXT(' + es(2, 'dcf', 'g') + ',"0.0%")&", múltiplo "&TEXT(INDEX(' + R['mult'] + ',1,2),"0.0x")&", DLOM "&TEXT(INDEX(' + R['dlom'] + ',1,2),"0%")&") · Conservador (cubiertos ×"&TEXT(INDEX(' + R['f_cov'] + ',1,3),"0.00")&", WACC "&TEXT(' + es(3, 'dcf', 'w') + ',"0.0%")&")"', italic=True, color=GREY, size=8)
RSR['label'] = 13

sec(RS, 15, 'B. PONDERACIÓN DE MÉTODOS — JUSTIFICACIÓN', 9)
for i, tx in enumerate(['="DCF vida finita "&TEXT(' + R['w_dcf'] + ',"0%")&": único método que modela ramp-up, prime cost, CT negativo, refresh y la vida del local."',
                        '="Comparables "&TEXT(' + R['w_cmp'] + ',"0%")&": ancla de mercado, pero el set verificable es pequeño (open item) y son cadenas con escala."',
                        '="VC Method "&TEXT(' + R['w_vc'] + ',"0%")&": precio de un inversionista financiero; muy sensible al múltiplo de salida."',
                        '="Perpetuidad "&TEXT(' + R['w_perp'] + ',"0%")&" y Gordon 0%: suponen vida infinita del local (contradice el contrato); sólo cross-check."']):
    W(RS, f'A{16+i}', tx)

sec(RS, 21, 'C. FOOTBALL FIELD — RANGO DE EQUITY PRE-MONEY POR MÉTODO (conservador → optimista)', 9)
hdr(RS, 22, ['Método', 'Mínimo', 'Base ★', 'Máximo', 'Rango (máx − mín)'])
ff_methods = [(7, 'DCF vida finita ★'), (8, 'DCF Gordon'), (9, 'Comparables'), (10, 'VC Method'), (11, 'Perpetuidad'), (12, 'Concluido ponderado')]
for i, (src_r, lab) in enumerate(ff_methods):
    rw = 23 + i
    W(RS, f'A{rw}', lab, bold=src_r == 12)
    W(RS, f'B{rw}', f'=MIN(C{src_r},E{src_r},G{src_r})', CUR); W(RS, f'C{rw}', f'=E{src_r}', CUR, bold=True); W(RS, f'D{rw}', f'=MAX(C{src_r},E{src_r},G{src_r})', CUR)
    W(RS, f'E{rw}', f'=D{rw}-B{rw}', CUR)
# helper columns K..N: segmentos apilados que funcionan con rangos que cruzan cero
for j, h in enumerate(['off+ (oculto)', 'rango +', 'off− (oculto)', 'rango −']):
    W(RS, f'{CL(16+j)}22', h, bold=True, color=GREY, size=8)
for i in range(6):
    rw = 23 + i
    W(RS, f'P{rw}', f'=MAX(0,B{rw})', CUR, color=GREY, size=8); W(RS, f'Q{rw}', f'=MAX(0,D{rw})-MAX(0,B{rw})', CUR, color=GREY, size=8)
    W(RS, f'R{rw}', f'=MIN(0,D{rw})', CUR, color=GREY, size=8); W(RS, f'S{rw}', f'=MIN(0,B{rw})-MIN(0,D{rw})', CUR, color=GREY, size=8)
[RS.column_dimensions.__getitem__(c_).__setattr__('width', 12) for c_ in 'PQRS']
ch = BarChart(); ch.type = 'bar'; ch.grouping = 'stacked'; ch.overlap = 100; ch.gapWidth = 60
ch.title = 'Football field — equity pre-money (MXN), mínimo → máximo'
for col in (16, 17, 18, 19):
    ch.add_data(Reference(RS, min_col=col, min_row=22, max_row=28), titles_from_data=True)
ch.set_categories(Reference(RS, min_col=1, min_row=23, max_row=28))
for k, s_ in enumerate(ch.series):
    if k in (0, 2):
        s_.graphicalProperties.noFill = True; s_.graphicalProperties.line.noFill = True
    else:
        s_.graphicalProperties.solidFill = NAVY; s_.graphicalProperties.line.solidFill = NAVY
ch.legend = None; ch.height = 8; ch.width = 18; ch.y_axis.numFmt = '$#,##0'; ch.x_axis.scaling.orientation = 'maxMin'
ch.y_axis.delete = False; ch.x_axis.delete = False; ch.x_axis.tickLblPos = 'low'
RS.add_chart(ch, 'G21')

sec(RS, 31, 'D. KPIs DEL PROYECTO (escenario base)', 9)
hdr(RS, 32, ['KPI', 'Valor', 'Referencia / benchmark', '', '', '', '', '', ''])
b = SCEN[2]
y2 = lambda k: esE(2, k, 2)
kpis = [('WACC (Ke all-equity)', f'={es(2,"dcf","w")}', PCT2, '="Ke Fisher USD cross-check: "&TEXT(' + R['ke_fisher'] + ',"0.0%")'),
        ('TIR del proyecto', f'={q("P&L y FCF")}B{mr["irr"]}', PCT, '="vs WACC "&TEXT(' + R['wacc'] + ',"0.0%")&" — escenario activo"'),
        ('VPN del proyecto al WACC', f'={q("P&L y FCF")}B{mr["npv"]}', CUR, '="Escenario activo; > 0 crea valor sobre la inversión"'),
        ('MOIC inversionista (precio concluido, 5 años)', f'={q("VC Method")}B{VR["moic"]}', MULT, '="TIR inversionista: "&TEXT(' + q("VC Method") + 'B' + str(VR["inv_irr"]) + ',"0.0%")'),
        ('Payback del proyecto (años)', f'={q("P&L y FCF")}B{mr["payback"]}', DEC, '="Desde el año 0, FCF acumulado"'),
        ('EBITDA 4-wall año 2 (pre-IFRS16)', f'={y2("ebitda4")}', CUR, '="Margen "&TEXT(' + y2("ebitda4m") + ',"0.0%")&" · benchmark 10–18%"'),
        ('EBITDA empresa año 2 pre / post IFRS16', f'={y2("ebitda")}', CUR, '="Post-IFRS16: "&TEXT(' + y2("ebitda_post") + ',"$#,##0")'),
        ('Prime cost año 2', f'={y2("primep")}', PCT, '="Meta < 60–65%"'),
        ('Ventas año 2', f'={y2("rev")}', CUR, '="Ticket salón "&TEXT(' + y2("ticket") + ',"$#,##0")'),
        ('Ventas por m² (año 2)', f'={y2("rev")}/{R["m2"]}', CUR, '="Benchmark México: N/D (no verificable)"'),
        ('Ventas por asiento (año 2)', f'={y2("rev")}/{R["seats"]}', CUR, '="Benchmark México: N/D (no verificable)"'),
        ('EV/asiento (DCF base)', f'={es(2,"dcf","evf")}/{R["seats"]}', CUR, '="Comparables: N/D — no se fabrica"'),
        ('% EV en valor terminal (DCF base)', f'={es(2,"dcf","ptv")}', PCT, f'={es(2,"dcf","ptv_al")}')]
for i, (lab, f, fmt, ref) in enumerate(kpis):
    rw = 33 + i; W(RS, f'A{rw}', lab); W(RS, f'B{rw}', f, fmt, bold=True); W(RS, f'C{rw}', ref, italic=True, color=GREY)
    RSR['kpi_' + str(i)] = rw
r0k = 33 + len(kpis) + 1
sec(RS, r0k, 'E. UNIT ECONOMICS Y BREAK-EVEN (escenario activo, año 2)', 9); r0k += 1
ue = [('Cubiertos/día año 2', 'ue_cov', NUM1), ('Ticket salón', 'ue_tk', CUR), ('Venta total por cubierto', 'ue_rpc', CUR), ('Costo variable por cubierto', 'ue_var', CUR),
      ('Margen de contribución por cubierto', 'ue_cm', CUR), ('Margen de contribución %', 'ue_cmp', PCT), ('Break-even EBITDA 4-wall (cubiertos/día)', 'be4', NUM1),
      ('Break-even EBITDA empresa (cubiertos/día)', 'be', NUM1), ('Colchón sobre break-even', 'be_cush', PCT), ('Nómina % ventas', 'lab_pct', PCT), ('Renta % ventas', 'rent_pct', PCT)]
for lab, k, fmt in ue:
    W(RS, f'A{r0k}', lab); W(RS, f'B{r0k}', f'={q("P&L y FCF")}B{mr[k]}', fmt, bold=k in ('be', 'be4', 'ue_cm')); RSR['ue_' + k] = r0k; r0k += 1
r0k += 1
sec(RS, r0k, 'F. MATRIZ DE RIESGOS (probabilidad × impacto, escala 1–5)', 9); r0k += 1
hdr(RS, r0k, ['Riesgo', 'Prob.', 'Impacto', 'Score', 'Nivel', 'Mitigante', '', '', '']); r0k += 1
risks = [('Ramp-up más lento / ocupación < plan', 4, 4, 'Desembolso por tramos; covenant de caja; reserva ≥ 2 meses de fijos.'),
         ('Licencia de alcoholes / uso de suelo no otorgada o tardía', 3, 5, 'CP: licencia vigente antes del tramo de obra; cesión de licencia existente.'),
         ('Restricciones INAH / municipio (obra, fachada, anuncios, terraza)', 3, 4, 'CP: dictamen INAH y permiso de imagen urbana antes del CapEx.'),
         ('Inflación de food cost / salario mínimo (+13% 2026)', 4, 3, 'Ingeniería de menú trimestral; contratos con proveedores; ajuste de precios.'),
         ('Concentración en eventos (Cervantino, Semana Santa) y demanda UG', 4, 3, 'Programación local fuera de temporada; menú ejecutivo para estudiantes.'),
         ('No renovación del arrendamiento', 2, 5, 'Opción de renovación y derecho de preferencia en contrato; VT acotado.'),
         ('Persona clave (chef / socio operador)', 3, 4, 'Key-man insurance, vesting, no competencia, recetas documentadas.'),
         ('Seguridad regional (Guanajuato 3º en percepción de inseguridad)', 3, 3, 'Seguros, CCTV, protocolo; ciudad capital con percepción menor (59.5%).'),
         ('Protección Civil / sanidad (COFEPRIS)', 2, 4, 'Programa interno de PC; auditoría sanitaria pre-apertura.')]
RSR['risk0'] = r0k
for a, p_, i_, m in risks:
    W(RS, f'A{r0k}', a); W(RS, f'B{r0k}', p_, '0', kind='input'); W(RS, f'C{r0k}', i_, '0', kind='input')
    W(RS, f'D{r0k}', f'=B{r0k}*C{r0k}', '0', bold=True)
    W(RS, f'E{r0k}', f'=IF(D{r0k}>=15,"ALTO",IF(D{r0k}>=9,"MEDIO","BAJO"))', bold=True); W(RS, f'F{r0k}', m, color=GREY); r0k += 1
r0k += 1
sec(RS, r0k, 'G. ESCENARIO DE ESTRÉS: −25% cubiertos y +15% food & beverage cost', 9); r0k += 1
hdr(RS, r0k, ['Métrica', 'Base ★', 'Estrés', 'Δ', 'Δ %', '', '', '', '']); r0k += 1
stress = [('EV DCF (vida finita)', es(2, 'dcf', 'evf'), es(4, 'dcf', 'evf'), CUR),
          ('Equity concluido ponderado', None, None, CUR),
          ('Ventas año 2', esE(2, 'rev', 2), esE(4, 'rev', 2), CUR),
          ('EBITDA empresa año 2', esE(2, 'ebitda', 2), esE(4, 'ebitda', 2), CUR),
          ('Prime cost % año 2', esE(2, 'primep', 2), esE(4, 'primep', 2), PCT),
          ('Caja mínima año 1 (mensual)', f'{ESN}$B${SCEN[2]["eng"]["rows"]["m_min"]}', f'{ESN}$B${SCEN[4]["eng"]["rows"]["m_min"]}', CUR),
          ('Covenant requerido', f'{ESN}$B${SCEN[2]["eng"]["rows"]["m_req"]}', f'{ESN}$B${SCEN[4]["eng"]["rows"]["m_req"]}', CUR)]
RSR['stress0'] = r0k
for lab, bref, sref, fmt in stress:
    W(RS, f'A{r0k}', lab)
    if bref is None:
        # equity concluido en estrés: mismos pesos
        W(RS, f'B{r0k}', f'=E{RSR["concl"]}', CUR)
        dl = SC('dlom', f'{ESN}$B${SCEN[4]["eng"]["rows"]["scen"]}'); adj = es(4, 'dcf', 'adj')
        dcf4 = f'IF({es(4,"dcf","evf")}+{adj}>0,({es(4,"dcf","evf")}+{adj})*(1-{dl}),{es(4,"dcf","evf")}+{adj})'
        W(RS, f'C{r0k}', f'={R["w_dcf"]}*{dcf4}+{R["w_cmp"]}*{es(4,"cmp","pre")}+{R["w_vc"]}*{es(4,"vc","pre")}+{R["w_perp"]}*{es(4,"perp","pre")}', CUR)
        RSR['stress_eq'] = r0k
    else:
        W(RS, f'B{r0k}', f'={bref}', fmt); W(RS, f'C{r0k}', f'={sref}', fmt)
    W(RS, f'D{r0k}', f'=C{r0k}-B{r0k}', fmt); W(RS, f'E{r0k}', f'=IF(B{r0k}<=0,"n.s.",C{r0k}/B{r0k}-1)' if fmt == CUR else '="pp"', PCT); r0k += 1
W(RS, f'A{r0k}', '¿Cumple covenant de caja en estrés?', bold=True)
W(RS, f'B{r0k}', f'={ESN}$B${SCEN[2]["eng"]["rows"]["m_ok"]}', bold=True); W(RS, f'C{r0k}', f'={ESN}$B${SCEN[4]["eng"]["rows"]["m_ok"]}', bold=True); RSR['stress_ok'] = r0k; r0k += 2

sec(RS, r0k, 'H. CONCLUSIÓN, ZONA DE NEGOCIACIÓN Y CONDICIONES PRECEDENTES', 9); r0k += 1
RSR['concl0'] = r0k
hdr(RS, r0k, ['Punto', 'Pre-money', 'Post-money', '% equity por el cheque', '', '', '', '', '']); r0k += 1
pts = [('Piso (conservador ponderado)', f'=G{RSR["concl"]}'), ('Base ★ (ponderado)', f'=E{RSR["concl"]}'), ('Techo (optimista ponderado)', f'=C{RSR["concl"]}')]
RSR['pts0'] = r0k
for lab, f in pts:
    W(RS, f'A{r0k}', lab, bold='Base' in lab); W(RS, f'B{r0k}', f, CUR, bold='Base' in lab)
    W(RS, f'C{r0k}', f'=B{r0k}+{R["monto"]}+{R["inkind"]}', CUR); W(RS, f'D{r0k}', f'=IF(B{r0k}<=0,"n.s. (pre ≤ 0: el cheque compra todo el valor)",{R["monto"]}/C{r0k})', PCT, bold=True); r0k += 1
W(RS, f'A{r0k}', 'Zona de negociación (pre-money)', bold=True, fill=F_KEY)
W(RS, f'B{r0k}', f'=MIN(B{RSR["pts0"]},B{RSR["pts0"]+1})', CUR, bold=True, fill=F_KEY); W(RS, f'C{r0k}', f'=B{RSR["pts0"]+1}', CUR, bold=True, fill=F_KEY)
W(RS, f'D{r0k}', f'=IF(C{r0k}<=0,"Pre-money base ≤ 0: no hay zona que pague valor por el concepto; negociar sweat equity con vesting / earn-out atado a cubiertos","Cheque de "&TEXT({R["monto"]},"$#,##0")&" → "&TEXT({R["monto"]}/(C{r0k}+{R["monto"]}),"0.0%")&" a "&IF(B{r0k}<=0,"100%",TEXT({R["monto"]}/(B{r0k}+{R["monto"]}),"0.0%"))&" del equity")', bold=True)
RSR['zone'] = r0k; r0k += 2
conc = [f'="• Rango justo de equity pre-money: "&TEXT(B{RSR["pts0"]},"$#,##0;-$#,##0")&" a "&TEXT(B{RSR["pts0"]+2},"$#,##0;-$#,##0")&"; base ★ "&TEXT(B{RSR["pts0"]+1},"$#,##0;-$#,##0")&IF(B{RSR["pts0"]+1}<=0,". Con los supuestos actuales el proyecto apenas cubre su costo de capital: el valor pre-money del concepto es ≈ 0 y el precio debe ser el capital invertido.",". Zona de negociación entre piso y base (no pagar el optimista).")',
        f'="• TIR del proyecto "&TEXT({q("P&L y FCF")}B{mr["irr"]},"0.0%")&" vs WACC "&TEXT({R["wacc"]},"0.0%")&"; break-even empresa "&TEXT({q("P&L y FCF")}B{mr["be"]},"0")&" cubiertos/día vs "&TEXT({q("P&L y FCF")}B{mr["ue_cov"]},"0")&" proyectados (colchón "&TEXT({q("P&L y FCF")}B{mr["be_cush"]},"0%")&")."',
        f'="• Estrés (−25% cubiertos, +15% food cost): equity concluido "&TEXT(C{RSR["stress_eq"]},"$#,##0")&" ("&TEXT(E{RSR["stress_eq"]},"0%")&"); covenant de caja en estrés: "&IF(C{RSR["stress_ok"]},"CUMPLE","NO CUMPLE → exigir tramos y reserva adicional")&"."',
        '="• Condición precedente 1: licencia de alcoholes, uso de suelo y dictamen INAH / imagen urbana emitidos antes del desembolso del tramo de obra."',
        '="• Condición precedente 2: contrato de arrendamiento firmado ≥ plazo modelado, con opción de renovación, tope de incremento (INPC) y derecho de preferencia."',
        '="• Condición precedente 3: validación de los supuestos naranja (POS / menú costeado / plantilla / cotizaciones de CapEx) por due diligence independiente; re-correr el modelo."']
for tx in conc: W(RS, f'A{r0k}', tx); r0k += 1

# ======================================================================================
# 8. RECONCILIACIÓN
# ======================================================================================
PLN = q('P&L y FCF'); DCN = q('DCF Valuación'); CPN = q('Comparables'); PPN = q('Perpetuidad'); CTN = q('Cap Table'); VCN = q('VC Method'); RSN = q('Resumen')
RC = wb.create_sheet('Reconciliación')
title(RC, 'RECONCILIACIÓN — cada número clave del Resumen → celda de origen', 'Columna "Coincide" compara el valor del Resumen contra la celda de origen.')
widths(RC, {'A': 52, 'B': 18, 'C': 34, 'D': 18, 'E': 12})
hdr(RC, 5, ['Número del Resumen', 'Valor en Resumen', 'Celda de origen', 'Valor en origen', 'Coincide'])
def unq(ref): return ref.replace('$', '')
recon = [('EV DCF vida finita — Base', f'Resumen!D7', es(2, 'dcf', 'evf')),
         ('EV DCF vida finita — Optimista', 'Resumen!B7', es(1, 'dcf', 'evf')),
         ('EV DCF vida finita — Conservador', 'Resumen!F7', es(3, 'dcf', 'evf')),
         ('EV DCF Gordon — Base', 'Resumen!D8', es(2, 'dcf', 'evg')),
         ('Equity comparables — Base', 'Resumen!E9', es(2, 'cmp', 'pre')),
         ('Post-money VC — Base', 'Resumen!D10', es(2, 'vc', 'post')),
         ('Equity perpetuidad — Base', 'Resumen!E11', es(2, 'perp', 'pre')),
         ('WACC base', f'Resumen!B{RSR["kpi_0"]}', es(2, 'dcf', 'w')),
         ('TIR proyecto', f'Resumen!B{RSR["kpi_1"]}', f'{PLN}B{mr["irr"]}'),
         ('VPN proyecto', f'Resumen!B{RSR["kpi_2"]}', f'{PLN}B{mr["npv"]}'),
         ('MOIC inversionista', f'Resumen!B{RSR["kpi_3"]}', f'{VCN}B{VR["moic"]}'),
         ('Payback', f'Resumen!B{RSR["kpi_4"]}', f'{PLN}B{mr["payback"]}'),
         ('EBITDA 4-wall año 2', f'Resumen!B{RSR["kpi_5"]}', esE(2, 'ebitda4', 2)),
         ('Prime cost año 2', f'Resumen!B{RSR["kpi_7"]}', esE(2, 'primep', 2)),
         ('Break-even empresa (cubiertos/día)', f'Resumen!B{RSR["ue_be"]}', f'{PLN}B{mr["be"]}'),
         ('Caja mínima año 1 — estrés', f'Resumen!C{RSR["stress0"]+5}', f'{ESN}$B${SCEN[4]["eng"]["rows"]["m_min"]}'),
         ('Pre-money concluido Base', f'Resumen!B{RSR["pts0"]+1}', f'{RSN}E{RSR["concl"]}'),
         ('Ke (Supuestos)', f'Supuestos!{unq(R["ke"].split("!")[1])}', R['ke'])]
for i, (lab, rsref, src) in enumerate(recon):
    rw = 6 + i
    sh, ad = rsref.split('!')
    W(RC, f'A{rw}', lab); W(RC, f'B{rw}', f'={q(sh)}{ad}', CUR if 'TIR' not in lab and 'WACC' not in lab and 'Prime' not in lab and 'Ke' not in lab else PCT2)
    W(RC, f'C{rw}', unq(src).replace("'", ''), color=GREY); W(RC, f'D{rw}', f'={src}', RC[f'B{rw}'].number_format)
    W(RC, f'E{rw}', f'=IFERROR(ABS(B{rw}-D{rw})<0.5,B{rw}=D{rw})', bold=True)
W(RC, f'A{6+len(recon)+1}', 'Todas coinciden', bold=True); W(RC, f'E{6+len(recon)+1}', f'=AND(E6:E{6+len(recon)-1})', bold=True, fill=F_KEY)
REC_ALL = f'{q("Reconciliación")}E{6+len(recon)+1}'
# ======================================================================================
# 7. CHECKS
# ======================================================================================
CK = wb.create_sheet('Checks')
title(CK, 'CHECKS — VALIDACIONES AUTOMÁTICAS (todas deben ser VERDADERO antes de entregar)', 'Tolerancia numérica: $1 MXN o 0.01pp.')
widths(CK, {'A': 6, 'B': 95, 'C': 14, 'D': 60})
hdr(CK, 5, ['#', 'Validación', 'Resultado', 'Detalle'])
act = R['scen']
def act_pick(blk, key):
    return f'CHOOSE({act},{es(1,blk,key)},{es(2,blk,key)},{es(3,blk,key)},{es(4,blk,key)})'
checks = [
    ('Cap table suma 100% — concluido, DCF, comparables y VC', f'=AND(ABS({CTN}C23-1)<0.0001,ABS({CTN}D23-1)<0.0001,ABS({CTN}E23-1)<0.0001,ABS({CTN}F23-1)<0.0001)', ''),
    ('Componentes in-kind = input in-kind (y % suman 100% si in-kind > 0)', f'=AND(ABS({CTN}D10-{R["inkind"]})<1,OR({R["inkind"]}=0,ABS({CTN}C10-1)<0.0001))', ''),
    ('Fuentes = usos (monto + caja = CapEx + preoperativos + depósito + reserva) y reserva ≥ 0',
     f'=AND(ABS({R["monto"]}+{R["cash0"]}-IF({R["gf"]}=1,{R["uses_ex"]},0)-{R["reserve"]})<1,{R["reserve"]}>=0)', ''),
    ('Reserva de caja ≥ covenant mínimo (escenario base)', f'={R["reserve"]}>={ESN}$B${SCEN[2]["eng"]["rows"]["m_req"]}', ''),
    ('Ponderación de métodos suma 100%', f'=ABS({R["w_sum"]}-1)<0.0001', ''),
    ('Motor de Escenarios (escenario activo) = P&L y FCF: ventas, EBITDA y FCF 10 años',
     f'=AND(ABS(SUM({PLN}C{er["rev"]}:L{er["rev"]})-CHOOSE({act},' + ','.join(f'SUM({ER(SCEN[s]["eng"],"rev")})' for s in range(1, 5)) + '))<1,'
     f'ABS(SUM({PLN}B{er["fcf"]}:L{er["fcf"]})-CHOOSE({act},' + ','.join(f'SUM({SCEN[s]["eng"]["P"]}$B${SCEN[s]["eng"]["rows"]["fcf"]}:$L${SCEN[s]["eng"]["rows"]["fcf"]})' for s in range(1, 5)) + '))<1)', ''),
    ('EV DCF hoja de método = bloque del escenario activo', f'=ABS({DCN}$D${DR["ev"]}-{act_pick("dcf","ev")})<1', ''),
    ('Equity comparables hoja de método = bloque del escenario activo', f'=ABS({CPN}$D${CR["pre"]}-{act_pick("cmp","pre")})<1', ''),
    ('Post-money VC hoja de método = bloque del escenario activo', f'=ABS({VCN}$D${VR["post"]}-{act_pick("vc","post")})<1', ''),
    ('Perpetuidad hoja de método = bloque del escenario activo', f'=ABS({PPN}$D${PR["pre"]}-{act_pick("perp","pre")})<1', ''),
    ('Sensibilidad DCF: celda central = EV del escenario activo', f'=ABS({DCN}{DR["sens_c"]}-{DCN}$D${DR["ev"]})<1', ''),
    ('Sensibilidad Perpetuidad: celda central = EV Gordon', f'=ABS({PPN}{PR["sens_c"]}-{PPN}$D${PR["vg"]})<1', ''),
    ('Resumen DCF base = hoja DCF (cuando escenario activo = Base y VT = vida finita)', f'=OR({act}<>2,{R["tv_method"]}<>1,ABS({RSN}D7-{DCN}$D${DR["ev"]})<1)', ''),
    ('Etiqueta de escenarios del Resumen contiene el WACC base vigente', f'=ISNUMBER(SEARCH(TEXT({es(2,"dcf","w")},"0.0%"),{RSN}A13))', ''),
    ('Etiqueta de escenarios del Resumen contiene el múltiplo base vigente', f'=ISNUMBER(SEARCH(TEXT(INDEX({R["mult"]},1,2),"0.0x"),{RSN}A13))', ''),
    ('Etiqueta del DCF contiene plazo y probabilidad de renovación vigentes', f'=AND(ISNUMBER(SEARCH(TEXT({R["term"]},"0")&" años",{DCN}A{DR["end"]+11})),ISNUMBER(SEARCH(TEXT({SC("prob",act)},"0%"),{DCN}A{DR["end"]+11})))', ''),
    ('FCF acumulado vs. payback: negativo antes del payback y ≥ 0 en el año de payback',
     f'=IF({PLN}B{mr["neg"]}>{N},TRUE,AND(INDEX({PLN}B{er["fcf_cum"]}:L{er["fcf_cum"]},1,{PLN}B{mr["neg"]})<0,INDEX({PLN}B{er["fcf_cum"]}:L{er["fcf_cum"]},1,{PLN}B{mr["neg"]}+1)>=0))', ''),
    ('Payback interpolado dentro del año correcto', f'=IF({PLN}B{mr["neg"]}>{N},TRUE,AND({PLN}B{mr["payback"]}>={PLN}B{mr["neg"]}-1,{PLN}B{mr["payback"]}<={PLN}B{mr["neg"]}))', ''),
    ('Ventas mensuales año 1 suman las ventas anuales del año 1', f'=ABS({PLN}O{er["m_rev"]}-{PLN}C{er["rev"]})<1', ''),
    ('Caja de apertura mensual = monto + caja + FCF año 0', f'=ABS({PLN}B{er["m_cash"]}-({R["monto"]}+{R["cash0"]}+{PLN}B{er["fcf"]}))<1', ''),
    ('EBITDA post-IFRS16 − pre = renta capitalizada (10 años)', f'=ABS(SUM({PLN}C{er["ebitda_post"]}:L{er["ebitda_post"]})-SUM({PLN}C{er["ebitda"]}:L{er["ebitda"]})-SUM({PLN}C{er["l_rent"]}:L{er["l_rent"]}))<1', ''),
    ('Pasivo por arrendamiento = 0 al vencer el plazo', f'=ABS(INDEX({PLN}C{er["l_bal"]}:L{er["l_bal"]},1,{R["term"]}))<1', ''),
    ('Plazo del arrendamiento ≤ horizonte del modelo (10 años)', f'=AND({R["term"]}>=1,{R["term"]}<={N})', ''),
    ('Estacionalidad normalizada promedia 1.0 y ramp-up ≤ 100%', f'=AND(ABS(AVERAGE({PLN}C{er["m_si"]}:N{er["m_si"]})-1)<0.0001,MAX({R["ramp"]})<=1)', ''),
    ('WACC > g en los 4 escenarios', '=AND(' + ','.join(f'{es(s,"dcf","w")}>{es(s,"dcf","g")}' for s in range(1, 5)) + ')', ''),
    ('Ke enfoque local vs. Fisher USD dentro de ±1.5pp (sin doble conteo de riesgo país)', f'=ABS({R["ke_gap"]})<=0.015', ''),
    ('D/E usado para re-apalancar ≈ D/E implícito (pasivo arrendamiento / equity concluido) ±30pp',
     f'=ABS({R["de_lease"]}-({PLN}B{er["l_bal"]}+{R["debt0"]})/MAX(1,{RSN}C{RSR["pts0"]+1}))<=0.30', f'="Implícito: "&TEXT(({PLN}B{er["l_bal"]}+{R["debt0"]})/MAX(1,{RSN}C{RSR["pts0"]+1}),"0%")'),
    ('Estacionalidad: suma de índices de entrada > 0 y 12 meses capturados', f'=AND(COUNT({R["season"]})=12,COUNT({R["ramp"]})=12)', ''),
    ('Valor concluido = Σ peso × método (reconciliación Resumen)', f'=ABS({RSN}E{RSR["concl"]}-SUMPRODUCT({RSN}E7:E11,{RSN}H7:H11))<1', ''),
    ('Sin errores en hojas de cálculo clave', f'=SUMPRODUCT(--ISERROR({PLN}A1:O{er["end"]+40}))+SUMPRODUCT(--ISERROR({ESN}A1:O{r_ if False else 2000}))+SUMPRODUCT(--ISERROR({RSN}A1:I120))=0', ''),
    ('Tabla de reconciliación: todos los números del Resumen coinciden con su origen', f'={REC_ALL}', ''),
    ('Comparables: al menos 1 observación en sets MX y TX', f'=AND({CPN}D{sr_+1}>=1,{CPN}E{sr_+1}>=1)', ''),
]
for i, (lab, f, det) in enumerate(checks):
    rw = 6 + i
    W(CK, f'A{rw}', i + 1, '0', color=BLACK); W(CK, f'B{rw}', lab); W(CK, f'C{rw}', f, bold=True)
    if det: W(CK, f'D{rw}', det, color=GREY)
CK_LAST = 6 + len(checks) - 1
W(CK, f'B{CK_LAST+2}', 'TODOS LOS CHECKS EN VERDADERO', bold=True); W(CK, f'C{CK_LAST+2}', f'=AND(C6:C{CK_LAST})', bold=True, fill=F_KEY)
from openpyxl.formatting.rule import CellIsRule
CK.conditional_formatting.add(f'C6:C{CK_LAST+2}', CellIsRule(operator='equal', formula=['FALSE'], fill=F_ALERT))

# Cap table fórmulas (dependen de Resumen)
for col, src in [('C', f'={RSN}E{RSR["concl"]}'), ('D', f'={RSN}E7'), ('E', f'={RSN}E9'), ('F', f'={RSN}E10')]:
    W(CT, f'{col}15', src, CUR); W(CT, f'{col}16', f'={R["monto"]}', CUR); W(CT, f'{col}17', f'={R["inkind"]}', CUR)
    W(CT, f'{col}18', f'=SUM({col}15:{col}17)', CUR, bold=True)
    for k, rr_ in [(20, 15), (21, 16), (22, 17)]: W(CT, f'{col}{k}', f'=IFERROR({col}{rr_}/{col}$18,0)', PCT)
    W(CT, f'{col}23', f'=SUM({col}20:{col}22)', PCT, bold=True)
W(CT, 'A24', 'Si el pre-money es negativo, el % de fundadores sale negativo: el cheque no se justifica a ese precio (señal para el comité).', italic=True, color=GREY)

# ======================================================================================
# 9. DATA REQUEST + OPEN ITEMS
# ======================================================================================
DQ = wb.create_sheet('Data Request')
title(DQ, 'DATA REQUEST Y OPEN ITEMS PARA EL COMITÉ', 'Sin estos documentos los supuestos naranja no pueden validarse. Prioridad A = bloquea la decisión.')
widths(DQ, {'A': 5, 'B': 48, 'C': 70, 'D': 40, 'E': 10, 'F': 18})
sec(DQ, 5, 'A. DATA REQUEST', 6)
hdr(DQ, 6, ['#', 'Documento', 'Detalle requerido', 'Valida (hoja / bloque)', 'Prioridad', 'Estatus'])
dreq = [('Estados financieros históricos', '3 años o desde la apertura: balance, resultados, flujo; dictaminados si existen. Balanza de comprobación mensual.', 'P&L y FCF / Supuestos D–E', 'A'),
        ('Ventas del POS diarias / mensuales', 'Cubiertos, ticket, mezcla alimentos/bebidas, por turno y día; ventas por canal (salón, delivery); % tarjeta.', 'Supuestos D (revenue build-up, estacionalidad)', 'A'),
        ('Menú con costeo (recetas estándar)', 'Costo por platillo y bebida, precio, popularidad (menu engineering); proveedores y condiciones.', 'Supuestos E (food & beverage cost)', 'A'),
        ('Layout y aforo', 'Planos, m², asientos por área (salón, terraza, barra), aforo de Protección Civil.', 'Supuestos D (asientos, m²)', 'A'),
        ('Contrato de arrendamiento', 'Renta, plazo, incrementos, depósito, opción de renovación, derecho de preferencia, mejoras.', 'Supuestos E / NIF D-5 / VT', 'A'),
        ('Plantilla y nómina', 'Puestos, sueldos, SBC, cuotas IMSS (SUA), ISN, rotación de personal, esquema de propinas.', 'Supuestos E (nómina y carga social)', 'A'),
        ('Deuda y caja', 'Créditos, arrendamientos financieros, saldos bancarios a la fecha de corte.', 'Supuestos C', 'A'),
        ('CapEx invertido / presupuesto de obra', 'Facturas o cotizaciones: obra, cocina, mobiliario, TI; presupuesto INAH-compatible.', 'Supuestos C (CapEx y vidas útiles)', 'A'),
        ('Cap table actual', 'Accionistas, % y clases de acciones, opciones, SAFEs/notas convertibles, acuerdos existentes.', 'Cap Table', 'A'),
        ('Licencias y permisos', 'Licencia de alcoholes, uso de suelo, PC, aviso de funcionamiento COFEPRIS, autorización INAH.', 'Riesgos / condiciones precedentes', 'A'),
        ('Monto a levantar y uso de fondos', 'Monto, tramos, calendario de desembolso, términos propuestos.', 'Supuestos C / Resumen', 'A'),
        ('Gastos operativos', '12 meses de energía, gas, agua, mantenimiento, marketing, seguros, honorarios.', 'Supuestos E', 'B'),
        ('Contratos de delivery y terminal', 'Comisiones Rappi / Uber Eats / DiDi; tarifa de TPV.', 'Supuestos E', 'B'),
        ('Datos turísticos OTEG', 'Serie mensual de ocupación hotelera y afluencia de Guanajuato capital (para calibrar estacionalidad).', 'Supuestos D (estacionalidad)', 'B')]
for i, (a, b, c, p_) in enumerate(dreq):
    rw = 7 + i
    W(DQ, f'A{rw}', i + 1, '0', color=BLACK); W(DQ, f'B{rw}', a, bold=True); W(DQ, f'C{rw}', b, wrap=True); W(DQ, f'D{rw}', c, color=GREY)
    W(DQ, f'E{rw}', p_, align='center', bold=p_ == 'A'); W(DQ, f'F{rw}', 'Pendiente', color='C65911', bold=True, fill=F_PEND)
r_ = 7 + len(dreq) + 1
sec(DQ, r_, 'B. OPEN ITEMS PARA EL COMITÉ — supuestos naranja (pendientes de validar) y datos de mercado no verificados', 6); r_ += 1
hdr(DQ, r_, ['#', 'Supuesto', 'Fuente / razón actual', 'Celda', 'Valor', '']); r_ += 1
mk = [('Múltiplos de comparables (ALSEA, CMRB, ARCO, QSR) — EV, EBITDA pre/post IFRS16, NTM, EV/Ventas', 'Red de la sesión bloqueó stockanalysis, BMV, SEC; cifras de snippets de búsqueda.', 'Supuestos!B (bloque I)'),
      ('Beta Damodaran Emerging Markets Restaurant/Dining (betaemerg.xls)', 'Se usó promedio EUA (verificado) / Global (secundaria).', R['bu'].split('!')[1]),
      ('Kroll CRSP decil 10 / 10z size premium vigente', 'De pago; se usó 5.0% (decil 10 histórico).', R['size'].split('!')[1]),
      ('Damodaran ctryprem jul-2026 (Mexico Baa3)', 'Ajuste CRP +0.65pp derivado de reporte secundario.', R['crp_adj'].split('!')[1]),
      ('M-Bono 10a en Banxico SIE a la fecha de corte', 'Cetesdirecto 9.25% (09-nov-2026).', R['mbono'].split('!')[1])]
n_ = 1
for a, b, c in mk:
    W(DQ, f'A{r_}', n_, '0', color=BLACK); W(DQ, f'B{r_}', a, wrap=True); W(DQ, f'C{r_}', b, color=GREY, wrap=True); W(DQ, f'D{r_}', c.replace('$', ''), color=GREY); r_ += 1; n_ += 1
for lab, ref, src in PENDING:
    W(DQ, f'A{r_}', n_, '0', color=BLACK); W(DQ, f'B{r_}', lab.strip(), wrap=True); W(DQ, f'C{r_}', src, color=GREY, wrap=True); W(DQ, f'D{r_}', ref, color=GREY)
    if ':' not in ref:
        W(DQ, f'E{r_}', f'={q("Supuestos")}{ref.split("!")[1]}')
    r_ += 1; n_ += 1

# ======================================================================================
# orden final de hojas
order = ['Supuestos', 'P&L y FCF', 'DCF Valuación', 'Comparables', 'Perpetuidad', 'Cap Table', 'VC Method', 'Resumen', 'Escenarios', 'Checks', 'Reconciliación', 'Data Request']
wb._sheets = [wb[n] for n in order]
for ws in wb:
    ws.sheet_view.showGridLines = False
wb.active = order.index('Resumen')
for ws in wb: ws.sheet_view.tabSelected = ws.title == 'Resumen'
wb.save(OUT)
print('saved', OUT, 'pending', len(PENDING))
