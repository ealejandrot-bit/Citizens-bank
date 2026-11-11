import openpyxl, sys
from openpyxl.styles import Font, PatternFill, Alignment
src, out = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(src)
F = 'Arial'; BLUE = '0000FF'; GREEN = '008000'; GREY = '595959'; NAVY = '1F3864'
CUR = '$#,##0;($#,##0);"-"'; PCT = '0.0%;(0.0%);"-"'; MULT = '0.0"x"'; DEC = '0.000'
HDR = PatternFill('solid', fgColor=NAVY); SEC = PatternFill('solid', fgColor='D9E1F2')
YEL = PatternFill('solid', fgColor='FFFF00'); KEY = PatternFill('solid', fgColor='E2EFDA')

def st(c, v=None, fmt=None, bold=False, color=None, fill=None, size=10, italic=False, wrap=False):
    if v is not None: c.value = v
    if color is None:
        if isinstance(v, str) and v.startswith('='): color = GREEN if '!' in v else '000000'
        elif isinstance(v, (int, float)) and not isinstance(v, bool): color = BLUE
        else: color = '000000'
    c.font = Font(name=F, bold=bold, color=color, size=size, italic=italic)
    if fmt: c.number_format = fmt
    if fill: c.fill = fill
    if wrap: c.alignment = Alignment(wrap_text=True, vertical='top')
    return c
def title(ws, t, sub):
    st(ws['A1'], t, bold=True, size=14, color=NAVY); st(ws['A2'], sub, italic=True, color=GREY)
    st(ws['A3'], 'Azul = supuesto editable (fondo amarillo = clave) · negro = fórmula · verde = vínculo a otra hoja', italic=True, color=GREY, size=8)
def section(ws, r, t, n=8):
    for c in range(1, n + 1): ws.cell(r, c).fill = SEC
    st(ws.cell(r, 1), t, bold=True, fill=SEC)
def hdr(ws, r, labels):
    for j, h in enumerate(labels):
        c = ws.cell(r, 1 + j); c.value = h; c.font = Font(name=F, bold=True, color='FFFFFF'); c.fill = HDR
        c.alignment = Alignment(horizontal='center', wrap_text=True)
def row(ws, r, label, v, fmt=CUR, note=None, bold=False, fill=None, col=2):
    st(ws.cell(r, 1), label, bold=bold); st(ws.cell(r, col), v, fmt, bold=bold, fill=fill)
    if note: st(ws.cell(r, 8), note, italic=True, color=GREY)

# ---------------- Supuestos ----------------
S = wb.create_sheet('Supuestos')
title(S, 'Dos Chingones — Supuestos generales', 'Guanajuato, Gto. Cifras en MXN nominales. Corte de datos: septiembre 2026; mercado: 11-nov-2026.')
R = {}
def inp(r, key, label, v, fmt, note, key_fill=False):
    st(S.cell(r, 1), label); st(S.cell(r, 2), v, fmt, fill=YEL if key_fill else None); st(S.cell(r, 3), note, italic=True, color=GREY)
    R[key] = f'Supuestos!$B${r}'
