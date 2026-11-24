GRUPOS_SIS03 = [
 {'nombre':'Lactantes y preescolares (0 a <7 a)','corto':'Lact/Preesc','total':'01.01.01','m':'01.01.01.01','f':'01.01.01.02',
  'primeras':['01.01.02.01','01.01.02.02','01.01.02.03','01.01.03.01','01.01.03.02'],
  'sucesivas':['01.01.02.04','01.01.03.03'],'enfermeria':['01.01.02.05','01.01.03.04'],
  'consultas':['01.01.02','01.01.03'],'dx':'01.01.11',
  'sanos':['01.01.11.01','01.01.11.03'],'enfermos':['01.01.11.02','01.01.11.04'],
  'nut':'01.01.04','ta':'01.01.07','riesgo':'01.01.08','ref':'01.01.12'},
 {'nombre':'Escolares (7 a <12 a)','corto':'Escolar','total':'01.02.01','m':'01.02.01.01','f':'01.02.01.02',
  'primeras':['01.02.02.01','01.02.02.02','01.02.02.03','01.02.02.06'],
  'sucesivas':['01.02.02.04'],'enfermeria':['01.02.02.05'],
  'consultas':['01.02.02'],'dx':'01.02.13','sanos':['01.02.13.01'],'enfermos':['01.02.13.02'],
  'nut':'01.02.07','ta':'01.02.09','riesgo':'01.02.10','ref':'01.02.14'},
 {'nombre':'Adolescentes (12 a <19 a)','corto':'Adolescente','total':'01.05.01','m':'01.05.01.01','f':'01.05.01.02',
  'primeras':['01.05.02.01'],'sucesivas':['01.05.02.02'],'enfermeria':['01.05.02.03'],
  'consultas':['01.05.02'],'dx':'01.05.03','sanos':['01.05.03.01'],'enfermos':['01.05.03.02'],
  'nut':'01.05.04','ta':'01.05.06','riesgo':'01.05.07','ref':'01.05.10'},
 {'nombre':'Adultos (19 a <60 a)','corto':'Adulto','total':'02.00.01','m':'02.00.01.01','f':'02.00.01.02',
  'primeras':['02.00.02.01'],'sucesivas':['02.00.02.02'],'enfermeria':['02.00.02.03'],
  'consultas':['02.00.02'],'dx':'02.00.03','sanos':['02.00.03.01'],'enfermos':['02.00.03.02'],
  'nut':'02.00.04','ta':'02.00.06','riesgo':'02.00.07','ref':'02.00.10'},
 {'nombre':'Tercera edad (60 a y mas)','corto':'Tercera edad','total':'03.00.01','m':'03.00.01.01','f':'03.00.01.02',
  'primeras':['03.00.02.01'],'sucesivas':['03.00.02.02'],'enfermeria':['03.00.02.03'],
  'consultas':['03.00.02'],'dx':'03.00.03','sanos':['03.00.03.01'],'enfermos':['03.00.03.02'],
  'nut':'03.00.04','ta':'03.00.06','riesgo':'03.00.07','ref':'03.00.10'}]

NUT_CATS = ['Exceso','Normal','Zona Critica','Leve','Moderada','Grave','Bajo Peso']
TA_CATS  = ['Normal','Hipertenso','Hipotenso']

PROGRAMAS = [('01.03','CED / Diarreicas'),('01.04','IRA'),('04.01','Diabetes'),
             ('04.02','Cardiovascular / HTA'),('06.01','Tuberculosis'),('06.02','Asma'),
             ('07','Salud reproductiva'),('08','Cancer cervico-uterino'),('09','ITS / VIH'),
             ('17','Salud mental'),('11','Nivel terciario'),('12','Otras actividades'),
             ('13','Educacion sanitaria'),('14','Visitas')]

MORB_CANON = [('Infecciosas y parasitarias',r'infeccios'),('Neoplasias',r'neoplasia'),
 ('Sangre y organos hematopoyeticos',r'sangre'),('Endocrina, nutricional y metabolica',r'endocrin'),
 ('Trastorno mental y comportamiento',r'mental y comp'),('Sistema nervioso',r'nervioso'),
 ('Ojo y sus anexos',r'ojo'),('Oido y apofisis mastoides',r'o[ií]do'),
 ('Sistema circulatorio',r'circulatorio'),('Sistema respiratorio',r'respiratorio'),
 ('Sistema digestivo',r'digestivo'),('Piel y tejido conjuntivo',r'piel'),
 ('Genital y urinaria',r'genital|urinar'),('Parto y puerperio',r'parto y puerper'),
 ('Traumatismos y envenenamientos',r'traumatism'),('Anomalias congenitas',r'anomal'),
 ('Control pre-natal',r'control pre-?natal'),('Parto distocico',r'parto dist'),
 ('Cianosis perinatal',r'cianosis'),('Icter
