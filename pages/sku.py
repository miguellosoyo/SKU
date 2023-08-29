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
import data
import time
import pytz
import io
import os

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
tribal_wl, tribal_rt, df, out = data.load_data()

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
        
        df_capacity = data.get_installed_capacity(df, job=entry_job, key=cat)
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
        df_capacity = data.get_installed_capacity(df, job=frontline_job, key=cat)
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
        df_capacity = data.get_installed_capacity(df, job=management_job, key=cat)
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
        df_capacity = data.get_installed_capacity(df, job=sr_management_job, key=cat)
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