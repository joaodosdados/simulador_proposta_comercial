import streamlit as st


# utils/styles/components.py
def primary_button(label, key=None):
    """Botão primário no estilo Carbon"""
    return st.button(label, key=key, type="primary")
