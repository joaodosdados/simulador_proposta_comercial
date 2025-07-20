# Pasta: etapas/
# Arquivo: restricoes.py
import streamlit as st
from utils.navigation import render_sidebar
from utils.llm import gerar_resposta_watsonx


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
    st.subheader("⚠️ Stage 6: Premises and Limitations")

    objetivos = st.session_state.get("objetivos", "Undefined objectives.")
    solucao = st.session_state.get("solucao_tecnica", "Technical solution not defined.")

    st.text_area("Project Objective:", value=objetivos, height=150, disabled=False)
    st.text_area("Technical Solution:", value=solucao, height=150, disabled=False)

    if st.button("⚙️ Generating Assumptions and Constraints with AI"):
        with st.spinner(
            "Generating recommendations from assumptions and limitations..."
        ):
            prompt = f"""
            You are a consultant specializing in technical Data Science proposals. Your role is to identify technical and operational assumptions, as well as limitations and risks for a project.

            Use the objectives and technical solution below as your basis:

            Objectives:
            {objetivos}

            Technical Solution:
            {solucao}

            List:
            - Operational assumptions (data, access, permissions, systems, etc.)
            - Scope limitations (integrations, legacy systems, exclusions, etc.)
            - Risk alerts and contractual safeguards
            - Compliance and data protection aspects (e.g., GDPR, LGPD), highlighting risks and recommendations

            Return the text in formal US English.
            """

            resultado = gerar_resposta_watsonx(prompt)
            if resultado:
                st.session_state.premissas_limitacoes = resultado
                st.success("✅ Text generated successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to generate text.")

    texto = st.session_state.get("premissas_limitacoes", "")
    st.markdown("**Premises and Limitations:**")
    premissas_texto = st.text_area(
        "Premises and Limitations:",
        value=st.session_state.get("premissas_limitacoes", ""),
        height=300,
        key="textarea_premissas",
    )

    if premissas_texto != st.session_state.get("premissas_limitacoes", ""):
        st.session_state.premissas_limitacoes = premissas_texto
