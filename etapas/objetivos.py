import streamlit as st
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
            <div class="info-label">Oportunidades identificadas</div>
            <div class="info-value">{st.session_state.get('qtd_oportunidades', 0)}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        status = "Definidos" if st.session_state.get("objetivos") else "Pendentes"
        st.markdown(
            f"""
        <div class="info-card">
            <div class="info-label">Status dos objetivos</div>
            <div class="info-value">{status}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Seção de comparação lado a lado
    st.markdown(
        '<div class="section-title">Comparação: Diagnóstico vs Objetivos</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            '<div class="comparison-title">📋 Diagnóstico Original</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
        <div class="comparison-panel">
            {st.session_state.get("resultado_diagnostico", "Nenhum diagnóstico disponível.")}
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            '<div class="comparison-title">🎯 Objetivos Propostos</div>',
            unsafe_allow_html=True,
        )
        objetivos = st.text_area(
            "Objetivos:",
            value=st.session_state.get("objetivos", "Nenhum objetivo definido ainda."),
            height=300,
            label_visibility="collapsed",
        )
        if objetivos != st.session_state.get("objetivos", ""):
            st.session_state.objetivos = objetivos

    # Seção de geração de objetivos
    st.markdown(
        '<div class="section-title">Gerar objetivos automaticamente</div>',
        unsafe_allow_html=True,
    )

    if st.button("⚙️ Gerar objetivos com IA", type="primary"):
        with st.spinner("Analisando oportunidades..."):
            texto_base = st.session_state.get("resultado_diagnostico", "")
            prompt = f"""
            Analise este diagnóstico e gere objetivos SMART específicos:
            
            {texto_base}
            
            Regras:
            1. Liste 3-5 objetivos claros
            2. Relacione cada objetivo com itens do diagnóstico
            4. Formato: "- [Objetivo] - [Justificativa baseada no diagnóstico]"
            """
            objetivos = gerar_resposta_ollama(prompt)
            st.session_state.objetivos = objetivos
            st.success("Objetivos gerados com sucesso!")
            st.rerun()

    # Rodapé
    st.markdown("---")
    if st.session_state.get("objetivos"):
        st.success("✅ Objetivos definidos - Você pode prosseguir para a próxima etapa")
    else:
        st.warning("⚠️ Defina os objetivos antes de continuar")
