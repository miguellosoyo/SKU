# Importar librerías de trabajo
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
from datetime import datetime as dt, timedelta
from streamlit_echarts import st_echarts
from streamlit_echarts import JsCode
import plotly.graph_objects as go
from itertools import chain
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

# Definir una función que ilumine una fila sí y otra no de un color en específico
def highlight(x):

  # Definir los colores para las filas impares y pares
  c1 = 'background-color: #dedede'
  c2 = 'background-color: white'

  # Definir un DataFrame con el mapeo de los colores
  df1 = pd.DataFrame('', index=x.index, columns=x.columns)
  df1.loc[df1.index%2!=0, :] = c2
  df1.loc[df1.index%2==0, :] = c2

  return df1

def highlight_percent_cells(val):
    color = '#96ebad' if float(val[:-1]) >=0 and float(val[:-1])<=24.99 else ('#ebe196' if float(val[:-1])>=25 and float(val[:-1])<=34.99 else '#eb9696')
    return 'background-color: {}'.format(color)

# Definir la página que corresponde el SKU
st.set_page_config(page_title='SKU - Stock Keeping Unit for TWW Positions', page_icon=':bar_chart:', layout='wide')

# Cargar información de todas las posiciones
tribal_wl, tribal_rt, labor_costs, out = data.load_data()
df_budgets_ok, detail_labor_costs = data.load_finance_data(labor_costs)
projects = df_budgets_ok['Proyecto'].unique()

# Definir las pestañas para cada categoría de nivel
sections = ['Escenario General', 'Detalle por Proyecto']
general, detail = st.tabs(sections)

# Integrar formulario para Entry Level
with general:
    
    # Definir input de Cargo, Nivel Salarial, Horas Asignadas
    st.markdown('### Escenario General')
    
    # Dividir en tres columnas
    c1, c2, c3, c4 = st.columns(4)
    income = (df_budgets_ok['Valor_Subtotal'].sum()) / 1e6
    c1.metric(label='Ingresos Totales', value=f'Q {income:,.2f} M')
    net_profits = (df_budgets_ok['Utilidad Neta'].sum()) / 1e3
    c2.metric(label='Utilidad Neta', value=f'Q {net_profits:,.2f} K')
    margin = (net_profits * 1e3) / (income * 1e6)
    c3.metric(label='Rendimiento Neto', value=f'{margin*100:,.2f}%')
    
    # Definir las especificaciones de una gráfica de barras apiladas 
    incomes = df_budgets_ok['Valor_Subtotal'].tolist()
    profits = [df_budgets_ok.loc[df_budgets_ok['Proyecto']==x, 'Utilidad Neta'].tolist()[-1] if df_budgets_ok.loc[df_budgets_ok['Proyecto']==x, 'Utilidad Neta'].tolist()[-1]>=0 else None for x in projects]
    losses = [df_budgets_ok.loc[df_budgets_ok['Proyecto']==x, 'Utilidad Neta'].tolist()[-1] if df_budgets_ok.loc[df_budgets_ok['Proyecto']==x, 'Utilidad Neta'].tolist()[-1]<=0 else None for x in projects]
    
    option = {
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
            'type': 'shadow'
            }
            },
        'legend': {},
        'grid': {
            'left': '3%',
            'right': '4%',
            'bottom': '3%',
            'containLabel': True
            },
        'xAxis': {
            'type': 'value'
            },
        'yAxis': {
            'type': 'category',
            'data': list(projects)
            },
        'series': [
            {'name': 'Ingresos por Proyecto',
             'type': 'bar',
             'label': {
                 'show': False
                 },
            'color':  'black',
             'emphasis': {
                 'focus': 'series'
                 },
             'data': [round(x, 2) for x in incomes]
             },
            {'name': 'Utilidad', 
             'type': 'bar', 
             'label': {
                 'show': False,
                 'formatter': ','
                 },
             'color':  '#339900',
             'emphasis': {
                 'focus': 'series'
                 },
            'data': [round(x, 2) if x!=None else x for x in profits]
            },
            {'name': 'Pérdida', 
             'type': 'bar', 
             'label': {
                 'show': False,
                 'formatter': ','
                 },
             'color':  'red',
             'emphasis': {
                 'focus': 'series'
                 },
            'data': [round(x, 2) if x!=None else x for x in losses]
            },
                      
        ]
        }
        
    # Integrar gráfica de barras
    st_echarts(options=option, height="400px")

