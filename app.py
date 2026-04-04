import streamlit as st
from etapas import (
    etapa_proposta,
    etapa_financeiro,
    restricoes,
    encerramento,
)
from utils.navigation import render_sidebar, ETAPAS

st.set_page_config(page_title="CostWise AI", layout="wide")

# Cabeçalho do projeto
st.markdown("<h1 style='color:#0F62FE;'>CostWise AI</h1>", unsafe_allow_html=True)

# Renderiza sidebar estilizada
render_sidebar()

# Barra de progresso baseada na etapa
etapas_keys = list(ETAPAS.keys())
etapa_atual = st.session_state.get("etapa", "proposta")
indice = etapas_keys.index(etapa_atual)
st.progress(
    (indice + 1) / len(etapas_keys), text=f"Stage {indice + 1} de {len(etapas_keys)}"
)

# Executa etapa correspondente
ETAPAS_FUNCOES = {
    "proposta": etapa_proposta.render,
    "financeiro": etapa_financeiro.render,
    "restricoes": restricoes.render,
    "encerramento": encerramento.render,
}
ETAPAS_FUNCOES[etapa_atual]()
