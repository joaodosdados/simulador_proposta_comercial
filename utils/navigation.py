# utils/navigation.py
from streamlit_option_menu import option_menu
import streamlit as st

ETAPAS = {
    "diagnostico": "Diagnostics",
    "objetivos": "Objectives",
    "solucao": "Tecnical Solution",
    "cronograma": "Timeline",
    "restricoes": "Premises and Limitations",
    "encerramento": "Resume",
}


def render_sidebar():
    labels = list(ETAPAS.values())
    chaves = list(ETAPAS.keys())
    etapa_atual = st.session_state.get("etapa", chaves[0])
    index_atual = chaves.index(etapa_atual)

    # Estilo customizado
    st.markdown(
        """
        <style>
        .sidebar-menu-wrapper h1 {
            font-size: 1.25rem;
            color: #0f62fe;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown('<div class="sidebar-menu-wrapper">', unsafe_allow_html=True)

        escolha_label = option_menu(
            menu_title="SimulAItor",
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
                "container": {
                    "padding": "0!important",
                    "background-color": "transparent",
                },
                "icon": {"color": "#0F62FE", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "4px 0",
                    "color": "#161616",
                    "border-radius": "8px",
                    "padding": "8px 12px",
                },
                "nav-link-selected": {
                    "background-color": "#D0E2FF",
                    "font-weight": "bold",
                    "color": "#0F62FE",
                },
            },
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # Atualiza etapa
    for chave, label in ETAPAS.items():
        if label == escolha_label:
            if chave != st.session_state.get("etapa"):
                st.session_state.etapa = chave
                st.rerun()
            break
