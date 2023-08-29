# Importar librerías de trabajo
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
from datetime import datetime as dt, timedelta
from github import Github
import streamlit as st
from io import BytesIO
from math import ceil
import pandas as pd
import numpy as np
import requests
import base64
import time
import pytz
import io
import os

# Definir área del token de entrada
# token = st.text_input('Ingrese el token de acceso', label_visibility=st.session_state.visibility, disabled=st.session_state.disabled, placeholder='Token de acceso')
token = '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'
if token!='':

    # Crear la sesión de GitHub
    github_session = Github(token)

    # Obtener el repositorio de trabajo
    github_repo = github_session.get_repo('miguellosoyo/SKU')

# Función que permite la extracción del número de la semana del mes en la que cae la fecha ingresada
def week_of_month(dt):
    """
    Usa una fecha en específico para devolver el número de la semana a la que corresponde en el mes de la fecha.
    Input:
    - dt: variable de tipo datetime. Es la fecha de la cual se quiere saber a qué semana del mes corresponde.
    Output:
    - n_week: Se devuelve un valor entero que hace referencia a la semana del mes en la que se encuentra la fecha ingresada.
    """

    # Obtener el primer día del mes
    first_day = dt.replace(day=1)

    # Identificar el transcurso desde el primer día del mes hasta la fecha ingresada
    dom = dt.day
    adjusted_dom = dom + first_day.weekday()

    # Devolver el número de la semana del año
    n_week = int(ceil(adjusted_dom/7.0))
    return f'Semana {n_week}'

# Definir una función que devuelva la fecha del día de la semana pasada que se elija
def previous_day_date(day):
    """
    Emplea el día de la semana y, opcionalmente, una fecha de referencia para calcular la fecha del día de la semana (inmediatamente anterior) ingresado.
    Input:
        - day: día de la semana del que se quiere obtener la fecha.
        - start_date: fecha de contexto para la semana de referencia.
    Output:
        - targetDate: fecha correspondiente al día de la semana pasada.
        """

    # Crear una tabla con los días de la semana
    weekdaysList = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Asignar la fecha en que se ejecuta el proceso al argumento start_date
    start_date = pd.to_datetime(str(dt.now(tz=pytz.timezone('America/Guatemala')))).replace(tzinfo=None)

    # Obtener el día de la semana que corresponde
    dayNumber = start_date.weekday()

    # Obtener el nombre del día de la semana que corresponde
    dayNumberTarget = weekdaysList.index(day)

    # Obtener la distancia entre el día actual y el de la semana pasada
    daysAgo = (7 + dayNumber - dayNumberTarget) % 7

    # Evaluar si la distancia es igual a 0
    if daysAgo == 0:

        # Asignar a la distancia el valor e 7 días de diferencia
        daysAgo = 7

    # Obtener la fecha del día de la semana anterior
    targetDate = pd.to_datetime(str(start_date - timedelta(days=daysAgo))[:10])

    # Devolver la fecha encontrada
    return targetDate

# Definir función para cargar información
@st.cache_data
def load_sku(values:pd.DataFrame):

    '''
    Esta función toma un DataFrame que sirve para cargar información que el usuario ha ingresado en las pestañas correspondientes a cada categoría de puesto de trabajo.

    Inputs:
    df: DataFrame de pandas con información de SKU. También puede ser un DataFrame vacío.
    values: DataFrame con los campos Puesto, Rango Salarial y Horas Asignadas, cuyos valores ha definido el usuario dentro del formulario correspondiente a una categoría en específico.

    Output:
    df: DataFrame con la información de SKU actualizada con los valores ingresados por el usuario. La información se guarda en memoria cache para que las actualizaciones no sean eliminadas.
    '''
    global sku_df
    
    # Concatenar información
    df = pd.concat([df, values], axis=0, ignore_index=True)

    return df

