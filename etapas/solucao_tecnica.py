# Pasta: etapas/
# Arquivo: solucao_tecnica.py
import streamlit as st
from utils.navigation import render_sidebar, ETAPAS
from utils.llm import gerar_resposta_ollama


def render():
    render_sidebar()
    st.subheader("🛠️ Etapa 3: Solução Técnica")

    objetivos_base = st.session_state.get("objetivos", "Objetivos ainda não definidos.")
    st.markdown("**Objetivos definidos:**")
    st.text_area("Objetivos:", value=objetivos_base, height=200, disabled=False)

    if st.button("⚙️ Gerar Solução Técnica com IA", key="btn_gerar_solucao"):
        with st.spinner("Gerando solução técnica com IA..."):
            prompt_solucao = f"""
            Você é um arquiteto de soluções. Com base nos objetivos abaixo, descreva uma proposta técnica de solução baseada em Data Science. Inclua tecnologias, abordagem, possíveis fontes de dados e etapas de desenvolvimento. Sugira também quais ferramentas, softwares ou frameworks da IBM poderiam ser utilizados.

            Objetivos:
            {objetivos_base}

            Responda com clareza, de forma estruturada.
            """
            solucao_gerada = gerar_resposta_ollama(prompt_solucao)
            st.session_state.solucao_tecnica = solucao_gerada
            st.success("Solução técnica gerada com sucesso!")

    st.markdown("**Solução Técnica Gerada:**")
    solucao = st.text_area(
        "Solução Técnica:",
        value=st.session_state.get("solucao_tecnica", ""),
        height=250,
    )