hdr(S, 4, ['Variable', 'Valor', 'Fuente / razón'])
section(S, 5, 'A. Identificación', 3)
inp(6, 'name', 'Nombre', 'Dos Chingones', None, 'Unidades: Garden y Presa.')
inp(7, 'loc', 'Ubicación', 'Guanajuato, Gto.', None, '')
inp(8, 'shares', 'Acciones totales (1 acción = 1%)', 100, '#,##0', 'Supuesto: no hay número de acciones en el archivo; % de socios de la hoja Original.', True)
section(S, 10, 'B. Inflación y crecimiento', 3)
inp(11, 'inf', 'Inflación de largo plazo México', 0.04, PCT, 'Instrucción del usuario (4.0%). Ref.: meta Banxico 3% ±1; INPC oct-2026 3.75%.', True)
inp(12, 'g_real', 'Crecimiento real a perpetuidad', 0.005, PCT, 'Instrucción del usuario: crecimiento real de largo plazo 0.5%–1.0% sobre inflación.')
st(S['A13'], 'g terminal nominal = (1+inflación)·(1+g real) − 1'); st(S['B13'], '=(1+B11)*(1+B12)-1', PCT, bold=True); R['g'] = 'Supuestos!$B$13'
section(S, 15, 'C. Tasa de descuento (Ke) — mismo enfoque que el modelo IC', 3)
items = [('mbono', 'M-Bono 10 años', 0.0925, PCT, 'Cetesdirecto, 09-nov-2026 (fuente secundaria; verificar en Banxico SIE).'),
         ('ds', 'Default spread soberano México (ajustado a Baa3)', 0.0205, PCT, 'Damodaran ene-2026 1.62% + ajuste por downgrade Moody\'s may-2026.'),
         (None, 'Rf local libre de default = M-Bono − default spread', '=B16-B17', PCT, 'Evita contar dos veces el riesgo país.'),
         ('bu', 'β desapalancada Restaurant/Dining (promedio EUA / Global)', 0.677, DEC, 'Damodaran ene-2026: EUA 0.739 (Hamada), Global 0.615.'),
         ('de', 'D/E de mercado de la industria (incluye arrendamientos)', 0.27, PCT, 'Damodaran Restaurant/Dining EUA 27.2%. Sin contrato de renta de las unidades no se usa D/E propio.'),
         ('t', 'ISR', 0.30, PCT, 'LISR art. 9.'),
         (None, 'β re-apalancada = βU·(1+(1−t)·D/E)', '=B19*(1+(1-B21)*B20)', DEC, 'Hamada.'),
         ('erp', 'ERP total México (maduro 4.20% + CRP 3.11%)', 0.0731, PCT, 'Damodaran (CRP ene-2026 2.46% + 0.65pp por Baa3; fuente secundaria).'),
         ('size', 'Prima por tamaño', 0.05, PCT, 'Kroll CRSP decil 10, histórico ~4.7–5.6% (no verificado).'),
         ('csrp', 'Riesgo específico (CSRP)', 0.035, PCT, 'Persona clave 1.0% · concentración turística 1.0% · historial corto 0.5% · regulatorio Centro Histórico 0.5% · seguridad 0.5%.')]
for i, (k, lab, v, fmt, note) in enumerate(items):
    r = 16 + i; st(S.cell(r, 1), lab); st(S.cell(r, 2), v, fmt); st(S.cell(r, 3), note, italic=True, color=GREY)
    if k: R[k] = f'Supuestos!$B${r}'
st(S['A26'], 'Ke = Rf local + βL × ERP + tamaño + CSRP', bold=True)
st(S['B26'], '=B18+B22*B23+B24+B25', PCT, bold=True, fill=KEY); R['ke'] = 'Supuestos!$B$26'
st(S['C26'], 'La utilidad neta ya es flujo al accionista (sin deuda financiera conocida) → se descuenta a Ke.', italic=True, color=GREY)
section(S, 28, 'D. Ponderación de métodos e iliquidez', 3)
inp(29, 'w_dcf', 'Peso DCF (proyección de ingresos × margen)', 0.5, PCT, 'Captura tendencia de ventas y margen.')
st(S['A30'], 'Peso múltiplo P/U'); st(S['B30'], '=1-B29', PCT); R['w_mult'] = 'Supuestos!$B$30'
inp(31, 'dlom', 'Descuento por falta de liquidez (DLOM)', 0.0, PCT, 'Precio de referencia entre socios = 0%. Si es venta a un tercero minoritario, usar 20–30% (estudios restricted stock).', True)

