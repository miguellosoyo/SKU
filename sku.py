# Importar librerías de trabajo
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
import streamlit as st
import pandas as pd
import numpy as np
import time
import os 

# Definir una función para crear una tabla con el nivel, código de posición y salario local y borderless
# def salary_levels(df:pd.DataFrame):
#     '''
#     Esta función transforma una tabla con niveles de posición, 
#     '''

# Definir función para cargar información
@st.cache
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

# Definir directorio de trabajo
os.chdir(r'C:\Users\Miguel\Documents\Documentos Servicio Social\Documentos Tribal\Operaciones')

# Cargar información de Tribal
tribal_wl = pd.read_excel('Bandas Salariales.xlsx')

# Cargar información del Roster de Tribal
tribal_rt = pd.read_excel('Roster Tribal.xlsx', skiprows=1)

# Instanciar DataFrame vacío para guardar información del SKU
sku_df = pd.DataFrame()

# Predefinir las pestañas a emplear
tab_1, tab_2, tab_3 = st.tabs(['SKU', 'Presupuesto Comercial', 'Costos Laborales'])

# Integrar factores de selección para el SKU
with tab_1:

    # Integrar título de la barra lateral
    st.header('⚙️ Stock Keeping Unit')

    # Insertar filtro para los distintos niveles
    levels_cat = tribal_wl['Categoria'].unique().tolist()
    levels = tribal_wl['Nivel'].unique().tolist()
    
    # Definir las pestañas para cada categoría de nivel
    entry, front, manage, sr_manage = st.tabs(levels_cat)
    
    # Integrar formulario para Entry Level
    with entry:

        # Definir variables de categoría, nivel y consecutivo
        i = 1
        level = 1
        cat = 'entry'

        # Dividir en tres columnas
        c1, c2, c3 = st.columns(3)
        
        # Definir input de Cargo, Nivel Salarial, Horas Asignadas 
        job = c1.selectbox(label='Seleccionar cargo', options=[x.title() for x in tribal_wl[(tribal_wl['Categoria']=='Entry Level')]['Posicion'].unique()], key=f'job_{level}_{i}')
        salary_range = c2.selectbox(label='Seleccionar rango salarial', options=list('ABC'), key=f'salary_{level}_{i}')
        hours = int(c3.number_input(label='Ingresar horas estimadas', step=1, key=f'hours_{level}_{i}'))
        
        # Definir una lista con los valores
        values = pd.DataFrame({'Puesto':[job], 'Rango Salario':[salary_range], 'Horas Asignadas':[hours]})

        # Integrar botón de carga
        entry_load = st.button('Cargar', key=f'button_{cat}')

        # Evaluar si se ha accionado el botón de carga
        if entry_load:

            # Integrar al DataFrame de SKU
            sku_df = load_sku(values)
        
    # Integrar formulario para Frontline
    with front:

        # Definir variables de categoría, nivel y consecutivo
        i = 2
        level = 2
        cat = 'front'

    
        # Dividir en tres columnas
        c1, c2, c3 = st.columns(3)
        
        # Definir input de Cargo, Nivel Salarial, Horas Asignadas 
        job = c1.selectbox(label='Seleccionar cargo', options=[x.title() for x in tribal_wl[(tribal_wl['Categoria']=='Frontline')]['Posicion'].unique()], key=f'job_{level}_{i}')
        salary_range = c2.selectbox(label='Seleccionar rango salarial', options=list('ABC'), key=f'salary_{level}_{i}')
        hours = int(c3.number_input(label='Ingresar horas estimadas', step=1, key=f'hours_{level}_{i}'))
        
        # Definir una lista con los valores
        values = pd.DataFrame({'Puesto':[job], 'Rango Salario':[salary_range], 'Horas Asignadas':[hours]})

        # Integrar botón de carga
        front_load = st.button('Cargar', key=f'button_{cat}')

        # Evaluar si se ha accionado el botón de carga
        if front_load:

            # Integrar al DataFrame de SKU
            sku_df = load_sku(values)

    # Integrar formulario para Management
    with manage:

        # Definir variables de categoría, nivel y consecutivo
        i = 3
        level = 3
        cat = 'manage'

        # Dividir en tres columnas
        c1, c2, c3 = st.columns(3)
        
        # Definir input de Cargo, Nivel Salarial, Horas Asignadas 
        job = c1.selectbox(label='Seleccionar cargo', options=[x.title() for x in tribal_wl[(tribal_wl['Categoria']=='Management')]['Posicion'].unique()], key=f'job_{level}_{i}')
        salary_range = c2.selectbox(label='Seleccionar rango salarial', options=list('ABC'), key=f'salary_{level}_{i}')
        hours = int(c3.number_input(label='Ingresar horas estimadas', step=1, key=f'hours_{level}_{i}'))
        
        # Definir una lista con los valores
        values = pd.DataFrame({'Puesto':[job], 'Rango Salario':[salary_range], 'Horas Asignadas':[hours]})

        # Integrar botón de carga
        manage_load = st.button('Cargar', key=f'button_{cat}')

        # Evaluar si se ha accionado el botón de carga
        if manage_load:

            # Integrar al DataFrame de SKU
            sku_df = load_sku(values)
    
    # Integrar formulario para Sr Management
    with sr_manage:

        # Definir variables de categoría, nivel y consecutivo
        i = 4
        level = 4
        cat = 'sr_manage'

        # Dividir en tres columnas
        c1, c2, c3 = st.columns(3)
        
        # Definir input de Cargo, Nivel Salarial, Horas Asignadas 
        job = c1.selectbox(label='Seleccionar cargo', options=[x.title() for x in tribal_wl[(tribal_wl['Categoria']=='Sr Management')]['Posicion'].unique()], key=f'job_{level}_{i}')
        salary_range = c2.selectbox(label='Seleccionar rango salarial', options=list('ABC'), key=f'salary_{level}_{i}')
        hours = int(c3.number_input(label='Ingresar horas estimadas', step=1, key=f'hours_{level}_{i}'))
        
        # Definir una lista con los valores
        values = pd.DataFrame({'Puesto':[job], 'Rango Salario':[salary_range], 'Horas Asignadas':[hours]})

        # Integrar botón de carga
        sr_manage_load = st.button('Cargar', key=f'button_{cat}')

        # Evaluar si se ha accionado el botón de carga
        if sr_manage_load:

            # Integrar al DataFrame de SKU
            sku_df = load_sku(values)

    # Integrar botón para generar reporte PDF del SKU cargado
    report = st.button('Generar Reporte', key='report') 

AgGrid(sku_df.head())

# Seleccionar variables de interés
columns = ['Posicion', '']

# Filtrar niveles en tabla de rangos salariales
tribal_wl = tribal_wl[tribal_wl['Nivel'].isin(levels)].reset_index(drop=True)

# Obtener los códigos de puesto de la tabla de rangos salariales
# ght_codes = tribal_wl['']

# Filtrar códigos GTH en tabla roster
# tribal_rt =



# AgGrid(tribal_rt.head())

