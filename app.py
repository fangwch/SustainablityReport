# coding=utf-8

import time
from dotenv import load_dotenv
import streamlit as st
from streamlit.script_run_context import get_script_run_ctx
import pydeck as pdk
import altair as alt

load_dotenv(override=True)

NOW = str(time.time_ns())

ctx = get_script_run_ctx()
if ctx is not None:
  st.set_page_config(
    page_title='Sustainablity Report',
    page_icon=':earth:',
    layout='wide',
    initial_sidebar_state='auto'
  )

  from lib.utils import save_in_session_state
  from lib.data import clear_data, get_line_level_data, add_distribute_mode
  from lib.auth import login, verify, get_token

  if not verify(get_token()):
    st.text_input('Username', on_change=None, key='username')
    st.text_input(
      'Password', type='password', on_change=None, key='password'
    )
    st.button(label='Sign In', on_click=login)
    if 'access_token' in st.session_state:
      st.error('😕 User not known or password incorrect or session expired')
  else:
    # Initialize
    if 'exec_mode' not in st.session_state:
      exec_mode = False
    else:
      exec_mode = st.session_state['exec_mode']
    if 'preview_mode' not in st.session_state:
      preview_mode = False
    else:
      preview_mode = st.session_state['preview_mode']
    for key in ['order_line', 'uom_conversion', 'gps_location', 'distance']:
      if key not in st.session_state:
        st.session_state[key] = None

    order_line = st.session_state['order_line']
    uom_conversion = st.session_state['uom_conversion']
    gps_location = st.session_state['gps_location']
    distance = st.session_state['distance']

    if not exec_mode:
      # File Uploader
      with st.sidebar.container():
        st.file_uploader(
          label='Order Line File: ' + ('' if order_line is None else order_line.name),
          type=['csv'],
          accept_multiple_files=False,
          key='order_line_' + NOW,
          on_change=save_in_session_state,
          kwargs={
            'label': 'order_line',
            'key': 'order_line_' + NOW
          }
        )
        st.file_uploader(
          label='Unit Conversion File: ' + ('' if uom_conversion is None else uom_conversion.name),
          type=['csv'],
          accept_multiple_files=False,
          key='uom_conversion_' + NOW,
          on_change=save_in_session_state,
          kwargs={
            'label': 'uom_conversion',
            'key': 'uom_conversion_' + NOW
          }
        )
        st.file_uploader(
          label='GPS Location File: ' + ('' if gps_location is None else gps_location.name),
          type=['csv'],
          accept_multiple_files=False,
          key='gps_location_' + NOW,
          on_change=save_in_session_state,
          kwargs={
            'label': 'gps_location',
            'key': 'gps_location_' + NOW
          }
        )
        st.file_uploader(
          label='Shipping Distance File: ' + ('' if distance is None else distance.name),
          type=['csv'],
          accept_multiple_files=False,
          key='distance_' + NOW,
          on_change=save_in_session_state,
          kwargs={
            'label': 'distance',
            'key': 'distance_' + NOW
          }
        )
      # Preview and Execute Button
      with st.sidebar.container():
        left, middle, right = st.columns([1, 1, 1])
        middle.button('Reset', key='reset', on_click=clear_data)
        if order_line is None or uom_conversion is None or gps_location is None or distance is None:
          left.button('Preview', key='preview_mode', disabled=True)
          right.button('Execute', key='exec_mode_' + NOW, disabled=True)
        else:
          if preview_mode:
            left.button('Preview', key='preview_mode', disabled=True)
          else:
            left.button('Preview', key='preview_mode')
          right.button(
            'Execute',
            key='exec_mode_' + NOW,
            on_click=save_in_session_state,
            kwargs={
              'label': 'exec_mode',
              'key': 'exec_mode_' + NOW
            }
          )
      # Preview Table
      if preview_mode:
        with st.container():
          st.markdown('''
          ## :point_right: Order Line File:
          ''')
          st.write(order_line)
          st.markdown('''
          ---
          ''')
        with st.container():
          st.markdown('''
          ## :point_right: Unit Conversion File:
          ''')
          st.write(uom_conversion)
          st.markdown('''
          ---
          ''')
        with st.container():
          st.markdown('''
          ## :point_right: GPS Location File:
          ''')
          st.write(gps_location)
          st.markdown('''
          ---
          ''')
        with st.container():
          st.markdown('''
          ## :point_right: Shipping Distance File:
          ''')
          st.write(distance)
    else:
      order_level = st.selectbox(
        'Which Level(Line/Order) Would You Like To Download?',
        ('Line', 'Order'),
        0
      )
      left, _, right = st.columns([1, 8, 1])
      line_level_data = get_line_level_data(
        order_line, uom_conversion, gps_location, distance
      )
      if order_level == 'Order':
        order_level_data = line_level_data.drop(columns=['Conversion Ratio', 'Order Line Number', 'Units'])
        GPBY_ORDER = [
          'Date', 'Month-Year', 'Warehouse Code', 'Warehouse Name',
          'Warehouse Country', 'Warehouse City', 'Customer Code',
          'Customer Country', 'Customer City', 'Location', 'GPS 1', 'GPS 2',
          'Road', 'Rail', 'Sea', 'Air', 'Order Number'
        ]
        order_level_data = order_level_data.groupby(GPBY_ORDER).sum()
        order_level_data.reset_index(inplace=True)
        order_level_data = add_distribute_mode(order_level_data)
        right.download_button(
          'Download',
          data=order_level_data.to_csv().encode('utf-8'),
          file_name='order_level_data.csv',
          mime='text/csv'
        )
        # Display on Map, Group by Customer Location
        st.markdown('''
        ## :point_down: Display on Map, Group by Customer Location
        ---
        ''')
        order_level_data_copy = order_level_data.copy()
        order_level_data_copy = order_level_data_copy.groupby(by=['Location', 'GPS 1', 'GPS 2'])[['CO2 Total']].sum().reset_index()
        order_level_data_copy['coord'] = list(
          zip(order_level_data_copy['GPS 2'], order_level_data_copy['GPS 1'])
        )
        min_co2 = order_level_data_copy['CO2 Total'].min()
        max_co2 = order_level_data_copy['CO2 Total'].max()
        order_level_data_copy['radius'] = order_level_data_copy['CO2 Total'].apply(
          lambda value: int((value - min_co2)*10000/(max_co2 - min_co2)) + 2
        )
        st.pydeck_chart(
          pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
              latitude=48.8292604, longitude=2.0323494, zoom=5, pitch=0
            ),
            layers=[
              pdk.Layer(
                'HexagonLayer', data=order_level_data_copy, get_position='coord',
                radius=200, elevation_scale=4, elevation_range=[0, 1000], pickable=True, extruded=True,
              ),
              pdk.Layer(
                'ScatterplotLayer', data=order_level_data_copy,
                pickable=True, opacity=0.8, stroked=True, filled=True, radius_scale=6,
                radius_min_pixels=5, radius_max_pixels=100, line_width_min_pixels=1,
                get_position='coord', get_fill_color=[255, 140, 0], get_line_color=[0, 0, 0], get_radius='radius'
              )
            ]
          )
        )
      else:
        line_level_data = add_distribute_mode(line_level_data)
        right.download_button(
          'Download',
          data=line_level_data.to_csv().encode('utf-8'),
          file_name='line_level_data.csv',
          mime='text/csv'
        )
        # Display at Line Level
        st.markdown('''
        ## :point_down: Display at Line Level
        ---
        ''')
        line_level_data_copy = line_level_data.copy()[[
          'Euros', 'CO2 Total', 'Location', 'Order Number', 'Order Line Number', 'Item Code'
        ]]
        chart = alt.Chart(line_level_data_copy).mark_circle().encode(
          x='Euros', y='CO2 Total', size='CO2 Total', tooltip=[
            'Euros', 'CO2 Total', 'Location', 'Order Number', 'Order Line Number', 'Item Code'
          ]
        )
        st.altair_chart(chart, use_container_width=True)
      left.button('Home', key='homepage', on_click=clear_data)
