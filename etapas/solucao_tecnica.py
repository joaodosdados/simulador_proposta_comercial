# Pasta: etapas/
# Arquivo: solucao_tecnica.py
import streamlit as st
from utils.navigation import render_sidebar, ETAPAS
from utils.llm import gerar_resposta_ollama, gerar_resposta_watsonx


def render():
    # Configuração de estilo
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
    st.subheader("🛠️ Etapa 3: Technical Solution")

    objetivos_base = st.session_state.get("objetivos", "Objectives not yet defined.")
    st.markdown("**Defined objectives:**")
    st.text_area("Objectivies:", value=objetivos_base, height=300, disabled=False)

    if st.button("⚙️ Generate Technical Solution with AI", key="btn_gerar_solucao"):
        with st.spinner("Generating technical solutions with AI..."):
            prompt_solucao = f"""
            You are a solutions architect. Based on the objectives below, describe a **technical solution** for each objective, using Data Science.

            Objectives:
            {objetivos_base}

            Rules:
            - For EACH objective, provide:
                1. Objective (short description)
                2. Technical Solution (approach or method to achieve the objective)
                3. Recommended Tools/Frameworks (including IBM tools when applicable, or compatible open-source tools)
                4. Main Development Steps (4 steps only, no more than 4)
            - Provide solutions only for the objectives listed; do NOT invent extra objectives.
            - Focus on IBM tools, but include open-source options commonly used by IBM or compatible with the IBM ecosystem.
            - Do NOT include the R language; only consider Python, SQL, JavaScript, Java, Scala, Rust, C++, and C#.
            - Use clear bullet points and structured lists under each objective.
            - Provide the answer in formal US English.
            """
            solucao_gerada = gerar_resposta_watsonx(
                prompt_solucao,
                temperature=0.5,
                max_tokens=1024,
            )
            st.session_state.solucao_tecnica = solucao_gerada
            st.success("Technical solution successfully generated!")

    st.markdown("**Technical solution generated!:**")
    solucao = st.text_area(
        "Technical Solution!:",
        value=st.session_state.get("solucao_tecnica", ""),
        height=300,
    )
