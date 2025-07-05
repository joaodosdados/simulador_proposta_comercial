import streamlit as st
from utils.ai_agent import agente_identifica_oportunidades
from utils.navigation import render_sidebar, ETAPAS


def render():
    render_sidebar()
    st.subheader("🎯 Etapa 2: Objetivos do Projeto")

    qtd = st.session_state.get("qtd_oportunidades", 0)
    st.markdown(f"**Número de oportunidades identificadas:** `{qtd}`")

    texto_base = st.session_state.get(
        "resultado_diagnostico", "Diagnóstico ainda não definido."
    )
    st.markdown("**Baseado no diagnóstico anterior:**")
    st.text_area("Diagnóstico:", value=texto_base, height=200, disabled=False)

    if st.button("⚙️ Gerar Objetivos com IA", key="btn_gerar_objetivos"):
        with st.spinner("Gerando objetivos com IA..."):
            prompt_objetivos = f"""
                            Você é um consultor técnico. Com base nas oportunidades abaixo, gere uma lista de objetivos estratégicos e técnicos para o projeto de Data Science.

                            As oportunidades foram:
                            "{texto_base}"

                            Liste entre 3 e 6 objetivos práticos, claros e conectados ao conteúdo.
                            """
            objetivos_gerados = agente_identifica_oportunidades(prompt_objetivos)
            st.session_state.objetivos = objetivos_gerados
            st.success("Objetivos gerados com sucesso!")

    st.markdown("**Objetivos identificados:**")
    objetivos = st.text_area(
        "Objetivos:", value=st.session_state.get("objetivos", ""), height=200
    )