# ---------------- Histórico ----------------
H = wb.create_sheet('Histórico')
title(H, 'Dos Chingones — Análisis histórico (base de las proyecciones)', 'Ventanas de 12 meses que terminan en septiembre. Fuente: hoja Original (columnas P–S).')
hdr(H, 5, ['Concepto', 'Oct-23 – Sep-24', 'Oct-24 – Sep-25', 'Oct-25 – Sep-26 (LTM)', 'Var. último año', 'CAGR 2 años', '', 'Nota'])
win = [(5, 16), (17, 28), (29, 40)]
lines = [('Ingresos Garden', 'P'), ('Utilidad neta Garden', 'R'), ('Ingresos Presa', 'Q'), ('Utilidad neta Presa', 'S')]
HR = {}
for i, (lab, col) in enumerate(lines):
    r = 6 + i; st(H.cell(r, 1), lab)
    for j, (a, b) in enumerate(win):
        f = f'=SUM(Original!{col}{a}:{col}{b})'
        if col == 'S' and j == 0: st(H.cell(r, 2 + j), 'N/D', color=GREY); continue
        if col == 'S' and j == 1: f = f'=SUM(Original!S19:S28)*12/10'
        st(H.cell(r, 2 + j), f, CUR)
    st(H.cell(r, 5), f'=IFERROR(D{r}/C{r}-1,"-")', PCT)
    st(H.cell(r, 6), f'=IFERROR((D{r}/B{r})^(1/2)-1,"-")', PCT)
    HR[col] = r
st(H['H9'], 'Presa sólo tiene utilidad desde dic-2024: ventana previa = 10 meses anualizados.', italic=True, color=GREY)
st(H['H7'], 'Incluye mar-2025 con posible doble conteo de $3,915 (R22) y abr-2025 promediado.', italic=True, color=GREY)
section(H, 11, 'Márgenes netos (utilidad neta / ingresos)', 8)
hdr(H, 12, ['Margen', 'Histórico completo', 'Oct-24 – Sep-25', 'LTM', 'Últimos 6 meses', 'Últimos 3 meses', '', 'Nota'])
st(H['A13'], 'Garden')
st(H['B13'], '=SUM(Original!R4:R40)/SUM(Original!P4:P40)', PCT); st(H['C13'], '=C7/C6', PCT); st(H['D13'], '=D7/D6', PCT)
st(H['E13'], '=SUM(Original!R35:R40)/SUM(Original!P35:P40)', PCT); st(H['F13'], '=SUM(Original!R38:R40)/SUM(Original!P38:P40)', PCT)
st(H['H13'], 'Histórico = sep-2023 a sep-2026. Margen sep-2026: 3.9% (alerta).', italic=True, color=GREY)
st(H['A14'], 'Presa')
st(H['B14'], '=SUM(Original!S19:S40)/SUM(Original!Q19:Q40)', PCT); st(H['C14'], '=SUM(Original!S19:S28)/SUM(Original!Q19:Q28)', PCT); st(H['D14'], '=D9/D8', PCT)
st(H['E14'], '=SUM(Original!S35:S40)/SUM(Original!Q35:Q40)', PCT); st(H['F14'], '=SUM(Original!S38:S40)/SUM(Original!Q38:Q40)', PCT)
st(H['H14'], 'Histórico = dic-2024 a sep-2026. Margen sep-2026: 0.1% (alerta).', italic=True, color=GREY)
section(H, 16, 'Lectura', 8)
for i, tx in enumerate(['="• Garden: ventas "&TEXT(E6,"0.0%")&" en el último año (real ≈ "&TEXT((1+E6)/(1+Supuestos!B11)-1,"0.0%")&"); margen de "&TEXT(C13,"0.0%")&" a "&TEXT(D13,"0.0%")&". La utilidad cae más que las ventas → presión de costos."',
                        '="• Presa: ventas "&TEXT(E8,"0.0%")&" en el último año; margen LTM "&TEXT(D14,"0.0%")&" (vs "&TEXT(C14,"0.0%")&" el año previo)."',
                        '="• La v1 proyectaba la utilidad LTM creciendo 4% sin ver ventas ni margen. La v2 proyecta ingresos (tendencia → inflación) × margen por escenario."']):
    st(H.cell(17 + i, 1), tx)
for c, w in zip('ABCDEFGH', [34, 17, 17, 20, 15, 13, 3, 70]): H.column_dimensions[c].width = w

