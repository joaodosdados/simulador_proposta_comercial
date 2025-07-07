# utils/styles/carbon.py
import streamlit as st


def carbon_header(title):
    """Cabeçalho no estilo Carbon Design System"""
    st.markdown(
        f"""
    <div style="
        background: #161616;
        color: white;
        padding: 0 1rem;
        height: 3rem;
        display: flex;
        align-items: center;
        margin: -1rem -1rem 1rem -1rem;
    ">
        <span style="font-weight: 600;">{title}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


def carbon_card(title, content, icon="•"):
    """Componente de card no estilo Carbon"""
    return f"""
    <div style="
        background: white;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    ">
        <h3 style="
            font-size: 1rem;
            font-weight: 600;
            color: #161616;
            margin-top: 0;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
        ">
            <span style="margin-right: 0.5rem;">{icon}</span>
            {title}
        </h3>
        <div style="color: #525252; font-size: 0.875rem;">
            {content}
        </div>
    </div>
    """
