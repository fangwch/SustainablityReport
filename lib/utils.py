# coding=utf-8

import streamlit as st
import pandas as pd
from streamlit.uploaded_file_manager import UploadedFile

def save_in_session_state(*_, **kwargs):
  label = kwargs['label']
  key = kwargs['key']
  if isinstance(st.session_state[key], (UploadedFile,)):
    st.session_state[label] = pd.read_csv(
      st.session_state[key], header=0, index_col=0
    )
    st.session_state[label].name = st.session_state[key].name
  else:
    st.session_state[label] = st.session_state[key]
