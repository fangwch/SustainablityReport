# coding=utf-8

import pandas as pd
import streamlit as st

MODES = ['Road', 'Rail', 'Sea', 'Air']
CO2E = dict(zip(['Air', 'Sea', 'Road', 'Rail'], [2.1, 0.01, 0.096, 0.028]))

def clear_data():
  for key in ['order_line', 'uom_conversion', 'gps_location', 'distance']:
    if key in st.session_state:
      del st.session_state[key]
  if 'exec_mode' in st.session_state:
    del st.session_state['exec_mode']

@st.cache
def get_line_level_data(order_line, uom_conversion, gps_location, distance):
  # Read all file
  order_line = order_line.copy()
  uom_conversion = uom_conversion.copy()
  gps_location = gps_location.copy()
  distance = distance.copy()
  # # Analysis
  # Step 1
  df_join = pd.merge(order_line, uom_conversion, on=['Item Code'], how='left', suffixes=('', '_y'))
  df_join.drop(df_join.filter(regex='_y$').columns.tolist(),axis=1, inplace=True)
  # Step 2
  distance['Location'] = distance['Customer Country'].astype(str) + ', ' + distance['Customer City'].astype(str)
  df_dist = pd.merge(distance, gps_location, on='Location', how='left', suffixes=('', '_y'))
  df_dist.drop(df_dist.filter(regex='_y$').columns.tolist(),axis=1, inplace=True)
  # Step 3
  df_join = pd.merge(df_join, df_dist, on = ['Warehouse Code', 'Customer Code'], how='left', suffixes=('', '_y'))
  df_join.drop(df_join.filter(regex='_y$').columns.tolist(),axis=1, inplace=True)
  # Step 4
  df_join['KG'] = df_join['Units'] * df_join['Conversion Ratio']
  for mode in MODES:
    df_join['CO2 ' + mode] = df_join['KG'].astype(float)/1000 * df_join[mode].astype(float) * CO2E[mode]
  df_join['CO2 Total'] = df_join[['CO2 ' + mode for mode in MODES]].sum(axis = 1)
  return df_join

def add_distribute_mode(data):
  data = data.copy()
  data['Delivery Mode'] = data[MODES].astype(
    float
  ).apply(lambda t: [mode if t[mode] > 0 else '-' for mode in MODES], axis=1)
  dict_map = dict(
    zip(
      data['Delivery Mode'].astype(str).unique(), [
        i.replace(", '-'", '').replace("'-'", '').replace("'", '')
        for i in data['Delivery Mode'].astype(str).unique()
      ]
    )
  )
  data['Delivery Mode'] = data['Delivery Mode'].astype(
    str
  ).map(dict_map)
  return data
