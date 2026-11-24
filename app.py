# -*- coding: utf-8 -*-
# Gestor de Morbilidad - Willian Almenar
# SISPRO / EPI12 / EPI15  +  Motor SIS-03/PRO (tabulador diario) + Foto->IA
import streamlit as st
import pandas as pd
import numpy as np
import re, calendar, base64
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Gestor de Morbilidad - Willian Almenar", layout="wide")

# ============ ESTILOS ============
st.markdown("""
    <style>
    .main-header {background-color:#1E3A5F;padding:1rem;border-radius:10px;color:white;text-align:center;}
    .success-box {background-color:#d4edda;padding:1rem;border-radius:5px;border-left:5px solid #28a745;}
    .warning-box {background-color:#fff3cd;padding:1rem;border-radius:5px;border-left:5px solid #ffc107;}
    .danger-box {background-color:#f8d7da;padding:1rem;border-radius:5px;border-left:5px solid #dc3545;}
    .info-box {background-color:#d1ecf1;padding:1rem;border-radius:5px;border-left:5px solid #17a2b8;}
    .match-box {background-color:#e8f5e9;padding:1rem;border-radius:10px;border-left:5px solid #2e7d32;margin-bottom:1rem;}
    .discrepancy-box {background-color:#fff3e0;padding:1rem;border-radius:10px;border-left:5px solid #ff9800;margin-bottom:1rem;}
    .total-box {background-color:#e8f5e9;padding:1rem;border-radius:10px;border-left:5px solid #2e7d32;margin:1rem 0;}
    .mes-box {background-color:#fff3e0;padding:1rem;border-radius:10px;margin:0.5rem 0;border:2px solid #ff9800;}
    .semana-box {background-color:#f3e5f5;padding:0.8rem;border-radius:8px;margin:0.5rem 0;border-left:4px solid #7b1fa2;}
    .grupo-box {background-color:#e3f2fd;padding:0.5rem 1rem;border-radius:5px;margin:0.2rem 0;border-left:3px solid #1976d2;}
    .reporte-box {background-color:#fce4ec;padding:1rem;border-radius:10px;border-left:5px solid #c62828;margin:1rem 0;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>Gestor de Morbilidad - Validación de Reportes</h1><p>Willian Almenar</p></div>', unsafe_allow_html=True)
st.markdown("---")

# ============ DICCIONARIOS Y FUNCIONES BASE ============
EXPECTED_COLUMNS = {
    "SISPRO": ["CODIGO_EPS","NOMBRE_EPS","TIPO_DOCUMENTO","NUMERO_DOCUMENTO","NOMBRE_PACIENTE","APELLIDO_PACIENTE",
               "FECHA_ATENCION","CODIGO_DIAGNOSTICO","DESCRIPCION_DIAGNOSTICO","CODIGO_CIE10","SEXO","EDAD","MUNICIPIO","DEPARTAMENTO"],
    "EPI12": ["CODIGO_EPS","NOMBRE_EPS","TIPO_DOCUMENTO","NUMERO_DOCUMENTO","NOMBRE_PACIENTE","APELLIDO_PACIENTE",
              "FECHA_ATENCION","CODIGO_DIAGNOSTICO","DESCRIPCION_DIAGNOSTICO","CODIGO_CIE10","PROCEDIMIENTO",
              "DESCRIPCION_PROCEDIMIENTO","SEXO","EDAD","ATENCION_AMBULATORIA","EMERGENCIA"],
    "EPI15": ["CODIGO_EPS","NOMBRE_EPS","TIPO_DOCUMENTO","NUMERO_DOCUMENTO","NOMBRE_PACIENTE","APELLIDO_PACIENTE",
              "FECHA_ATENCION","CODIGO_DIAGNOSTICO","DESCRIPCION_DIAGNOSTICO","CODIGO_CIE10","SERVICIO","SEXO","EDAD","MUNICIPIO","CAUSA_CONSULTA"]
}
GRUPOS_SISPRO = {
    'Total Lactantes y Pre-escolares': (0, 5),
    'Total Escolares': (6, 11),
    'Total Adolescentes de 12 a Menores de 19 Años': (12, 18),
    'Total Adultos': (19, 59),
    'Total de la Tercera Edad': (60, 150)
}

GRUPOS_ETARIOS = {
    '0-4 anos': (0,4),'5-9 anos': (5,9),'10-14 anos': (10,14),'15-19 anos': (15,19),'20-24 anos': (20,24),
    '25-29 anos': (25,29),'30-34 anos': (30,34),'35-39 anos': (35,39),'40-44 anos': (40,44),'45-49 anos': (45,49),
    '50-54 anos': (50,54),'55-59 anos': (55,59),'60-64 anos': (60,64),'65+ anos': (65,150)
}

def obtener_semana_mes(fecha):
    if pd.isna(fecha): return 0
    dia = fecha.day
    if dia <= 7: return 1
    elif dia <= 14: return 2
    elif dia <= 21: return 3
    elif dia <= 28: return 4
    return 5

def asignar_grupo_etario(edad):
    if pd.isna(edad): return 'Sin dato'
    try:
        edad = float(edad)
        for grupo,(mn,mx) in GRUPOS_ETARIOS.items():
            if mn <= edad <= mx: return grupo
        return 'Sin dato'
    except: return 'Sin dato'

def asignar_grupo_sispro(edad):
    if pd.isna(edad): return 'Sin dato'
    try:
        edad = float(edad)
        for grupo,(mn,mx) in GRUPOS_SISPRO.items():
            if mn <= edad <= mx: return grupo
        return 'Sin dato'
    except: return 'Sin dato'

def normalizar_identificacion(df):
    if 'NUMERO_DOCUMENTO' in df.columns: df['IDENTIFICACION'] = df['NUMERO_DOCUMENTO'].astype(str).str.strip()
    elif 'DOCUMENTO' in df.columns: df['IDENTIFICACION'] = df['DOCUMENTO'].astype(str).str.strip()
    else: df['IDENTIFICACION'] = df.index.astype(str)
    return df

def detectar_columna_fecha(df):
    posibles = ['FECHA_ATENCION','FECHA ATENCION','FECHADEATENCION','FECHA_CONSULTA','FECHA CONSULTA','FECHACONSULTA',
                'FECHA_DE_ATENCION','FECHA_DE_CONSULTA','FECHA_REGISTRO','FECHA REGISTRO','FECHAREGISTRO','FECHA','FECH','DATE','FECHA_DIA']
    for col in df.columns:
        cu = col.upper().strip()
        for f in posibles:
            if cu == f or cu == f.replace(' ','_') or cu == f.replace(' ',''): return col
    for col in df.columns:
        if 'FECHA' in col.upper() or 'DATE' in col.upper(): return col
    return None

def convertir_fechas(df, columna_fecha):
    if columna_fecha is None: return None, "No se encontró columna de fecha"
    try:
        if pd.api.types.is_numeric_dtype(df[columna_fecha]):
            fechas = pd.to_datetime(df[columna_fecha], unit='D', origin='1899-12-30', errors='coerce')
            if fechas.notna().sum() > 0: return fechas, "Formato Excel (fecha serial)"
    except: pass
    formatos = ['%d/%m/%Y','%m/%d/%Y','%Y-%m-%d','%d-%m-%Y','%d.%m.%Y','%Y/%m/%d','%d/%m/%y','%m/%d/%y',
                '%Y-%m-%d %H:%M:%S','%d/%m/%Y %H:%M:%S']
    for formato in formatos:
        try:
            fechas = pd.to_datetime(df[columna_fecha], format=formato, errors='coerce')
            if fechas.notna().sum() > 0: return fechas, f"Formato detectado: {formato}"
        except: continue
    try:
        fechas = pd.to_datetime(df[columna_fecha], errors='coerce')
        if fechas.notna().sum() > 0: return fechas, "Conversion automatica"
    except: pass
    return None, "No se pudieron convertir las fechas"

def analizar_archivo(file, tipo_archivo, columna_fecha_seleccionada=None):
    if file is None: return None, "No se ha subido ningun archivo"
    try:
        if file.name.endswith('.xls'): df = pd.read_excel(file, engine='xlrd', header=0)
        else: df = pd.read_excel(file, engine='openpyxl', header=0)
        df.columns = df.columns.str.strip().str.upper()
        info = {"filas": df.shape[0], "columnas": df.shape[1], "nombres_columnas": list(df.columns),
                "fecha_carga": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        df = normalizar_identificacion(df)
        if 'EDAD' in df.columns:
            df['GRUPO_ETARIO'] = df['EDAD'].apply(asignar_grupo_etario)
            df['GRUPO_SISPRO'] = df['EDAD'].apply(asignar_grupo_sispro)
        columna_fecha = columna_fecha_seleccionada if columna_fecha_seleccionada else detectar_columna_fecha(df)
        info["columna_fecha_detectada"] = columna_fecha
        if columna_fecha:
            fechas, mensaje = convertir_fechas(df, columna_fecha)
            if fechas is not None:
                df['FECHA_ATENCION'] = fechas
                df['ANO'] = df['FECHA_ATENCION'].dt.year
                df['MES'] = df['FECHA_ATENCION'].dt.month
                df['SEMANA_ANUAL'] = df['FECHA_ATENCION'].dt.isocalendar().week
                df['SEMANA'] = df['FECHA_ATENCION'].apply(obtener_semana_mes)
                info["fechas_ok"] = True; info["fechas_validas"] = fechas.notna().sum(); info["mensaje_fechas"] = mensaje
                if fechas.notna().sum() > 0:
                    info["fecha_min"] = fechas.min(); info["fecha_max"] = fechas.max()
            else:
                info["fechas_ok"] = False; info["error_fechas"] = mensaje
        else:
            info["fechas_ok"] = False; info["error_fechas"] = "No se encontró columna de fecha"
        info["estadisticas"] = {"total_registros": len(df),
                                "pacientes_unicos": df['IDENTIFICACION'].nunique() if 'IDENTIFICACION' in df.columns else 0}
        return df, info
    except Exception as e:
        return None, f"Error al procesar el archivo: {str(e)}"

def validar_mes_completo(df_sispro, df_epi12, df_epi15, ano, mes):
    mask_sispro = (df_sispro['ANO'] == ano) & (df_sispro['MES'] == mes)
    mask_epi12  = (df_epi12['ANO'] == ano) & (df_epi12['MES'] == mes)
    mask_epi15  = (df_epi15['ANO'] == ano) & (df_epi15['MES'] == mes)
    df_sispro_mes = df_sispro[mask_sispro].copy()
    df_epi12_mes  = df_epi12[mask_epi12].copy()
    df_epi15_mes  = df_epi15[mask_epi15].copy()
    if len(df_sispro_mes)==0 and len(df_epi12_mes)==0 and len(df_epi15_mes)==0:
        return None, f"No hay datos para {mes:02d}/{ano}"
    grupos_sispro, total_sispro = {}, 0
    for grupo in GRUPOS_SISPRO.keys():
        if 'GRUPO_SISPRO' in df_sispro_mes.columns:
            count = df_sispro_mes[df_sispro_mes['GRUPO_SISPRO']==grupo]['IDENTIFICACION'].nunique()
        else: count = 0
        grupos_sispro[grupo] = count; total_sispro += count
    totales_semanales_epi12, total_epi12 = {}, 0
    if len(df_epi12_mes) > 0:
        col_amb = next((c for c in df_epi12_mes.columns if 'AMBULATORIA' in c or 'AMB' in c), None)
        col_emerg = next((c for c in df_epi12_mes.columns if 'EMERGENCIA' in c or 'EMER' in c), None)
        for sem in range(1, 53):
            df_sem = df_epi12_mes[df_epi12_mes['SEMANA_ANUAL'] == sem]
            if len(df_sem) > 0:
                amb_val = df_sem[col_amb].sum() if col_amb else len(df_sem)
                emerg_val = df_sem[col_emerg].sum() if col_emerg else 0
                tot_sem = amb_val + emerg_val
                totales_semanales_epi12[f"Semana {sem}"] = tot_sem
                total_epi12 += tot_sem
        if not totales_semanales_epi12: total_epi12 = df_epi12_mes['IDENTIFICACION'].nunique()
    total_epi15 = len(df_epi15_mes) if len(df_epi15_mes) > 0 else 0
    diff12 = total_epi12 - total_sispro; diff15 = total_epi15 - total_sispro
    errores = []
    if diff12 != 0: errores.append({'tipo':'EPI12','descripcion':f"EPI12 difiere de SISPRO en {abs(diff12)} registros."})
    if diff15 != 0: errores.append({'tipo':'EPI15','descripcion':f"EPI15 difiere de SISPRO en {abs(diff15)} causas."})
    return {'mes': f"{mes:02d}/{ano}", 'ano': ano, 'mes_num': mes,
            'sispro': {'grupos': grupos_sispro, 'total': total_sispro},
            'epi12': {'totales_semanales': totales_semanales_epi12, 'total': total_epi12},
            'epi15': {'total': total_epi15},
            'diferencias': {'sispro_epi12': diff12, 'sispro_epi15': diff15},
            'errores': errores, 'todos_coinciden': (diff12==0 and diff15==0)}, None

def validar_periodo(df_sispro, df_epi12, df_epi15, ano_inicio, mes_inicio, ano_fin, mes_fin):
    resultados = []
    fecha_actual = datetime(ano_inicio, mes_inicio, 1); fecha_fin = datetime(ano_fin, mes_fin, 1)
    while fecha_actual <= fecha_fin:
        ano, mes = fecha_actual.year, fecha_actual.month
        resultado, _ = validar_mes_completo(df_sispro, df_epi12, df_epi15, ano, mes)
        if resultado: resultados.append(resultado)
        fecha_actual = datetime(ano+1,1,1) if mes==12 else datetime(ano,mes+1,1)
    return resultados

# ==================================================================
# ============ MOTOR SIS-03/PRO (TABULADOR DIARIO) =================
# ==================================================================
MESES = ['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']
DIAS_MES = [31,28,31,30,31,30,31,31,30,31,30,31]

def norm_code(v):
    if not isinstance(v,str): return None
    m = re.match(r'^\s*(\d{2}(?:\.\d{2})*)[\.\s]*$', v)
    return m.group(1) if m else None

def num(v):
    if isinstance(v,bool): return np.nan
    if isinstance(v,(int,float)): return float(v)
    if isinstance(v,str):
        t = v.strip().replace(',','.')
        if re.fullmatch(r'-?\d+(\.\d+)?', t): return float(t)
    return np.nan

def leer_libro(a):
    nombre = getattr(a,'name',str(a))
    if hasattr(a,'read'):
        try: a.seek(0)
        except Exception: pass
        data = a.read()
    else:
        data = open(a,'rb').read()
    hojas = []
    if nombre.lower().endswith('.xls'):
        import xlrd
        bk = xlrd.open_workbook(file_contents=data)
        for sh in bk.sheets():
            hojas.append((sh.name, [[sh.cell_value(r,c) for c in range(sh.ncols)] for r in range(sh.nrows)]))
    else:
        import openpyxl
        wb = openpyxl.load_workbook(BytesIO(data), data_only=True, read_only=True)
        for ws in wb.worksheets:
            hojas.append((ws.title, [list(r) for r in ws.iter_rows(values_only=True)]))
    return hojas

def es_tabulador(hojas):
    for n,m in hojas[:3]:
        for r in range(min(30,len(m))):
            f = [str(x).strip().lower() for x in m[r] if x is not None]
            if any(x in ('código','codigo') for x in f) and any('actividad' in x for x in f): return True
    return False

def detectar_layout(matriz):
    hdr, cc, cl = None, 0, 1
    for r in range(min(40,len(matriz))):
        for c,v in enumerate(matriz[r]):
            if isinstance(v,str) and v.strip().lower() in ('código','codigo'):
                hdr, cc = r, c; break
        if hdr is not None: break
    if hdr is None: return None
    fila = matriz[hdr]
    for c,v in enumerate(fila):
        if isinstance(v,str) and 'actividad' in v.strip().lower(): cl = c
    dias, ct = {}, None
    for c,v in enumerate(fila):
        n = num(v)
        if n is not None and not np.isnan(n) and float(n).is_integer() and 1 <= n <= 31 and c > cl: dias[int(n)] = c
        if isinstance(v,str) and 'TOTAL' in v.upper(): ct = c
    if len(dias) < 28: dias = {d: cl+d for d in range(1,32)}
    if ct is None: ct = max(dias.values())+1
    return {'header_row':hdr,'col_code':cc,'col_label':cl,'dias':dias,'col_total':ct}

MAPA_META = {'entidad':'entidad','municipio':'municipio','establecimiento':'establecimiento',
             'nombre del medico':'medico','mes':'mes','año':'anio','ano':'anio'}

def extraer_meta(matriz, hdr):
    meta = {k:'' for k in ['entidad','municipio','establecimiento','medico','mes','anio','profesional','enfermera','ams']}
    for r in range(hdr):
        fila = matriz[r]
        for c,v in enumerate(fila):
            if not isinstance(v,str): continue
            t = v.strip(); low = t.lower()
            for campo,clave in MAPA_META.items():
                if low.startswith(campo+':'):
                    resto = t.split(':',1)[1].strip()
                    if not resto:
                        for k in range(c+1,len(fila)):
                            w = fila[k]
                            if isinstance(w,str) and w.strip():
                                wt = w.strip()
                                if wt.endswith(':') or any(wt.lower().startswith(x+':') for x in MAPA_META): break
                                resto = wt; break
                            nw = num(w)
                            if nw is not None and not np.isnan(nw): resto = str(int(nw)); break
                    if resto and not meta[clave]: meta[clave] = resto
            if 'NOMBRE MEDICO O PROFESIONAL' in t.upper():
                for ln in t.split('\n'):
                    l = ln.strip(); u = l.upper()
                    if u.startswith('NOMBRE MEDICO O PROFESIONAL:'): meta['profesional'] = l.split(':',1)[1].strip()
                    elif u.startswith('NOMBRE ENFERMERA O AUXILIAR:'): meta['enfermera'] = l.split(':',1)[1].strip()
                    elif u.startswith('NOMBRE AMS/ACAPS:'): meta['ams'] = l.split(':',1)[1].strip()
    if not meta['anio']:
        for r in range(hdr):
            fila = matriz[r]
            if any(isinstance(v,str) and v.strip().lower().startswith('mes:') for v in fila):
                for v in fila:
                    n = num(v)
                    if n is not None and not np.isnan(n) and 1900 <= n <= 2100: meta['anio'] = str(int(n)); break
            if meta['anio']: break
    return meta

def parse_hoja(nombre, matriz):
    lay = detectar_layout(matriz)
    if lay is None: return None
    hdr = lay['header_row']; mx = max(lay['col_total'], max(lay['dias'].values())); recs = []
    for r in range(hdr+1, len(matriz)):
        fila = matriz[r]
        if lay['col_code'] >= len(fila): continue
        code = norm_code(fila[lay['col_code']])
        if not code: continue
        lab = fila[lay['col_label']] if lay['col_label'] < len(fila) else ''
        lab = str(lab).strip() if lab is not None else ''
        daily = [num(fila[lay['dias'][d]]) if d in lay['dias'] and lay['dias'][d] < len(fila) else np.nan for d in range(1,32)]
        tot = num(fila[lay['col_total']]) if lay['col_total'] < len(fila) else np.nan
        recs.append({'fila':r+1,'codigo':code,'actividad':lab,'nivel':code.count('.')+1,'dias':daily,'total':tot,
                     'suma':float(np.nansum(daily)),
                     'celdas':int(sum(1 for v in daily if not np.isnan(v) and v>0)),'raw':fila[:mx+1]})
    if not recs: return None
    df = pd.DataFrame(recs); codes = set(df.codigo)
    df['es_padre'] = [any(o!=c and o.startswith(c+'.') for o in codes) for c in df.codigo]
    return {'nombre':nombre,'df':df,'meta':extraer_meta(matriz,hdr),'header_row':hdr+1,'layout':lay,'nrows':len(matriz)}

GRUPOS_SIS03 = [
 {'nombre':'Lactantes y preescolares (0 a <7 a)','corto':'Lact/Preesc','total':'01.01.01','m':'01.01.01.01','f':'01.01.01.02',
  'primeras':['01.01.02.01','01.01.02.02','01.01.02.03','01.01.03.01','01.01.03.02'],'sucesivas':['01.01.02.04','01.01.03.03'],
  'enfermeria':['01.01.02.05','01.01.03.04'],'consultas':['01.01.02','01.01.03'],'dx':'01.01.11',
  'sanos':['01.01.11.01','01.01.11.03'],'enfermos':['01.01.11.02','01.01.11.04'],
  'nut':'01.01.04','ta':'01.01.07','riesgo':'01.01.08','ref':'01.01.12'},
 {'nombre':'Escolares (7 a <12 a)','corto':'Escolar','total':'01.02.01','m':'01.02.01.01','f':'01.02.01.02',
  'primeras':['01.02.02.01','01.02.02.02','01.02.02.03','01.02.02.06'],'sucesivas':['01.02.02.04'],'enfermeria':['01.02.02.05'],
  'consultas':['01.02.02'],'dx':'01.02.13','sanos':['01.02.13.01'],'enfermos':['01.02.13.02'],
  'nut':'01.02.07','ta':'01.02.09','riesgo':'01.02.10','ref':'01.02.14'},
 {'nombre':'Adolescentes (12 a <19 a)','corto':'Adolescente','total':'01.05.01','m':'01.05.01.01','f':'01.05.01.02',
  'primeras':['01.05.02.01'],'sucesivas':['01.05.02.02'],'enfermeria':['01.05.02.03'],'consultas':['01.05.02'],
  'dx':'01.05.03','sanos':['01.05.03.01'],'enfermos':['01.05.03.02'],
  'nut':'01.05.04','ta':'01.05.06','riesgo':'01.05.07','ref':'01.05.10'},
 {'nombre':'Adultos (19 a <60 a)','corto':'Adulto','total':'02.00.01','m':'02.00.01.01','f':'02.00.01.02',
  'primeras':['02.00.02.01'],'sucesivas':['02.00.02.02'],'enfermeria':['02.00.02.03'],'consultas':['02.00.02'],
  'dx':'02.00.03','sanos':['02.00.03.01'],'enfermos':['02.00.03.02'],
  'nut':'02.00.04','ta':'02.00.06','riesgo':'02.00.07','ref':'02.00.10'},
 {'nombre':'Tercera edad (60 a y mas)','corto':'Tercera edad','total':'03.00.01','m':'03.00.01.01','f':'03.00.01.02',
  'primeras':['03.00.02.01'],'sucesivas':['03.00.02.02'],'enfermeria':['03.00.02.03'],'consultas':['03.00.02'],
  'dx':'03.00.03','sanos':['03.00.03.01'],'enfermos':['03.00.03.02'],
  'nut':'03.00.04','ta':'03.00.06','riesgo':'03.00.07','ref':'03.00.10'}]

NUT_CATS = ['Exceso','Normal','Zona Critica','Leve','Moderada','Grave','Bajo Peso']
TA_CATS  = ['Normal','Hipertenso','Hipotenso']
PROGRAMAS = [('01.03','CED / Diarreicas'),('01.04','IRA'),('04.01','Diabetes'),('04.02','Cardiovascular / HTA'),
 ('06.01','Tuberculosis'),('06.02','Asma'),('07','Salud reproductiva'),('08','Cancer cervico-uterino'),
 ('09','ITS / VIH'),('17','Salud mental'),('11','Nivel terciario'),('12','Otras actividades'),
 ('13','Educacion sanitaria'),('14','Visitas')]

MORB_CANON = [('Infecciosas y parasitarias',r'infeccios'),('Neoplasias',r'neoplasia'),
 ('Sangre y organos hematopoyeticos',r'sangre'),('Endocrina, nutricional y metabolica',r'endocrin'),
 ('Trastorno mental y comportamiento',r'mental y comp'),('Sistema nervioso',r'nervioso'),('Ojo y sus anexos',r'ojo'),
 ('Oido y apofisis mastoides',r'o[ií]do'),('Sistema circulatorio',r'circulatorio'),('Sistema respiratorio',r'respiratorio'),
 ('Sistema digestivo',r'digestivo'),('Piel y tejido conjuntivo',r'piel'),('Genital y urinaria',r'genital|urinar'),
 ('Parto y puerperio',r'parto y puerper'),('Traumatismos y envenenamientos',r'traumatism'),
 ('Anomalias congenitas',r'anomal'),('Control pre-natal',r'control pre-?natal'),('Parto distocico',r'parto dist'),
 ('Cianosis perinatal',r'cianosis'),('Ictericia neonatal',r'ictericia'),('Medicamentos en el embarazo',r'medicament'),
 ('Embarazo con tabaco',r'tabaco'),('Embarazo con alcohol',r'alcohol'),('Embarazo con cocaina',r'coca[ií]na'),
 ('Embarazo con pre-eclampsia',r'eclampsia')]

def canon_morb(l):
    t = l.lower()
    for n,p in MORB_CANON:
        if re.search(p,t): return n
    return l.strip()

def canon_ref(l):
    t = re.sub(r'\s+',' ', l.strip())
    for a,b in [('Traum. y Ortopedia','Traumatologia y Ortopedia'),('Traumatología  y Ortopedia','Traumatologia y Ortopedia'),
                ('Traumatología y Ortopedia','Traumatologia y Ortopedia'),('Médicos de Familia','Medico de Familia'),
                ('Medicos de Familia','Medico de Familia'),('Médico de Familia','Medico de Familia'),
                ('Atención Psiquiátrica de Ambulatoria','Atencion Psiquiatrica Ambulatoria'),
                ('Atención Psiquiátrica Ambulatoria','Atencion Psiquiatrica Ambulatoria'),
                ('Hospitalización Psiquiática de Agudos','Hospitalizacion Psiquiatrica de Agudos'),
                ('Hospitalización Psiquiátrica de Agudos','Hospitalizacion Psiquiatrica de Agudos')]:
        t = t.replace(a,b)
    return re.sub(r'\(Ministerio de (Educación|Sanidad)\)','(Ministerio)', t)

def idx_hoja(h): return {r.codigo: r for r in h['df'].itertuples(index=False)}
def val(ix,c,campo='suma'):
    r = ix.get(c)
    if r is None: return 0.0
    if campo=='suma': return float(r.suma)
    t = r.total; return 0.0 if (t is None or np.isnan(t)) else float(t)
def act_de(ix,c):
    r = ix.get(c); return r.actividad if r is not None else '-'
def fila_de(ix,c):
    r = ix.get(c); return int(r.fila) if r is not None else None
def dias_de(ix,c):
    r = ix.get(c); return list(r.dias) if r is not None else [np.nan]*31
def suma_lista(ix,cs,campo='suma'): return float(sum(val(ix,c,campo) for c in cs))
def hijos(ix,p):
    n = p.count('.')+1
    return [c for c in ix if c.startswith(p+'.') and c.count('.')==n]

def analizar_hoja(hoja, modo='dias'):
    campo = 'total' if modo=='ah' else 'suma'
    df = hoja['df']; ix = idx_hoja(hoja)
    V  = lambda c: val(ix,c,campo)
    S  = lambda cs: suma_lista(ix,cs,campo)
    VF = lambda c: (val(ix,c,'suma') or val(ix,c,'total'))
    out = {'nombre':hoja['nombre'],'meta':hoja['meta'],'header_row':hoja['header_row'],'modo':modo}
    us = {}
    for r in df.itertuples(index=False):
        for i,v in enumerate(r.dias):
            if not np.isnan(v) and v>0: us[i+1] = us.get(i+1,0)+v
    out['dias_con_c
