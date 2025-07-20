import streamlit as st
from etapas import (
    diagnostico,
    objetivos,
    solucao_tecnica,
    cronograma,
    restricoes,
    encerramento,
)
from utils.navigation import render_sidebar, ETAPAS

st.set_page_config(page_title="SimulAItor - Simulador de Propostas", layout="wide")

# Cabeçalho do projeto
st.markdown("<h1 style='color:#0F62FE;'>SimulAItor </h1>", unsafe_allow_html=True)

# Renderiza sidebar estilizada
render_sidebar()

# Barra de progresso baseada na etapa
etapas_keys = list(ETAPAS.keys())
etapa_atual = st.session_state.get("etapa", "diagnostico")
indice = etapas_keys.index(etapa_atual)
st.progress(
    (indice + 1) / len(etapas_keys), text=f"Stage {indice + 1} de {len(etapas_keys)}"
)

# Executa etapa correspondente
ETAPAS_FUNCOES = {
    "diagnostico": diagnostico.render,
    "objetivos": objetivos.render,
    "solucao": solucao_tecnica.render,
    "cronograma": cronograma.render,
    "restricoes": restricoes.render,
    "encerramento": encerramento.render,
}
ETAPAS_FUNCOES[etapa_atual]()
