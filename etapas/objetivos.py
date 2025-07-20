import streamlit as st
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

    # Cards de informação
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-label">Opportunities identified</div>
                <div class="info-value">
                    <span style="background: #e0e7ff; color: #0f62fe; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.875rem;">
                        {st.session_state.get('qtd_oportunidades', 0)}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        status = (
            "Defined"
            if st.session_state.get("objetivos")
            and st.session_state.objetivos.strip() != "No goals defined yet."
            else "Pending"
        )

        color = "#198754" if status == "Defined" else "#ffc107"  # green or yellow
        bg_color = (
            "#d1e7dd" if status == "Defined" else "#fff3cd"
        )  # light green or light yellow

        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-label">Status of objectives</div>
                <div class="info-value">
                    <span style="background: {bg_color}; color: {color}; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.875rem;">
                        {status}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Seção de comparação lado a lado

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            '<div class="comparison-title">📋 Original Diagnosis</div>',
            unsafe_allow_html=True,
        )
        st.text_area(
            label="Original Diagnosis",
            value=st.session_state.get(
                "resultado_diagnostico", "No diagnosis available."
            ),
            height=450,
            disabled=False,
            label_visibility="collapsed",
        )

    with col2:
        st.markdown(
            '<div class="comparison-title">🎯 Proposed Objectives</div>',
            unsafe_allow_html=True,
        )
        objetivos = st.text_area(
            "Objetivos:",
            value=st.session_state.get("objetivos", "No goals defined yet."),
            height=450,
            label_visibility="collapsed",
        )
        if objetivos != st.session_state.get("objectives", ""):
            st.session_state.objetivos = objetivos

    # Seção de geração de objetivos
    st.markdown(
        '<div class="section-title">Generate goals automatically</div>',
        unsafe_allow_html=True,
    )

    if st.button("⚙️ Generate objectives with IA", type="primary"):
        with st.spinner("Analyzing oportunities..."):
            texto_base = st.session_state.get("resultado_diagnostico", "")
            prompt = f"""
            You are a specialist in defining SMART objectives for business diagnostics.

            Analyze the diagnostic text below and generate ONLY specific, clear SMART objectives that are explicitly mentioned or clearly derivable from the text.

            {texto_base}

            Rules:
            - Provide only objectives that are explicitly supported by the diagnostic content; do not invent or infer details
            - If no quantitative goal (percentages, timeframes) is provided in the diagnostic, describe the objective qualitatively, without adding fictitious numbers
            - One objective per line, following the format: "- Objective: S.M.A.R.T. Justification"
            - Output strictly in English (USA), formal executive tone
            - Do NOT include any HTML, Markdown, explanations, summaries, or extra text before or after the list
            """
            objetivos = gerar_resposta_watsonx(
                prompt,
                temperature=0.5,
                max_tokens=1024,
            )
            st.session_state.objetivos = objetivos
            st.success("Goals successfully generated!")
            st.rerun()

    # Footer
    st.markdown("---")
    if (
        st.session_state.get("objetivos")
        and st.session_state.objetivos.strip() != "No goals defined yet."
    ):
        st.success("✅ Objectives defined - You can proceed to the next step")
    else:
        st.warning("⚠️ Please define the objectives before continuing")