# ---------------- Unidades ----------------
SCN = ['Optimista', 'Base ★', 'Conservador']
def unidad(name, rev_r, ni_r, mrow):
    ws = wb.create_sheet(f'Valuación {name}')
    title(ws, f'Dos Chingones — Valuación {name}', 'Proyección 5 años: ingresos × margen neto. DCF (Ke) + múltiplo P/U. MXN.')
    section(ws, 5, '1. Supuestos de la unidad')
    row(ws, 6, 'Ingresos LTM (oct-2025 – sep-2026)', f'=Histórico!D{rev_r}', note='Base de proyección.')
    row(ws, 7, 'Utilidad neta LTM', f'=Histórico!D{ni_r}')
    row(ws, 8, 'Crecimiento nominal de ingresos año 1 (CAGR 2 años)', f'=Histórico!F{rev_r}', PCT, note='Tendencia real de la unidad; converge a la inflación en el año 3.')
    row(ws, 9, 'Crecimiento nominal años 3–5 = inflación LP + g real', f'={R["g"]}', PCT)
    row(ws, 10, 'Múltiplo P/U (precio / utilidad neta)', 4.0, MULT, note='Negocios privados pequeños de hospitalidad en México: 3–5x; consistente con 6.6x EV/EBITDA de mercado −40% por tamaño.')
    st(ws['B10'], fill=YEL)
    hdr(ws, 12, ['Margen neto por escenario', 'Optimista', 'Base ★', 'Conservador', '', '', '', 'Razón'])
    st(ws['A13'], 'Margen neto aplicado')
    st(ws['B13'], f'=Histórico!B{mrow}', PCT); st(ws['C13'], f'=Histórico!D{mrow}', PCT); st(ws['D13'], f'=Histórico!E{mrow}', PCT)
    st(ws['H13'], 'Optimista = regresa al promedio histórico · Base = se mantiene el LTM · Conservador = se queda en el de los últimos 6 meses.', italic=True, color=GREY)
    section(ws, 15, '2. Proyección de ingresos y utilidad neta')
    hdr(ws, 16, ['Concepto', 'LTM (año 0)', 'Año 1', 'Año 2', 'Año 3', 'Año 4', 'Año 5', 'Nota'])
    st(ws['A17'], 'Crecimiento de ingresos')
    st(ws['C17'], '=$B$8', PCT); st(ws['D17'], '=($B$8+$B$9)/2', PCT)
    for c in 'EFG': st(ws[f'{c}17'], '=$B$9', PCT)
    st(ws['H17'], 'Año 2 = punto medio entre tendencia e inflación.', italic=True, color=GREY)
    st(ws['A18'], 'Ingresos', bold=True); st(ws['B18'], '=B6', CUR, bold=True)
    for p, c in zip('BCDEF', 'CDEFG'): st(ws[f'{c}18'], f'={p}18*(1+{c}17)', CUR, bold=True)
    st(ws['A19'], 't'); [st(ws[f'{c}19'], f'={p}19+1', '0') for p, c in zip('BCDEF', 'CDEFG')]; st(ws['B19'], 0, '0', color='000000')
    st(ws['A20'], 'Factor de descuento 1/(1+Ke)^t'); [st(ws[f'{c}20'], f'=1/(1+{R["ke"]})^{c}19', '0.0000') for c in 'CDEFG']
    for i, sname in enumerate(SCN):
        r = 22 + i * 3; mc = 'BCD'[i]
        st(ws[f'A{r}'], f'Utilidad neta — {sname}', bold=i == 1)
        st(ws[f'B{r}'], f'=B18*${mc}$13', CUR)
        for c in 'CDEFG': st(ws[f'{c}{r}'], f'={c}18*${mc}$13', CUR, bold=i == 1)
        st(ws[f'A{r+1}'], f'  VP utilidad neta — {sname}')
        for c in 'CDEFG': st(ws[f'{c}{r+1}'], f'={c}{r}*{c}20', CUR)
    section(ws, 32, '3. Valuación por escenario')
    hdr(ws, 33, ['Concepto', 'Optimista', 'Base ★', 'Conservador', '', '', '', 'Nota'])
    labels = ['Σ VP utilidad neta años 1–5', 'Valor terminal (Gordon) al año 5', 'VP valor terminal', 'Valor DCF',
              'Valor por múltiplo (P/U × utilidad año 0 del escenario)', 'Valor ponderado (DCF / múltiplo)', 'Valor después de DLOM',
              'Valor por acción', '% del DCF que viene del valor terminal']
    for k, lab in enumerate(labels): st(ws.cell(34 + k, 1), lab, bold=k in (5, 7))
    for i in range(3):
        c = 'BCD'[i]; r = 22 + i * 3
        st(ws[f'{c}34'], f'=SUM(C{r+1}:G{r+1})', CUR)
        st(ws[f'{c}35'], f'=G{r}*(1+{R["g"]})/({R["ke"]}-{R["g"]})', CUR)
        st(ws[f'{c}36'], f'={c}35*G20', CUR)
        st(ws[f'{c}37'], f'={c}34+{c}36', CUR)
        st(ws[f'{c}38'], f'=B{r}*$B$10', CUR)
        st(ws[f'{c}39'], f'={R["w_dcf"]}*{c}37+{R["w_mult"]}*{c}38', CUR, bold=True, fill=KEY if i == 1 else None)
        st(ws[f'{c}40'], f'={c}39*(1-{R["dlom"]})', CUR)
        st(ws[f'{c}41'], f'={c}40/{R["shares"]}', CUR, bold=True, fill=YEL if i == 1 else None)
        st(ws[f'{c}42'], f'=IFERROR({c}36/{c}37,0)', PCT)
    st(ws['H35'], 'Utilidad año 5 × (1+g) / (Ke − g).', italic=True, color=GREY)
    st(ws['H38'], 'Utilidad año 0 = ingresos LTM × margen del escenario.', italic=True, color=GREY)
    for col, w in zip('ABCDEFGH', [52, 16, 16, 16, 16, 16, 16, 70]): ws.column_dimensions[col].width = w
    ws.freeze_panes = 'B4'
    return ws
