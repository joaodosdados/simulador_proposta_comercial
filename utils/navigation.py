# utils/navigation.py
from streamlit_option_menu import option_menu
import streamlit as st

ETAPAS = {
    "proposta": "Proposal",
    "financeiro": "Cost Estimator",
    "restricoes": "Premissas e Limitações",
    "encerramento": "Resume",
}


def render_sidebar():
    labels = list(ETAPAS.values())
    chaves = list(ETAPAS.keys())
    etapa_atual = st.session_state.get("etapa", chaves[0])
    index_atual = chaves.index(etapa_atual)

    # Estilo customizado — remove scroll do menu para não cortar itens
    st.markdown(
        """
        <style>
        .sidebar-menu-wrapper h1 {
            font-size: 1.25rem;
            color: #0f62fe;
            margin-bottom: 1rem;
        }
        /* Give the option-menu iframe enough room for all 4 items + title */
        div[data-testid="stSidebar"] iframe {
            height: 420px !important;
            min-height: 420px !important;
        }
        /* Prevent parent containers from clipping the iframe */
        div[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stSidebar"] [data-testid="element-container"] {
            overflow: visible !important;
        }
        /* Prevent nav container from clipping menu items */
        div[data-testid="stSidebar"] nav.nav,
        div[data-testid="stSidebar"] .nav-justified,
        div[data-testid="stSidebar"] .nav-pills {
            max-height: none !important;
            overflow: visible !important;
        }
        /* Ensure long menu labels wrap instead of being truncated */
        div[data-testid="stSidebar"] .nav-link span {
            white-space: normal !important;
            word-wrap: break-word !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown('<div class="sidebar-menu-wrapper">', unsafe_allow_html=True)

        escolha_label = option_menu(
            menu_title="CostWise AI",
            options=labels,
            icons=[
                "pencil-square",
                "calculator",
                "exclamation-triangle",
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
