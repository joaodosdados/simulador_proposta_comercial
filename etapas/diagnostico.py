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
        <h1 style="font-size: 1.5rem; margin: 0 0 0.25rem;">🔍 Diagnostics</h1>
        <p style="color: #525252; margin: 0;">Identify opportunities for Data Science projects</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