unidad('Garden', 6, 7, 13)
unidad('Presa', 8, 9, 14)

# ---------------- Total ----------------
T = wb.create_sheet('Valuación Total')
title(T, 'Dos Chingones — Valuación total y valor por acción (v2)', '="Guanajuato, Gto. · "&TEXT(Supuestos!B8,"0")&" acciones · Ke "&TEXT(Supuestos!B26,"0.0%")&" · inflación LP "&TEXT(Supuestos!B11,"0.0%")&" · DLOM "&TEXT(Supuestos!B31,"0%")')
section(T, 5, '1. Valor por acción', 7)
hdr(T, 6, ['Unidad', 'Valor por acción Base ★', 'Mínimo (Conservador)', 'Máximo (Optimista)', 'Valor total Base ★', 'Utilidad neta LTM', 'Valor / utilidad LTM'])
for r, u in ((7, 'Garden'), (8, 'Presa')):
    qn = f"'Valuación {u}'"
    st(T[f'A{r}'], u)
    st(T[f'B{r}'], f'={qn}!C41', CUR, bold=True); st(T[f'C{r}'], f'={qn}!D41', CUR); st(T[f'D{r}'], f'={qn}!B41', CUR)
    st(T[f'E{r}'], f'={qn}!C40', CUR); st(T[f'F{r}'], f'={qn}!B7', CUR); st(T[f'G{r}'], f'=IFERROR(E{r}/F{r},0)', MULT)
st(T['A9'], 'TOTAL DOS CHINGONES', bold=True, fill=KEY)
for c in 'BCDEF': st(T[f'{c}9'], f'=SUM({c}7:{c}8)', CUR, bold=True, fill=KEY)
st(T['G9'], '=IFERROR(E9/F9,0)', MULT, bold=True, fill=KEY)
section(T, 11, '2. Valor por socio (Base ★)', 7)
hdr(T, 12, ['Socio', '% participación', 'Acciones', 'Valor Garden', 'Valor Presa', 'Valor total', 'Rango total'])
socios = [('Alma', 0.01), ('Anabel', 0.02), ('Alejandro', 0.02), ('María Ester', 0.02), ('Adrián', 0.03), ('Alma Galland', 0.04), ('José Luis', 0.04), ('Resto de los socios', 0.82)]
for i, (n, p) in enumerate(socios):
    r = 13 + i; st(T[f'A{r}'], n); st(T[f'B{r}'], p, PCT)
    st(T[f'C{r}'], f'=B{r}*Supuestos!$B$8', '#,##0.0'); st(T[f'D{r}'], f'=B{r}*$E$7', CUR); st(T[f'E{r}'], f'=B{r}*$E$8', CUR); st(T[f'F{r}'], f'=D{r}+E{r}', CUR)
    st(T[f'G{r}'], f'=TEXT(C{r}*$C$9,"$#,##0")&" – "&TEXT(C{r}*$D$9,"$#,##0")')
