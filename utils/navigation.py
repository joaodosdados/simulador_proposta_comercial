# utils/navigation.py
import streamlit as st

ETAPAS = {
    "diagnostico": "🔍 Diagnóstico",
    "objetivos": "🎯 Objetivos",
    "solucao": "🛠️ Solução Técnica",
    "cronograma": "🗓️ Cronograma",
    "restricoes": "⚠️ Premissas e Limitações",
    "encerramento": "✅ Encerramento",
}


def render_sidebar():
    st.sidebar.title("📌 Navegação")
    escolha = st.sidebar.radio(
        "Ir para etapa:",
        options=list(ETAPAS.keys()),
        format_func=lambda k: ETAPAS[k],
    )
    if escolha != st.session_state.get("etapa"):
        st.session_state.etapa = escolha
        st.rerun()
