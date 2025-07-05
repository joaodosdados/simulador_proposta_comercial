# Pasta: etapas/
# Arquivo: diagnostico.py
import streamlit as st
from utils.ai_agent import agente_identifica_oportunidades
from utils.benchmark_loader import carregar_benchmark
from PyPDF2 import PdfReader
import docx
from utils.navigation import render_sidebar, ETAPAS


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
        return "❌ Tipo de arquivo não suportado."


def render():
    render_sidebar()
    st.subheader("🔍 Etapa 1: Diagnóstico")
    benchmark_text = carregar_benchmark("cemig")

    col1, col2 = st.columns([1, 2])
    with col1:
        uploaded_file = st.file_uploader(
            "📁 Upload de arquivo", type=["txt", "pdf", "docx"]
        )
    with col2:
        manual_text = st.text_area(
            "✍️ Ou digite o texto aqui", value=benchmark_text, height=250
        )

    texto_extraido = ""
    if uploaded_file:
        texto_extraido = extract_text_from_file(uploaded_file)
    elif manual_text:
        texto_extraido = manual_text

    if st.button("🔎 Analisar com IA", key="btn_analisa_ia"):
        with st.spinner("Analisando..."):
            resultado = agente_identifica_oportunidades(texto_extraido)
            oportunidades = [
                l for l in resultado.splitlines() if l.strip().startswith("-")
            ]
            st.session_state.resultado_diagnostico = resultado
            st.session_state.qtd_oportunidades = len(oportunidades)
            st.success(
                f"Diagnóstico gerado com sucesso! Foram encontradas {len(oportunidades)} oportunidades."
            )

    resultado = st.session_state.get("resultado_diagnostico", "")
    if resultado:
        st.text_area("Resultado do Diagnóstico:", value=resultado, height=200)
