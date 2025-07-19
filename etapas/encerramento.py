# etapas/encerramento.py
import streamlit as st
import json
import os
from utils.navigation import render_sidebar
from datetime import datetime
from fpdf import FPDF, HTMLMixin
import markdown2
import pandas as pd

SALVAMENTO_DIR = "simulacoes_salvas"
os.makedirs(SALVAMENTO_DIR, exist_ok=True)


class PDF(FPDF, HTMLMixin):
    pass


def gerar_pdf():
    from textwrap import wrap
    import re

    def limpar_texto(texto):
        return re.sub(
            r"[^\x20-\x7E\u00A0-\u00FF]", "", texto
        )  # remove caracteres não imprimíveis

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    def add_titulo(titulo):
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, titulo, ln=True)
        pdf.set_font("Arial", size=12)

    def add_texto_markdown(texto_md):
        html = markdown2.markdown(texto_md)
        html = html.replace("<ul>", "").replace("</ul>", "")  # fpdf2 não lida com <ul>
        pdf.write_html(html)

    add_titulo("Technical Proposal for Data Science Project")

    add_titulo("1. Diagnosis")
    add_texto_markdown(st.session_state.get("resultado_diagnostico", ""))

    add_titulo("2. Objectives")
    add_texto_markdown(st.session_state.get("objetivos", ""))

    add_titulo("3. Technical Solution")
    add_texto_markdown(st.session_state.get("solucao_tecnica", ""))

    add_titulo("4. Timeline and Cost")
    cronograma_df = st.session_state.get("cronograma_df")
    if cronograma_df is not None and not cronograma_df.empty:
        pdf.set_font("Arial", size=10)
        for index, row in cronograma_df.iterrows():
            linha = f"Mês {row['Mês']} - {row['Profissional']}: {row['Horas']}h @ R$ {row['Custo Hora']}/h"

            pdf.cell(0, 8, linha, ln=True)
        pdf.ln(2)
        total = st.session_state.get("total_geral", 0)
        preco_final = st.session_state.get("total_com_adicional", total)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Custo Total: R$ {total:,.2f}", ln=True)
        pdf.cell(0, 10, f"Preço Final Estimado: R$ {preco_final:,.2f}", ln=True)
        pdf.ln(5)

    add_titulo("5. Modelo Comercial")
    modelo = st.session_state.get("proposta_tipo", "Fixed-price")
    pdf.cell(0, 8, f"Tipo de proposta: {modelo}", ln=True)
    pdf.ln(5)

    add_titulo("6. Premissas e Limitações")
    add_texto_markdown(st.session_state.get("premissas_limitacoes", ""))

    nome_arquivo = f"proposta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    caminho = os.path.join(SALVAMENTO_DIR, nome_arquivo)
    pdf.output(caminho)
    return caminho


def render():
    st.subheader("✅ Stage 7: Proposal Closure and Export")

    preco_final = st.session_state.get("total_com_adicional", 0.0)
    st.markdown("### 💰 Estimated Final Price")
    st.markdown(f"## `R$ {preco_final:,.2f}`")

    st.markdown("---")
    st.markdown("### 1. Diagnosis")
    st.text_area(
        "Describe the diagnosis made:",
        value=st.session_state.get("resultado_diagnostico", ""),
        height=150,
        key="resultado_diagnostico",
    )

    st.markdown("### 2. Objectives")
    st.text_area(
        "Define the project objectives:",
        value=st.session_state.get("objetivos", ""),
        height=150,
        key="objetivos",
    )

    st.markdown("### 3. Technical Solution")
    st.text_area(
        "Describe the proposed technical solution:",
        value=st.session_state.get("solucao_tecnica", ""),
        height=150,
        key="solucao_tecnica",
    )

    st.markdown("### 4. Timeline and Cost")
    if "cronograma_df" in st.session_state:
        st.dataframe(st.session_state.cronograma_df, use_container_width=True)
        st.markdown(f"**Total Cost:** R$ {st.session_state.get('total_geral', 0):,.2f}")
        st.markdown(
            f"**Estimated Final Price with additional:** R$ {st.session_state.get('total_com_adicional', 0):,.2f}"
        )
    else:
        st.info("No timeline has been set.")

    st.markdown("### 5. Commercial Model")
    proposta_tipo = st.selectbox(
        "Select the type of commercial proposal:",
        options=["Fixed-price", "Time & Materials"],
        index=["Fixed-price", "Time & Materials"].index(
            st.session_state.get("proposta_tipo", "Fixed-price")
        ),
    )
    st.session_state.proposta_tipo = proposta_tipo

    st.markdown("### 6. Premises and Limitations")
    st.text_area(
        "List relevant assumptions and limitations:",
        value=st.session_state.get("premissas_limitacoes", ""),
        height=150,
        key="premissas_limitacoes",
    )

    st.markdown("---")
    st.markdown("### 💾 Save or Load Simulation")

    if st.button("💾 Save Simulation in JSON"):
        file_name = f"simulacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_data = json.dumps(dict(st.session_state), indent=2, default=str)
        file_path = os.path.join(SALVAMENTO_DIR, file_name)
        with open(file_path, "w") as f:
            f.write(json_data)
        st.success(f"Simulation saved successfully in `{file_path}`")
        with open(file_path, "rb") as f:
            st.download_button(
                "📥 Baixar JSON", data=f, file_name=file_name, mime="application/json"
            )

    uploaded_file = st.file_uploader(
        "📂 Load previous simulation (.json)", type=["json"]
    )
    if uploaded_file:
        data = json.load(uploaded_file)
        for key, value in data.items():
            st.session_state[key] = value
        st.success("Simulation loaded successfully! Reload the page to see updates.")

    st.markdown("---")
    st.markdown("### 📄 Export to PDF")
    if st.button("📄 Generate Proposal PDF"):
        with st.spinner("Generating PDF..."):
            caminho_pdf = gerar_pdf()
            with open(caminho_pdf, "rb") as f:
                st.download_button(
                    label="📥 Download PDF",
                    data=f,
                    file_name=os.path.basename(caminho_pdf),
                    mime="application/pdf",
                )