st(T['A21'], 'Total', bold=True)
for c, fmt in zip('BCDEF', [PCT, '#,##0.0', CUR, CUR, CUR]): st(T[f'{c}21'], f'=SUM({c}13:{c}20)', fmt, bold=True)
section(T, 23, '3. Qué cambió vs. v1 y lectura', 7)
notes = ['="• v1: utilidad LTM × 4% de crecimiento, Ke 21.5% genérico. v2: ingresos con tendencia real de cada unidad (CAGR 2 años) que converge a inflación 4.0%, × margen neto por escenario; Ke con build-up (Damodaran/M-Bono) = "&TEXT(Supuestos!B26,"0.0%")&"."',
         '="• Garden: CAGR de ventas "&TEXT(Histórico!F6,"0.0%")&"; margen LTM "&TEXT(Histórico!D13,"0.0%")&" vs histórico "&TEXT(Histórico!B13,"0.0%")&" y últimos 6 meses "&TEXT(Histórico!E13,"0.0%")&"."',
         '="• Presa: CAGR de ventas "&TEXT(Histórico!F8,"0.0%")&" (año 1 sigue cayendo); margen LTM "&TEXT(Histórico!D14,"0.0%")&", últimos 6 meses "&TEXT(Histórico!E14,"0.0%")&"."',
         '="• Rango = escenarios de margen (no de método). El mínimo supone que el deterioro de los últimos 6 meses se vuelve permanente."',
         '• Utilidad neta = flujo para los socios (sin deuda conocida, CapEx ≈ depreciación). Sin estados financieros no se puede separar EBITDA, D&A ni renta.']
for i, tx in enumerate(notes): st(T.cell(24 + i, 1), tx)
for col, w in zip('ABCDEFG', [30, 20, 20, 20, 18, 18, 24]): T.column_dimensions[col].width = w

# Checks rápidos
C = wb.create_sheet('Checks')
title(C, 'Checks', 'Deben ser VERDADERO.')
chk = [('% de socios suma 100%', "=ABS('Valuación Total'!B21-1)<0.0001"),
       ('Ke > g terminal', f'={R["ke"]}>{R["g"]}'),
       ('Total = Garden + Presa (valor base)', "=ABS('Valuación Total'!E9-'Valuación Garden'!C40-'Valuación Presa'!C40)<1"),
       ('Mínimo ≤ Base ≤ Máximo por acción (total)', "=AND('Valuación Total'!C9<='Valuación Total'!B9,'Valuación Total'!B9<='Valuación Total'!D9)"),
       ('Ingresos LTM coinciden con hoja Original', "=ABS('Valuación Garden'!B6-SUM(Original!P29:P40))+ABS('Valuación Presa'!B6-SUM(Original!Q29:Q40))<1"),
       ('Pesos de métodos suman 100%', '=ABS(Supuestos!B29+Supuestos!B30-1)<0.0001')]
for i, (lab, f) in enumerate(chk):
    st(C.cell(5 + i, 1), lab); st(C.cell(5 + i, 2), f, bold=True)
st(C.cell(12, 1), 'TODOS', bold=True); st(C.cell(12, 2), '=AND(B5:B10)', bold=True, fill=KEY)
C.column_dimensions['A'].width = 50

order = ['Valuación Total', 'Valuación Garden', 'Valuación Presa', 'Histórico', 'Supuestos', 'Checks', 'Original', 'Sheet1']
wb._sheets = [wb[n] for n in order]; wb.active = 0
for ws in wb: ws.sheet_view.tabSelected = ws.title == 'Valuación Total'
wb.save(out)
