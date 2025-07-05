from etapas import (
    diagnostico,
    objetivos,
    solucao_tecnica,
    cronograma,
    restricoes,
    encerramento,
)

import streamlit as st

st.set_page_config(page_title="Simulador de Propostas DS", layout="wide")

ETAPAS_FUNCOES = {
    "diagnostico": diagnostico.render,
    "objetivos": objetivos.render,
    "solucao": solucao_tecnica.render,
    "cronograma": cronograma.render,
    "restricoes": restricoes.render,
    "encerramento": encerramento.render,
    # outras etapas a seguir...
}

etapa_atual = st.session_state.get("etapa", "diagnostico")
ETAPAS_FUNCOES[etapa_atual]()
