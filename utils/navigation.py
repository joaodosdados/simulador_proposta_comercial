# utils/navigation.py
from streamlit_option_menu import option_menu
import streamlit as st

ETAPAS = {
    "diagnostico": "Diagnóstico",
    "objetivos": "Objetivos",
    "solucao": "Solução Técnica",
    "cronograma": "Cronograma",
    "restricoes": "Premissas e Limitações",
    "encerramento": "Encerramento",
}


def render_sidebar():
    labels = list(ETAPAS.values())  # nomes visuais
    chaves = list(ETAPAS.keys())  # ids internos

    etapa_atual = st.session_state.get("etapa", chaves[0])
    index_atual = chaves.index(etapa_atual)

    with st.sidebar:
        escolha_label = option_menu(
            menu_title="SimulAI",
            options=labels,
            icons=[
                "search",
                "bullseye",
                "tools",
                "calendar",
                "exclamation",
                "check2-circle",
            ],
            menu_icon="cast",
            default_index=index_atual,
            styles={
                "container": {"padding": "0!important", "background-color": "#FFFFFF"},
                "icon": {"color": "#0F62FE", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "2px",
                    "--hover-color": "#E5E5E5",
                },
                "nav-link-selected": {
                    "background-color": "#D0E2FF",
                    "font-weight": "bold",
                },
            },
        )

    # Encontra chave correspondente ao label escolhido
    for chave, label in ETAPAS.items():
        if label == escolha_label:
            if chave != st.session_state.get("etapa"):
                st.session_state.etapa = chave
                st.rerun()
            break
