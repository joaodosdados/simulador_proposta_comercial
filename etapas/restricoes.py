# Pasta: etapas/
# Arquivo: restricoes.py
import streamlit as st
from utils.navigation import render_sidebar
from utils.llm import gerar_resposta_ollama


def render():
    st.markdown(
        """
    <style>
        .header-section {
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #161616;
            margin: 1rem 0 0.5rem;
        }
        .info-card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .comparison-container {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .stButton>button {
            width: 100%;
            padding: 0.75rem;
            border-radius: 8px;
            background-color: #0f62fe;
            color: white;
            border: none;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #0353e9;
        }
        .comparison-panel {
            flex: 1;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            height: 300px;
            overflow-y: auto;
        }
        .comparison-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #0f62fe;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
    st.subheader("⚠️ Etapa 6: Premissas e Limitações")

    objetivos = st.session_state.get("objetivos", "Objetivos não definidos.")
    solucao = st.session_state.get("solucao_tecnica", "Solução técnica não definida.")

    st.text_area("Objetivos do Projeto:", value=objetivos, height=150, disabled=False)
    st.text_area("Solução Técnica:", value=solucao, height=150, disabled=False)

    if st.button("⚙️ Gerar Premissas e Limitações com IA"):
        with st.spinner("Gerando recomendações de premissas e limitações..."):
            prompt = f"""
            Você é um consultor especialista em propostas técnicas de Data Science. Seu papel é identificar premissas técnicas e operacionais, bem como limitações e riscos para um projeto.

            Use os objetivos e a solução técnica abaixo como base:

            Objetivos:
            {objetivos}

            Solução Técnica:
            {solucao}

            Liste:
            - Premissas operacionais (dados, acessos, permissões, sistemas...)
            - Limitações do escopo (integrações, sistemas legados, não inclusões...)
            - Alertas de risco e salvaguardas contratuais
            """

            resultado = gerar_resposta_ollama(prompt)
            st.session_state.premissas_limitacoes = resultado
            st.success("Texto gerado com sucesso!")

    texto = st.session_state.get("premissas_limitacoes", "")
    st.markdown("**Premissas e Limitações:**")
    st.text_area(
        "Resultado:", value=texto, height=300, key="textarea_restricoes", disabled=False
    )

    if st.button("🔁 Atualizar Texto"):
        st.session_state.premissas_limitacoes = st.session_state.textarea_restricoes