@st.cache_data()
def load_data():
    
    # Cargar información de Tribal
    content = github_repo.get_contents('Bandas Salariales.csv')
    tribal_wl = pd.read_csv(io.StringIO(content.decoded_content.decode('utf-8')))
    tribal_wl.columns = [x.title() for x in tribal_wl.columns]

    # Definir tipo de cambio QTG/USD
    tc = 0.147679319
    
    # Cargar información del Roster de Tribal
    content = github_repo.get_contents('Códigos de Posición Tribal.csv')
    tribal_rt = pd.read_csv(io.StringIO(content.decoded_content.decode('utf-8')))
    
    # Cruzar información
    tribal_salary = pd.merge(tribal_rt, tribal_wl, left_on='Codigo de Puesto', right_on='Codigo Posicion',  how='left')
    
    # Importar y consolidar información de proyectos
    activos = pd.read_csv('https://raw.githubusercontent.com/miguellosoyo/SKU/main/Proyectos%20Activos.csv', encoding='latin')
    archivados = pd.read_csv('https://raw.githubusercontent.com/miguellosoyo/SKU/main/Proyectos%20Archivados.csv', encoding='latin')
    proyectos = pd.concat([activos, archivados], axis=0, ignore_index=True)
    proyectos = proyectos.loc[(proyectos['Proyecto'].notna()) & (~proyectos['Proyecto'].astype(str).str.contains('Total ')), ['Proyecto', 'Estado']].reset_index(drop=True)

    # Cargar información del Roster de Tribal
    columns = ['Código', 'Nombre completo', 'Fecha nacimiento', 'Sexo', 'Nacionalidad', 'Departamento', 'Puesto', 'Fecha alta', 'Fecha baja', 'Email comunicación']
    roster = pd.read_csv('https://raw.githubusercontent.com/miguellosoyo/SKU/main/Roster%20Tribal.csv', usecols=columns, encoding='latin')
    roster = roster[(roster['Fecha baja'].isna()) & (roster['Código'].notna())].reset_index(drop=True)       
    roster[['Fecha nacimiento', 'Fecha alta']] = roster[['Fecha nacimiento', 'Fecha alta']].astype('datetime64[ms]')
    missing_emails = {'DANIEL REYNOSO SANCHEZ':'dreynoso@tribalworldwide.gt', 'ALEJANDRO BRITO DAMAS':'abrito@tribalworldwide.gt', 
                        'JOSE MANUEL DUBON MONGE':'jdubon@tribalworldwide.gt', 'ULAI SEM NAVA CAMPOS':'unava@tribalworldwide.gt'}
    roster.loc[roster['Email comunicación'].isna(), 'Email comunicación'] = roster.loc[roster['Email comunicación'].isna(), 'Nombre completo'].map(missing_emails)
    now = pd.to_datetime(str(dt.now(tz=pytz.timezone('America/Guatemala')))).replace(tzinfo=None)
    roster['Edad'] = roster['Fecha nacimiento'].fillna(pd.to_datetime('2000/01/01')).apply(lambda x: int((now-x).days/365))
    roster['Seniority'] = roster['Fecha alta'].apply(lambda x: np.where(int((now-x).days/365) < 1, 'Sin Seniority', int((now-x).days/365)))

    # Importar y transformar información de Clockify
    urls = ['https://raw.githubusercontent.com/miguellosoyo/SKU/main/Informe%20Detallado%20de%20Horas%201.csv', 
            'https://raw.githubusercontent.com/miguellosoyo/SKU/main/Informe%20Detallado%20de%20Horas%202.csv']
    columns = ['Proyecto', 'Cliente', 'Usuario', 'Grupo', 'Correo electrónico', 'Fecha de inicio', 'Duración (decimal)']
    df = pd.concat([pd.read_csv(url, usecols=columns, encoding='latin') for url in urls], axis=0, ignore_index=True)
    df = df[df['Fecha de inicio'].notna()].reset_index(drop=True)
    df['Fecha de inicio'] = df['Fecha de inicio'].astype('datetime64[ms]')
    
    # Integrar nombres del día de la semana, semana del mes, quincena del mes y mes correspondiente
    weekdays_dict = {'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
    month_dict = {'January':'Enero', 'February':'Febrero', 'March':'Marzo', 'April':'Abril', 'May':'Mayo', 'June':'Junio', 'July':'Julio', 'August':'Agosto', 'September':'Septiembre', 'October':'Octubre', 'November':'Noviembre', 'December':'Diciembre'}
    df['Día'] = df['Fecha de inicio'].dt.day_name().map(weekdays_dict)
    df['Semana'] = df['Fecha de inicio'].apply(week_of_month)
    df['Quincena'] = df['Fecha de inicio'].apply(lambda x: np.where(x.day<=15, 'Quincena 1', 'Quincena 2'))
    df['Mes'] = df['Fecha de inicio'].astype('datetime64[ms]').dt.month_name().map(month_dict)
    df['Año'] = df['Fecha de inicio'].astype('datetime64[ms]').dt.year

    # Crear una tabla comparativa de horas capacidad y cargadas
    groups = ['Usuario', 'Correo electrónico', 'Grupo', 'Semana', 'Mes', 'Proyecto']
    agg ={'Duración (decimal)':'sum', 'Cliente':'nunique', 'Fecha de inicio':'min'}
    df_hrs = df.groupby(groups, as_index=False).agg(agg).rename(columns={'Duración (decimal)':'Horas Cargadas'})
    df_hrs['Horas Capacidad'] = 44
    df_hrs['Horas Desarrollo'] = df_hrs['Horas Capacidad']*0.8
    df_hrs['Horas Gestión']	= df_hrs['Horas Capacidad']*0.175
    df_hrs['Horas No Facturables'] = df_hrs['Horas Capacidad']*0.015
    df_hrs['Horas Recursos Humanos'] = df_hrs['Horas Capacidad']*0.01
    df_hrs['Capacidad Disponible'] = df_hrs[['Horas Desarrollo', 'Horas Gestión']].sum(axis=1)
    df_hrs['Capacidad Disponible'] = df_hrs['Capacidad Disponible'].sub(df_hrs['Horas Cargadas']).round(0)
    
    # Calcular porcentaje de horas cargadas por proyecto
    df_hrs['Porcentaje de Horas Cargadas'] = df_hrs['Horas Cargadas'].div(df_hrs.groupby(['Usuario'])['Horas Cargadas'].transform(lambda x: x.sum()))
    
    # Cálculo de los indicadores
    df_hrs['Porcentaje Horas Cargadas'] = ((df_hrs['Horas Cargadas'] / df_hrs['Horas Capacidad']) * 100).round(2)
    df_hrs['Porcentaje Capacidad Disponible'] = ((df_hrs['Capacidad Disponible'] / df_hrs['Horas Capacidad']) * 100).round(2)
    df_hrs['Porcentaje Horas Desarrollo'] = ((df_hrs['Horas Desarrollo'] / df_hrs['Horas Capacidad']) * 100).round(2)
    df_hrs['Porcentaje Horas Gestión'] = ((df_hrs['Horas Gestión'] / df_hrs['Horas Capacidad']) * 100).round(2)
    df_hrs['Porcentaje Horas No Facturables'] = ((df_hrs['Horas No Facturables'] / df_hrs['Horas Capacidad']) * 100).round(2)

    # Integrar información del Roster
    columns = ['Código', 'Email comunicación', 'Sexo', 'Nacionalidad', 'Departamento', 'Puesto', 'Fecha alta', 'Edad', 'Seniority',]
    df_hrs = pd.merge(df_hrs, roster[columns], left_on='Correo electrónico', right_on='Email comunicación', how='left').drop(columns='Email comunicación')

    # Identificar a los usuarios sin posición definida en Roster
    usuarios_sin_posicion = df_hrs[df_hrs['Edad'].isna()]['Usuario'].nunique()
    df_hrs = df_hrs[df_hrs['Edad'].notna()].reset_index(drop=True)
    df_hrs['Edad'] = df_hrs['Edad'].astype(int)
    
    # Obtener el registro más reciente
    now = pd.to_datetime(str(dt.now(tz=pytz.timezone('America/Guatemala')))).replace(tzinfo=None)
    now = pd.to_datetime('2023-08-21')
    anio_actual = now.year
    semana_actual = week_of_month(now)
    month_dict = {'1':'Enero', '2':'Febrero', '3':'Marzo', '4':'Abril', '5':'Mayo', '6':'Junio', '7':'Julio', '8':'Agosto', '9':'Septiembre', '10':'Octubre', '11':'Noviembre', '12':'Diciembre'}
    mes_actual = str(now.month).replace(str(now.month), month_dict[str(now.month)])
    df_hrs = df_hrs[(df_hrs['Semana']==semana_actual) & (df_hrs['Mes']==mes_actual)].sort_values(['Usuario', 'Capacidad Disponible'], ascending=False, ignore_index=True)
    
    # Integrar salarios
    df_hrs['Salario Q'] = pd.merge(df_hrs, tribal_salary, on='Código', how='left')['Salario Local']
    df_hrs['Salario US'] = pd.merge(df_hrs, tribal_salary, on='Código', how='left')['Salario Borderless']
    
    # Calcular los costos por hora de acuerdo al mes
    months_dates = {'Enero':[f'{anio_actual}-01-01', f'{anio_actual}-01-31'], 'Febrero':[f'{anio_actual}-02-01', f'{anio_actual}-01-28'], 
                    'Marzo':[f'{anio_actual}-03-01', f'{anio_actual}-03-31'], 'Abril':[f'{anio_actual}-04-01', f'{anio_actual}-04-30'], 
                    'Mayo':[f'{anio_actual}-05-01', f'{anio_actual}-05-31'], 'Junio':[f'{anio_actual}-06-01', f'{anio_actual}-06-30'], 
                    'Julio':[f'{anio_actual}-07-01', f'{anio_actual}-07-31'], 'Agosto':[f'{anio_actual}-05-01', f'{anio_actual}-05-31'], 
                    'Septiembre':[f'{anio_actual}-09-01', f'{anio_actual}-09-30'], 'Octubre':[f'{anio_actual}-10-01', f'{anio_actual}-10-31'], 
                    'Noviembre':[f'{anio_actual}-11-01', f'{anio_actual}-11-30'], 'Diciembre':[f'{anio_actual}-12-01', f'{anio_actual}-12-31']}
    start, end = months_dates[mes_actual] 
    out_days = ['2023-08-15']
    busdays = np.busday_count(start, end, holidays=out_days)
    df_hrs['Días Laborables'] = busdays
    df_hrs['Costo por Hora Q'] = df_hrs['Salario Q'].div(df_hrs['Días Laborables']*9).round(2)
    df_hrs['Costo por Hora US'] = df_hrs['Salario US'].div(df_hrs['Días Laborables']*9).round(2)
    df_hrs['Costo por Horas Cargadas Q'] = df_hrs['Horas Cargadas'].multiply(df_hrs['Costo por Hora Q']).round(2)
    df_hrs['Costo por Horas Cargadas US'] = df_hrs['Horas Cargadas'].multiply(df_hrs['Costo por Hora US']).round(2)
    df_hrs['Costo por Horas Disponibles Q'] = df_hrs['Capacidad Disponible'].multiply(df_hrs['Costo por Hora Q']).round(2)
    df_hrs['Costo por Horas Disponibles US'] = df_hrs['Capacidad Disponible'].multiply(df_hrs['Costo por Hora US']).round(2)
    
    df_hrs[['Salario Q', 'Salario US']] = df_hrs[['Salario Q', 'Salario US']].fillna('Sin Salario Asociado')
    costs = ['Costo por Hora Q', 'Costo por Hora US', 'Costo por Horas Cargadas Q', 'Costo por Horas Cargadas US', 
            'Costo por Horas Disponibles Q', 'Costo por Horas Disponibles US'] 
    df_hrs[costs] = df_hrs[costs].fillna('Sin Costo Determinado')
    
    # Identificar posiciones sin código de posición
    users_without_code_position = df_hrs.loc[df_hrs['Salario Q']=='Sin Salario Asociado', ['Código', 'Usuario', 'Puesto', 'Fecha alta', 'Salario Q']].copy()
    # st.write(df_hrs[df_hrs['Usuario']=='Ángel David Vargas'])
    
    # Crear nueva variable de proyectos
    return tribal_wl, tribal_rt, df_hrs, users_without_code_position

def position():
    if st.session_state.button_clicked_entry:
        return st.session_state['job_1_1']
    elif st.session_state.button_clicked_frontline:
        return st.session_state['job_2_2']
    elif st.session_state.button_clicked_management:
        return st.session_state['job_3_3']
    elif st.session_state.button_clicked_sr_management:
        return st.session_state['job_4_4']
    else:
        return ''

def get_installed_capacity(data, job, key):
        
    # Evaluar la capacidad disponible
    df = data.copy()
    df = df[(df['Puesto']==job)].sort_values(['Código', 'Capacidad Disponible'], ascending=False, ignore_index=True)
    columns = ['Código', 'Usuario', 'Correo electrónico', 'Puesto', 'Grupo', 'Proyecto', 'Capacidad Disponible', 'Porcentaje Horas Cargadas', 
                'Porcentaje Capacidad Disponible'] #
    df_hrs = df[columns].copy()
    
    # Crear una tabla editable
    gd = GridOptionsBuilder.from_dataframe(df_hrs)
    gd.configure_default_column(groupable=True)
    gd.configure_selection(selection_mode='multiple', use_checkbox=True)
    gridoptions = gd.build()
    grid_table = AgGrid(df_hrs, gridOptions=gridoptions, key=job, allow_unsafe_jscode=True, theme='balham')
    
    return grid_table 

@st.cache_data()
def get_filtered_data_cache():
    return pd.DataFrame()

@st.cache_data()
def save(df):
    return df

@st.cache_data
def selection_data(df):
    selection = df['selected_rows']
    
    # Concatenar información a tabla SKUs
    df_selection = pd.DataFrame()
    if selection != []:
        for dic in selection:
            df_selection = pd.concat([df_selection, pd.DataFrame({k:[v] for k,v in zip(list(dic.keys())[1:], list(dic.values())[1:])})], axis=0, ignore_index=True)
    else:
        df_selection = pd.DataFrame()
    return df_selection
    
@st.cache_resource
def save_data(df, sku=pd.DataFrame()):
    return pd.concat([sku, df]).drop_duplicates().reset_index(drop=True)

@st.cache_resource
def load_finance_data(labor_costs:pd.DataFrame):
    
    # Crear la sesión de GitHub
    token = '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'
    github_session = Github(token)

    # Obtener el repositorio de trabajo
    github_repo = github_session.get_repo('miguellosoyo/SKU')

    # Cargar tabla de proyectos
    content = github_repo.get_contents('Proyectos Tribal.csv')
    active_projects = pd.read_csv(io.StringIO(content.decoded_content.decode('utf-8')))
    active_projects.columns = [x.title() for x in active_projects.columns]
    budget_list = [str(x).replace('\n', '').strip().split(';') for x in active_projects['Presupuestos Asociados'].tolist() if str(x)!='nan']
    budget_list = [x.strip() for x in list(chain.from_iterable(budget_list))]
    active_projects['Presupuestos Asociados'] = active_projects['Presupuestos Asociados'].apply(lambda x: str(x).split(';'))
    budgets = pd.DataFrame(active_projects['Presupuestos Asociados'].to_list())
    budgets.columns = [f'Presupuesto {i+1}' for i in range(0, len(budgets.columns))]
    active_projects = pd.concat([active_projects, budgets], axis=1).drop(columns='Presupuestos Asociados')
    active_projects = pd.melt(active_projects, id_vars=['Proyecto', 'Freelance', 'Pago De Licencias Y Aplicativos', 'Descripción De Licencias Y Aplicativos Pagados'],
                            value_vars=[f'Presupuesto {i+1}' for i in range(0, len(budgets.columns))], var_name='Presupuesto', value_name='Número_Presupuesto')
    active_projects = active_projects.loc[~active_projects['Número_Presupuesto'].astype(str).str.contains('None|nan'),:].reset_index(drop=True)

    # Cargar tabla de Presupuestos y Cotizaciones
    budgets = pd.read_excel('https://github.com/miguellosoyo/SKU/raw/main/Reporte%20Presupuestos%20Consulte.xlsx')
    budgets.columns = [x.replace('TRAFICO_PRESUPUESTOS_', '') for x in budgets.columns]
    # budgets = budgets[budgets['Número_Presupuesto'].isin(active_projects['Número_Presupuesto'].drop_duplicates().tolist())].reset_index(drop=True)
    columns = ['Valor_Total', 'Valor_Subtotal', 'Costo_Externo', 'Costo_Interno', 'Valor_Comisión_Externo']
    budgets[columns] = budgets[columns].applymap(lambda x: float(str(x).replace('Q', '').replace('.','').replace(',', '.')))
    columns = ['CATEGORIA_CLIENTE', 'CLIENTE', 'EJECUTIVO', 'STATUS', 'Número_Presupuesto', 'P_C'] + columns
    budgets = budgets[columns]

    # Combinar información de Consulte y Proyectos Activos
    budgets = pd.merge(active_projects, budgets, on='Número_Presupuesto', how='left')

    # Sustituir valores no determinados del costo de horas
    labor_costs.loc[labor_costs['Costo por Hora Q']=='Sin Costo Determinado', 'Costo por Hora Q'] = labor_costs.loc[labor_costs['Costo por Hora Q']!='Sin Costo Determinado', 'Costo por Hora Q'].mean().round(2)
    labor_costs.loc[labor_costs['Costo por Hora US']=='Sin Costo Determinado', 'Costo por Hora US'] = labor_costs.loc[labor_costs['Costo por Hora US']!='Sin Costo Determinado', 'Costo por Hora Q'].mean().round(2)

    # Integrar información faltante
    mean_cost_q = labor_costs.loc[(labor_costs['Costo por Hora Q']!='Sin Costo Determinado') & (labor_costs['Costo por Hora Q'].notna()), 'Costo por Hora Q'].median().round(2)
    mean_cost_us = labor_costs.loc[(labor_costs['Costo por Hora US']!='Sin Costo Determinado') & (labor_costs['Costo por Hora US'].notna()), 'Costo por Hora US'].median().round(2)
    labor_costs['Costo por Hora Q'] = labor_costs['Costo por Hora Q'].fillna(mean_cost_q).astype(str).replace('Sin Costo Determinado', f'{mean_cost_q}').astype(float)
    labor_costs['Costo por Hora US'] = labor_costs['Costo por Hora US'].fillna(mean_cost_us).astype(str).replace('Sin Costo Determinado', f'{mean_cost_us}').astype(float)
    budgets[['Freelance', 'Pago De Licencias Y Aplicativos']] = budgets[['Freelance', 'Pago De Licencias Y Aplicativos']].replace('[\$,]', '', regex=True).astype(float)
    
    # Detallar costos laborales
    groups = ['Proyecto', 'Usuario']
    agg = {'Horas Cargadas':'sum', 'Fecha de inicio':'min', 'Costo por Hora Q':'median', 'Costo por Hora US':'median'}
    detail_labor_costs = labor_costs.groupby(groups, as_index=False).agg(agg)
    detail_labor_costs['Fecha Actual'] = pd.to_datetime(str(dt.now(tz=pytz.timezone('America/Guatemala')))).replace(tzinfo=None)
    detail_labor_costs['Periodo Transcurrido'] = detail_labor_costs.apply(lambda row : np.busday_count(row['Fecha de inicio'].date(), row['Fecha Actual'].date()), axis=1)/5
    
    # Obtener las horas capacidad correctas
    detail_labor_costs['Horas Capacidad'] = detail_labor_costs['Periodo Transcurrido'] * 44
    
    # Calcular los costos y gastos de cada proyecto
    detail_labor_costs['Costo Total No Facturables Q'] = (detail_labor_costs['Costo por Hora Q'].multiply((detail_labor_costs['Horas Capacidad'])) * 0.015).round(2)
    detail_labor_costs['Costo Total No Facturables US'] = (detail_labor_costs['Costo por Hora US'].multiply(detail_labor_costs['Horas Capacidad']) * 0.015).round(2)
    detail_labor_costs['Costo Total GTH Q'] = (detail_labor_costs['Costo por Hora Q'].multiply(detail_labor_costs['Horas Capacidad']) * 0.01).round(2)
    detail_labor_costs['Costo Total GTH US'] = (detail_labor_costs['Costo por Hora US'].multiply(detail_labor_costs['Horas Capacidad']) * 0.01).round(2)
    detail_labor_costs['Costo Total Desarrollo Q'] = (detail_labor_costs['Costo por Hora Q'].multiply(detail_labor_costs['Horas Capacidad']) * 0.8).round(2)
    detail_labor_costs['Costo Total Desarrollo US'] = (detail_labor_costs['Costo por Hora US'].multiply(detail_labor_costs['Horas Capacidad']) * 0.8).round(2)
    detail_labor_costs['Costo Total Gestión Q'] = (detail_labor_costs['Costo por Hora Q'].multiply(detail_labor_costs['Horas Capacidad']) * 0.175).round(2)
    detail_labor_costs['Costo Total Gestión US'] = (detail_labor_costs['Costo por Hora US'].multiply(detail_labor_costs['Horas Capacidad'])* 0.175).round(2)
    
    # Agrupar información por proyecto
    groups = ['Proyecto']
    agg = {'Horas Cargadas':'sum', 'Fecha de inicio':'min', 'Costo por Hora Q':'median', 'Costo por Hora US':'median', 'Usuario':'nunique'}
    labor_costs_agg = detail_labor_costs.groupby(groups, as_index=False).agg(agg)

    # Obtener el número de días laborales entre dos fechas
    labor_costs_agg['Fecha Actual'] = pd.to_datetime(str(dt.now(tz=pytz.timezone('America/Guatemala')))).replace(tzinfo=None)
    labor_costs_agg['Periodo Transcurrido'] = labor_costs_agg.apply(lambda row : np.busday_count(row['Fecha de inicio'].date(), row['Fecha Actual'].date()), axis=1)/5

    # Obtener las horas capacidad correctas
    labor_costs_agg['Horas Capacidad'] = labor_costs_agg['Periodo Transcurrido'] * 44 * labor_costs_agg['Usuario']

    # Calcular los costos y gastos de cada proyecto
    labor_costs_agg['Gastos Administrativos'] = 0.08
    labor_costs_agg['Costos Indirectos'] = 0.06
    labor_costs_agg['Costo Total No Facturables Q'] = (labor_costs_agg['Costo por Hora Q'].multiply((labor_costs_agg['Horas Capacidad'])) * 0.015).round(2)
    labor_costs_agg['Costo Total No Facturables US'] = (labor_costs_agg['Costo por Hora US'].multiply(labor_costs_agg['Horas Capacidad']) * 0.015).round(2)
    labor_costs_agg['Costo Total GTH Q'] = (labor_costs_agg['Costo por Hora Q'].multiply(labor_costs_agg['Horas Capacidad']) * 0.01).round(2)
    labor_costs_agg['Costo Total GTH US'] = (labor_costs_agg['Costo por Hora US'].multiply(labor_costs_agg['Horas Capacidad']) * 0.01).round(2)
    labor_costs_agg['Costo Total Desarrollo Q'] = (labor_costs_agg['Costo por Hora Q'].multiply(labor_costs_agg['Horas Capacidad']) * 0.8).round(2)
    labor_costs_agg['Costo Total Desarrollo US'] = (labor_costs_agg['Costo por Hora US'].multiply(labor_costs_agg['Horas Capacidad']) * 0.8).round(2)
    labor_costs_agg['Costo Total Gestión Q'] = (labor_costs_agg['Costo por Hora Q'].multiply(labor_costs_agg['Horas Capacidad']) * 0.175).round(2)
    labor_costs_agg['Costo Total Gestión US'] = (labor_costs_agg['Costo por Hora US'].multiply(labor_costs_agg['Horas Capacidad'])* 0.175).round(2)

    # Agrupar información por proyecto
    groups = ['Proyecto']
    agg = {'Gastos Administrativos':'mean', 'Costos Indirectos':'mean', 'Costo Total No Facturables Q':'sum', 'Costo Total GTH Q':'sum', 'Costo Total Desarrollo Q':'sum', 'Costo Total Gestión Q':'sum', 'Fecha de inicio':'min'}
    labor_costs_agg = labor_costs_agg.groupby(groups, as_index=False).agg(agg)

    # Agrupar información
    groups = ['Proyecto']
    agg = {'Freelance':'mean', 'Pago De Licencias Y Aplicativos':'mean', 'Valor_Total':'sum', 'Valor_Subtotal':'sum', 'Costo_Externo':'sum', 'Costo_Interno':'sum', 'Valor_Comisión_Externo':'sum'}
    budgets_agg = budgets.groupby(groups, as_index=False).agg(agg)

    # Calcular utilidad
    budgets_agg['Utilidad Bruta'] = budgets_agg['Valor_Subtotal'] - budgets_agg['Costo_Externo']

    # Integrar información de Consulte
    df_budgets = pd.merge(budgets_agg, labor_costs_agg, on='Proyecto', how='left')
    df_budgets['Gastos Administrativos'] = df_budgets['Valor_Subtotal'].multiply(df_budgets['Gastos Administrativos']).round(2)
    df_budgets['Costos Indirectos'] = df_budgets['Valor_Subtotal'].multiply(df_budgets['Costos Indirectos']).round(2)

    # Calcular utilidad neta
    df_budgets['Utilidad Neta'] = (df_budgets['Utilidad Bruta'] - df_budgets['Pago De Licencias Y Aplicativos'] - df_budgets['Freelance'] - df_budgets['Gastos Administrativos'] - df_budgets['Costos Indirectos'] - df_budgets['Costo Total No Facturables Q'] - df_budgets['Costo Total GTH Q'] - df_budgets['Costo Total Desarrollo Q'] - df_budgets['Costo Total Gestión Q']).round(2)

    # Identificar los proyectos que tienen información completa
    df_budgets_ok = df_budgets.loc[(~df_budgets['Utilidad Neta'].isnull()) & (df_budgets['Valor_Total']!=0), :].reset_index(drop=True)
    df_budgets_ok['Margen Neto'] = df_budgets_ok['Utilidad Neta'].div(df_budgets_ok['Valor_Subtotal']).round(2)

    return df_budgets_ok, detail_labor_costs

# Definir una función para traer gráfico de media luna
def half_doughnut(df):
    values = ['Freelance', 'Pago De Licencias Y Aplicativos', 'Gastos Administrativos', 'Costos Indirectos', 'Costo Total No Facturables', 'Costo Total GTH', 
              'Costo Total Desarrollo', 'Costo Total Gestión']
    options = {
        'tooltip': {
            'trigger': 'item'
            },
        'legend': {
            'top': '0%',
            'left': 'center',
            },
        'series': [
            {
                'name': 'Access From',
                'type': 'pie',
                'radius': ['40%', '70%'],
                'startAngle': 180,
                'top': '20%',
                'label': {
                    'show': True,
                    },
                'data':[{'value': df.loc[df['Conceptos']==x, 'Valores'].str.replace('Q ', '').str.replace(',','').astype(float).values[0], 
                         'name': f'{x}'} for x in values]
                }
            ]
        }
    
    return options



# Definir la página que corresponde el SKU
st.set_page_config(page_title='SKU - Stock Keeping Unit for TWW Positions', page_icon=':bar_chart:', layout='wide')

# Hacer las columnas ajustables y con filtros
gb = GridOptionsBuilder()
gb.configure_default_column(resizable=True, editable=False,)

# Instanciar estados de visibilidad para la sesión de la app
if 'button_clicked_entry' not in st.session_state or 'button_clicked_frontline' not in st.session_state or 'button_clicked_management' not in st.session_state or 'button_clicked_sr_management' not in st.session_state:
    st.session_state.button_clicked_entry = False
    st.session_state.button_clicked_frontline = False
    st.session_state.button_clicked_management = False
    st.session_state.button_clicked_sr_management = False
    
if 'visibility' not in st.session_state:
    st.session_state.visibility = 'visible'
    st.session_state.disabled = False

if 'get_codes' not in st.session_state:
    st.session_state.get_codes = []

def callback_entry():
    st.session_state.button_clicked_entry = True
    st.session_state.button_clicked_frontline = False
    st.session_state.button_clicked_management = False
    st.session_state.button_clicked_sr_management = False

def callback_frontline():
    st.session_state.button_clicked_entry = False
    st.session_state.button_clicked_frontline = True
    st.session_state.button_clicked_management = False
    st.session_state.button_clicked_sr_management = False

def callback_management():
    st.session_state.button_clicked_entry = False
    st.session_state.button_clicked_frontline = False
    st.session_state.button_clicked_management = True
    st.session_state.button_clicked_sr_management = False

def callback_sr_management():
    st.session_state.button_clicked_entry = False
    st.session_state.button_clicked_frontline = False
    st.session_state.button_clicked_management = False
    st.session_state.button_clicked_sr_management = True

# Cargar información de todas las posiciones
tribal_wl, tribal_rt, df, out = load_data()

# Integrar título de la barra lateral
st.header('⚙️ Stock Keeping Unit')

# Insertar filtro para los distintos niveles
levels_cat = tribal_wl['Categoria'].unique().tolist()
levels = tribal_wl['Nivel'].unique().tolist()
tribal_wl['Posicion'] = tribal_wl['Posicion'].str.title()

# st.write(df)

# Definir las pestañas para cada categoría de nivel
entry, front, manage, sr_manage, sku_tab = st.tabs(levels_cat + ['SKU'])

# Integrar formulario para Entry Level
with entry:

    # Definir variables de categoría, nivel y consecutivo
    i = 1
    level = 1
    cat = 'entry'

    # Dividir en tres columnas
    c1, c2, c3 = st.columns(3)
    
    # Definir input de Cargo, Nivel Salarial, Horas Asignadas
    c1.markdown('### Disponibilidad')
    entry_job = c1.selectbox(label='Seleccionar cargo', options=[x for x in tribal_wl[(tribal_wl['Categoria']=='Entry \nLevel')]['Posicion'].unique()], key=f'job_{level}_{i}')
    
    # Integrar botón para consultar posiciones de Frontline
    c2.button('Consultar Posiciones', key='consult_entry', on_click=callback_entry)
    
    # Cargar información de capacidad instalada
    if st.session_state.button_clicked_entry:
        # st.write(cat)
        # st.write(entry_job)
        # st.write(df)
        
        df_capacity = get_installed_capacity(df, job=entry_job, key=cat)
        selection = df_capacity['selected_rows']
        
        # Concatenar información a tabla SKUs
        df_selection = pd.DataFrame()
    
        if selection != []:
            for dic in selection:
                df_selection = pd.concat([df_selection, pd.DataFrame({k:[v] for k,v in zip(list(dic.keys())[1:], list(dic.values())[1:])})], axis=0, ignore_index=True)
    
            if st.button('Guardar Selección', key='save_selection_entry'):
                codes = df_selection['Código'].tolist()
                st.session_state.get_codes.append(codes)
                                    
# Integrar formulario para Frontline
with front:

    # Definir variables de categoría, nivel y consecutivo
    i = 2
    level = 2
    cat = 'front'

    # Dividir en tres columnas
    c1, c2, c3 = st.columns(3)
    
    # Definir input de Cargo, Nivel Salarial, Horas Asignadas
    c1.markdown('### Disponibilidad')
    frontline_job = c1.selectbox(label='Seleccionar cargo', options=[x for x in tribal_wl[(tribal_wl['Categoria']=='Frontline')]['Posicion'].unique()], key=f'job_{level}_{i}')
    
    # Integrar botón para consultar posiciones de Frontline
    c2.button('Consultar Posiciones', key='consult_frontline', on_click=callback_frontline)
    
    # Cargar información de capacidad instalada
    if st.session_state.button_clicked_frontline:
        df_capacity = get_installed_capacity(df, job=frontline_job, key=cat)
        selection = df_capacity['selected_rows']
        
        # Concatenar información a tabla SKUs
        df_selection = pd.DataFrame()
    
        if selection != []:
            for dic in selection:
                df_selection = pd.concat([df_selection, pd.DataFrame({k:[v] for k,v in zip(list(dic.keys())[1:], list(dic.values())[1:])})], axis=0, ignore_index=True)
    
            if st.button('Guardar Selección', key='save_selection_frontline'):
                codes = df_selection['Código'].tolist()
                st.session_state.get_codes.append(codes)
            
# Integrar formulario para Management
with manage:

    # Definir variables de categoría, nivel y consecutivo
    i = 3
    level = 3
    cat = 'manage'

    # Dividir en tres columnas
    c1, c2, c3 = st.columns(3)
    
    # Definir input de Cargo, Nivel Salarial, Horas Asignadas
    c1.markdown('### Disponibilidad')
    management_job = c1.selectbox(label='Seleccionar cargo', options=[x for x in tribal_wl[(tribal_wl['Categoria']=='Management')]['Posicion'].unique()], key=f'job_{level}_{i}')
    
    # Integrar botón para consultar posiciones de Management
    c2.button('Consultar Posiciones', key='consult_management', on_click=callback_management)
    
    # Cargar información de capacidad instalada
    if st.session_state.button_clicked_management:
        df_capacity = get_installed_capacity(df, job=management_job, key=cat)
        selection = df_capacity['selected_rows']
        
        # Concatenar información a tabla SKUs
        df_selection = pd.DataFrame()
        if selection != []:
            for dic in selection:
                df_selection = pd.concat([df_selection, pd.DataFrame({k:[v] for k,v in zip(list(dic.keys())[1:], list(dic.values())[1:])})], axis=0, ignore_index=True)
        
            if st.button('Guardar Selección', key='save_selection'):
                codes = df_selection['Código'].tolist()
                st.session_state.get_codes.append(codes)
                    
# Integrar formulario para Sr Management
with sr_manage:

    # Definir variables de categoría, nivel y consecutivo
    i = 4
    level = 4
    cat = 'sr_manage'

    # Dividir en tres columnas
    c1, c2, c3 = st.columns(3)
    
    # Definir input de Cargo, Nivel Salarial, Horas Asignadas
    c1.markdown('### Disponibilidad')
    sr_management_job = c1.selectbox(label='Seleccionar cargo', options=[x for x in tribal_wl[(tribal_wl['Categoria']=='Sr Management')]['Posicion'].unique()], key=f'job_{level}_{i}')

    # Integrar botón para consultar posiciones de Sr Management
    c2.button('Consultar Posiciones', key='consult_sr_management', on_click=callback_sr_management)
    
    # Cargar información de capacidad instalada
    if st.session_state.button_clicked_sr_management:            
        df_capacity = get_installed_capacity(df, job=sr_management_job, key=cat)
        selection = df_capacity['selected_rows']
        
        # Concatenar información a tabla SKUs
        df_selection = pd.DataFrame()
        if selection != []:
            for dic in selection:
                df_selection = pd.concat([df_selection, pd.DataFrame({k:[v] for k,v in zip(list(dic.keys())[1:], list(dic.values())[1:])})], axis=0, ignore_index=True)
        
            if st.button('Guardar Selección', key='save_selection'):
                codes = df_selection['Código'].tolist()
                st.session_state.get_codes.append(codes)

with sku_tab:
    # Dividir en tres columnas
    c1, c2, c3 = st.columns(3)
    
    # Definir input de Cargo, Nivel Salarial, Horas Asignadas
    c1.markdown('### Posiciones Seleccionadas del SKU')

    if c2.button('Mostrar Tabla SKU', key='sku_table'):
        
        # Obtener todos los códigos seleccionados
        all_codes_get = st.session_state.get_codes
        df_all_codes_get = pd.DataFrame({'Códigos':all_codes_get}).explode('Códigos').drop_duplicates(ignore_index=True)

        # Mostrar resultados
        columns = ['Código', 'Usuario', 'Correo electrónico', 'Puesto', 'Grupo', 'Proyecto', 'Capacidad Disponible', 'Porcentaje Horas Cargadas', 
                    'Porcentaje Horas Disponibles', 'Porcentaje Horas Desarrollo', 'Porcentaje Horas Gestión', 'Porcentaje Horas No Facturables']
        sku_df = df.loc[df['Código'].isin(df_all_codes_get['Códigos'].tolist()), columns].drop_duplicates(ignore_index=True).copy()
        sku_df['Categoria'] = sku_df.set_index('Puesto').index.map(tribal_wl.set_index('Posicion')['Categoria'])
        sku_df['Nivel'] = sku_df.set_index('Puesto').index.map(tribal_wl.set_index('Posicion')['Nivel'])
        columns = ['Código', 'Usuario', 'Correo electrónico', 'Nivel', 'Categoria', 'Puesto', 'Grupo', 'Proyecto', 'Capacidad Disponible', 
                    'Porcentaje Horas Cargadas', 'Porcentaje Horas Disponibles', 'Porcentaje Horas Desarrollo', 'Porcentaje Horas Gestión', 
                    'Porcentaje Horas No Facturables']
        sku_df = sku_df[columns].sort_values('Nivel')
        
        # Crear una tabla editable
        sku_table = AgGrid(sku_df)
    
    if c3.button('Limpiar Tabla', key='clean_sku_table'):
        st.session_state.get_codes = []


# Instanciar una variable con bytes de memoria para crear el archivo de trabajo
output = BytesIO() 
workbook = pd.ExcelWriter(output, engine='xlsxwriter')

# # Exportar archivo
# df = df.drop_duplicates()
# df.to_excel(workbook, sheet_name='Detalle 4', index=False)


# Guardar cambios y cerrar archivo
workbook.save()
st.download_button('📊 Descargar Usuarios Sin Código de Posición', output.getvalue(), file_name=f'Usuarios Sin Códigos de Posición.xlsx')
