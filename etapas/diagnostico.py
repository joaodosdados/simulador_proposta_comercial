import streamlit as st
from utils.benchmark_loader import carregar_benchmark
from PyPDF2 import PdfReader
import docx
from utils.navigation import render_sidebar, ETAPAS
from utils.llm import gerar_resposta_ollama, gerar_resposta_watsonx


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
        <h1 style="font-size: 1.5rem; margin: 0 0 0.25rem;">🔍 Diagnosis</h1>
        <p style="color: #525252; margin: 0;">Identify opportunities for Data Science projects</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Card de entrada de dados
    st.markdown(
        '<div class="card-title">📌 Fonte de dados</div>', unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["✍️ Handwritten text", "📁 File Upload"])

    with tab1:
        manual_text = st.text_area(
            "Type or paste your content for analysis:",
            value=st.session_state.get(
                "texto_extraido", carregar_benchmark("cemig_en")
            ),
            height=250,
            label_visibility="collapsed",
        )

        if manual_text != st.session_state.get("texto_extraido", ""):
            st.session_state.texto_extraido = manual_text

        texto_extraido = st.session_state.texto_extraido

    with tab2:
        uploaded_file = st.file_uploader(
            "Select a file (TXT, PDF or DOCX):",
            type=["txt", "pdf", "docx"],
            label_visibility="collapsed",
        )
        if uploaded_file:
            with st.expander("🔍 View content", expanded=False):
                texto_extraido = extract_text_from_file(uploaded_file)
                if texto_extraido:
                    st.text_area(
                        "Conteúdo extraído:",
                        value=texto_extraido,
                        height=200,
                        label_visibility="collapsed",
                    )
                else:
                    st.warning("Unable to extract text from this file")

    # Botão de análise
    if st.button("🔎 Analyze with IA", type="primary"):
        if texto_extraido and len(texto_extraido.strip()) > 0:
            with st.spinner("Analisando conteúdo..."):
                prompt = (
                    "You are a specialist in identifying Data Science opportunities for commercial proposals.\n"
                    "Analyze the content below and provide ONLY a clear, concise list:\n"
                    "- One project opportunity per bullet (one line)\n"
                    "- Include area of application and expected impact in parentheses on the same line\n"
                    "- All opportunities must start with '-'\n"
                    "- Use consistent area names\n"
                    "- Keep each bullet under 250 characters\n"
                    "- Describe impact qualitatively, without numbers or unverifiable estimates\n"
                    "- Only identify and list opportunities explicitly present or clearly mentioned in the provided content; do not infer or assume\n"
                    "- DO NOT include introductions, explanations, summaries, or any text before or after the list\n"
                    "- Output in English USA, formal executive language\n\n"
                    f"Content:\n{texto_extraido.strip()}"
                )
                resultado = gerar_resposta_watsonx(
                    prompt,
                    temperature=0.5,
                    max_tokens=1024,
                )
                oportunidades = [
                    l for l in resultado.splitlines() if l.strip().startswith("-")
                ]
                st.session_state.resultado_diagnostico = resultado
                st.session_state.qtd_oportunidades = len(oportunidades)
                st.success(
                    f"Analysis complete! {len(oportunidades)} opportunities found"
                )
        else:
            st.error("Please enter some text or upload a file")

    # Resultados
    if st.session_state.get("resultado_diagnostico"):
        st.markdown("---")
        st.markdown(
            """
        <div class="card result-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 class="card-title">📋 Resultados</h2>
                <span style="background: #e0e7ff; color: #0f62fe; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.875rem;">
                    {0} opportunities
                </span>
            </div>
        """.format(st.session_state.qtd_oportunidades),
            unsafe_allow_html=True,
        )

        edited_result = st.text_area(
            "Opportunities identified:",
            value=st.session_state.resultado_diagnostico,
            height=300,
            label_visibility="collapsed",
        )

        if edited_result != st.session_state.resultado_diagnostico:
            st.session_state.resultado_diagnostico = edited_result
            st.info("Changes saved automatically")

        st.markdown("</div>", unsafe_allow_html=True)
