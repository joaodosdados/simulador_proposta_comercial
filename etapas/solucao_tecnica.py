# Pasta: etapas/
# Arquivo: solucao_tecnica.py
import streamlit as st
from utils.navigation import render_sidebar, ETAPAS
from utils.llm import gerar_resposta_ollama


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
    st.subheader("🛠️ Etapa 3: Solução Técnica")

    objetivos_base = st.session_state.get("objetivos", "Objetivos ainda não definidos.")
    st.markdown("**Objetivos definidos:**")
    st.text_area("Objetivos:", value=objetivos_base, height=200, disabled=False)

    if st.button("⚙️ Gerar Solução Técnica com IA", key="btn_gerar_solucao"):
        with st.spinner("Gerando solução técnica com IA..."):
            prompt_solucao = f"""
            Você é um arquiteto de soluções. Com base nos objetivos abaixo, descreva uma proposta técnica de solução baseada em Data Science.
            Inclua tecnologias, abordagem, possíveis fontes de dados e etapas de desenvolvimento.
            Sugira também quais ferramentas, softwares ou frameworks da IBM poderiam ser utilizados.
            Se houver tecnologias que não são da IBM porém a IBM também usa ou são compatíveis com o ecossitema da IBM sigura também.
            Não sugira a linguage R, somente Python, SQL, JavaScript, Java, Scala, Rust, C++ e C#.

            Objetivos:
            {objetivos_base}

            Responda com clareza, de forma estruturada. Em portugues do Brasil, brasileiro
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