with detail:
    
    # Visualización en Streamlit
    st.write("# Resultados Financieros del Proyecto")
    c1, c2 = st.columns(2)
    selection_project = c1.selectbox(label='Seleccionar Proyecto', options=projects, key=f'list_projects')
    
    # Seleccionamos las columnas relevantes
    selected_columns = ['Proyecto', 'Valor_Subtotal', 'Costo_Externo', 'Utilidad Bruta', 'Freelance', 'Pago De Licencias Y Aplicativos', 'Gastos Administrativos', 'Costos Indirectos', 'Costo Total No Facturables Q', 'Costo Total GTH Q', 'Costo Total Desarrollo Q', 'Costo Total Gestión Q', 'Utilidad Neta']
    df_project_sheet = df_budgets_ok.loc[df_budgets_ok['Proyecto']==selection_project, selected_columns].copy()
    df_transposed = df_project_sheet.drop(columns='Proyecto').transpose().reset_index().round(2)
    df_transposed.columns = ['Conceptos', 'Valores',]
    df_transposed['Conceptos'] = df_transposed['Conceptos'].str.replace(' Q', '')
    df_transposed['Porcentajes'] = df_transposed['Valores'].div(df_transposed.loc[df_transposed['Conceptos']=='Valor_Subtotal', 'Valores'].sum())
    df_transposed['Valores'] = df_transposed['Valores'].apply(lambda x : 'Q {:,}'.format(x))
    df_transposed['Conceptos'] = df_transposed['Conceptos'].str.replace('Valor_Subtotal', 'Presupuesto Vendido').replace('Costo_Externo', 'Costos Externos')
        
    # Aplicar el formato definido en el caso respectivo, y esconder el índice de números consecutivos
    df_transposed = df_transposed.style.apply(highlight, axis=None).applymap(highlight_percent_cells, subset=['Porcentajes']).set_properties(**{'font-size': '10pt', 'font-family': 'monospace', 'border': '', 'width': '60%'}).format(format)
    df_transposed.data['Porcentajes'] = df_transposed.data['Porcentajes'].apply(lambda x : '{:.2%}'.format(x))
    
    # Definir las propiedades de estilo para los encabezados
    th_props = [
                ('font-size', '14pt'),
                ('text-align', 'center'),
                ('font-weight', 'bold'),
                ('color', 'white'),
                ('background-color', '#404040'),
                ('width', '40%'),
                ]

    # Definir las propiedades de estilo para la información de la tabla
    td_props = [
                ('font-size', '10pt'),
                ('width', '40%'),
                ('text-align', 'center'),
                ('border', '0.1px solid white'),
                ]

    # Integrar los estilos en una variable de estilos
    styles = [
            dict(selector='th', props=th_props),
            dict(selector='td', props=td_props),
            {'selector':'.line', 'props':'border-bottom: 1.5px solid #000066'},
            {'selector':'.False', 'props':'color: black'},
            {'selector':'.Margin', 'props':[('font-weight', 'bold'), ('font-size', '12pt'), ('background-color', '#f2f2f2')]},
            {'selector':'.w', 'props':[('background-color','white'), ('color','black')]},
            ]

    # Integrar líneas si el índice corresponde a una posición de la tabla
    cell_border = pd.DataFrame([['line']*len(x) if i in [1, 10] else ['']*len(x) for i, x in df_transposed.data.iterrows()], columns=df_transposed.data.columns)
    cell_margin = pd.DataFrame([x.notnull().astype(str).replace('True', 'w').tolist() if i==0 else (x.notnull().astype(str).replace('True', 'Margin').tolist() if i in [2, 11] else ['False']*len(x)) for i, x in df_transposed.data.iterrows()], columns=df_transposed.data.columns)

    # Aplicar formatos sobre las clases definidas
    df_transposed = df_transposed.set_table_styles(styles).set_td_classes(cell_margin).set_td_classes(cell_border)

    # Filtrar proyecto
    columns = ['Proyecto', 'Usuario', 'Costo Total Desarrollo Q', 'Costo Total Gestión Q', 'Costo Total No Facturables Q', 'Costo Total GTH Q']
    df_detail_project_costs = detail_labor_costs.loc[detail_labor_costs['Proyecto']==selection_project, columns]
    columns = ['Costo Total Desarrollo Q', 'Costo Total Gestión Q', 'Costo Total No Facturables Q', 'Costo Total GTH Q']
    df_detail_project_costs[columns] = df_detail_project_costs  [columns].applymap(lambda x: 'Q {:,}'.format(x))
    df_detail_project_costs = df_detail_project_costs.style.apply(highlight, axis=None).set_properties(**{'font-size': '10pt', 'font-family': 'monospace', 'border': '', 'width': '60%'}).format(format)
    
    # Integrar líneas si el índice corresponde a una posición de la tabla
    cell_border = pd.DataFrame([['line']*len(x) if i in [1, 10] else ['']*len(x) for i, x in df_transposed.data.iterrows()], columns=df_transposed.data.columns)
    cell_margin = pd.DataFrame([x.notnull().astype(str).replace('True', 'w').tolist() if i==0 else (x.notnull().astype(str).replace('True', 'Margin').tolist() if i in [2, 11] else ['False']*len(x)) for i, x in df_transposed.data.iterrows()], columns=df_transposed.data.columns)
    
    # Aplicar formatos sobre las clases definidas
    df_detail_project_costs = df_detail_project_costs.set_table_styles(styles).set_td_classes(cell_margin).set_td_classes(cell_border)

    # Definir formato CSS para eliminar los índices de la tabla, centrar encabezados, aplicar líneas de separación y cambiar tipografía
    hide_table_row_index = """
                            <style>
                            tbody th {display:none;}
                            .blank {display:none;}
                            .col_heading {font-family: monospace; border: 3px solid white; text-align: center !important;}
                            </style>
                        """
    hide_table_row_index = """
                            <style>
                            tbody th {display:none;}
                            .blank {display:none;}
                            .col_heading {font-family: monospace; text-align: center !important;}
                            </style>
                        """

    # Integrar el CSS con Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)

    # Integrar el DataFrame a la aplicación Web
    c1.markdown(df_transposed.to_html(), unsafe_allow_html=True)

    # Insertar una nota al pie de la tabla
    c1.caption(f'Cifras expresadas en quetzales.')

    # Obtener gráfico de costos
    options_half_doughnut = data.half_doughnut(df_transposed.data)
    with c2:
        st_echarts(options=options_half_doughnut, height="600px")
    
    # Integrar el DataFrame a la aplicación Web
    # c1.markdown(df_detail_project_costs.to_html(), unsafe_allow_html=True)

    # Insertar una nota al pie de la tabla
    # c1.caption(f'Cifras expresadas en quetzales.')
    
    # Instanciar una variable con bytes de memoria para crear el archivo de trabajo
    output = BytesIO() 
    workbook = pd.ExcelWriter(output, engine='xlsxwriter')

    # Exportar archivo
    df_transposed.to_excel(workbook, sheet_name='Datos', index=False)

    # Guardar cambios y cerrar archivo
    workbook.save()
    st.download_button('📊 Descargar P&L del Proyecto', output.getvalue(), file_name=f'P & L {selection_project}.xlsx')
            
        
