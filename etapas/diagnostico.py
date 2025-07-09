import streamlit as st
from utils.benchmark_loader import carregar_benchmark
from PyPDF2 import PdfReader
import docx
from utils.navigation import render_sidebar, ETAPAS
from utils.llm import gerar_resposta_ollama


def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif (
        uploaded_file.type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        doc = docx.Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        return None


def render():
    # Configuração de estilo minimalista
    st.markdown(
        """
    <style>
        .header {
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #161616;
            margin-top: 0;
            margin-bottom: 1rem;
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
        .result-card {
            border-left: 3px solid #0f62fe;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Cabeçalho
    st.markdown(
        """
    <div class="header">
        <h1 style="font-size: 1.5rem; margin: 0 0 0.25rem;">🔍 Diagnóstico</h1>
        <p style="color: #525252; margin: 0;">Identifique oportunidades para projetos de Data Science</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Card de entrada de dados
    st.markdown(
        '<div class="card-title">📌 Fonte de dados</div>', unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["✍️ Texto manual", "📁 Upload de arquivo"])

    with tab1:
        manual_text = st.text_area(
            "Digite ou cole seu conteúdo para análise:",
            value=carregar_benchmark("cemig"),
            height=250,
            label_visibility="collapsed",
        )
        texto_extraido = manual_text

    with tab2:
        uploaded_file = st.file_uploader(
            "Selecione um arquivo (TXT, PDF ou DOCX):",
            type=["txt", "pdf", "docx"],
            label_visibility="collapsed",
        )
        if uploaded_file:
            with st.expander("🔍 Visualizar conteúdo", expanded=False):
                texto_extraido = extract_text_from_file(uploaded_file)
                if texto_extraido:
                    st.text_area(
                        "Conteúdo extraído:",
                        value=texto_extraido,
                        height=200,
                        label_visibility="collapsed",
                    )
                else:
                    st.warning("Não foi possível extrair texto deste arquivo")

    # Botão de análise
    if st.button("🔎 Analisar com IA", type="primary"):
        if texto_extraido and len(texto_extraido.strip()) > 0:
            with st.spinner("Analisando conteúdo..."):
                prompt = (
                    "Você é um especialista em identificar oportunidades de Data Science.\n"
                    "Analise este conteúdo e identifique:\n"
                    "1. Oportunidades claras para projetos\n"
                    "2. Áreas de aplicação\n"
                    "3. Impacto potencial\n"
                    "4. Formate como lista markdown com:\n"
                    "   - Bullet points iniciando com '-'\n"
                    "   - Breve justificativa entre parênteses\n"
                    "   - A saída deve ser em português Brasileiro\n\n"
                    f"Conteúdo:\n{texto_extraido.strip()}"
                )
                resultado = gerar_resposta_ollama(prompt)
                oportunidades = [
                    l for l in resultado.splitlines() if l.strip().startswith("-")
                ]
                st.session_state.resultado_diagnostico = resultado
                st.session_state.qtd_oportunidades = len(oportunidades)
                st.success(
                    f"Análise concluída! {len(oportunidades)} oportunidades encontradas"
                )
        else:
            st.error("Por favor, insira algum texto ou faça upload de um arquivo")

    # Resultados
    if st.session_state.get("resultado_diagnostico"):
        st.markdown("---")
        st.markdown(
            """
        <div class="card result-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 class="card-title">📋 Resultados</h2>
                <span style="background: #e0e7ff; color: #0f62fe; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.875rem;">
                    {0} oportunidades
                </span>
            </div>
        """.format(st.session_state.qtd_oportunidades),
            unsafe_allow_html=True,
        )

        edited_result = st.text_area(
            "Oportunidades identificadas:",
            value=st.session_state.resultado_diagnostico,
            height=300,
            label_visibility="collapsed",
        )

        if edited_result != st.session_state.resultado_diagnostico:
            st.session_state.resultado_diagnostico = edited_result
            st.info("Alterações salvas automaticamente")

        st.markdown("</div>", unsafe_allow_html=True)
