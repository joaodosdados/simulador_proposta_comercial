# etapas/encerramento.py
import streamlit as st
import json
import os
from utils.navigation import render_sidebar
from datetime import datetime
from fpdf import FPDF
import pandas as pd

SALVAMENTO_DIR = "simulacoes_salvas"
os.makedirs(SALVAMENTO_DIR, exist_ok=True)


def gerar_pdf():
    from textwrap import wrap
    import re

    def limpar_texto(texto):
        return re.sub(
            r"[^\x20-\x7E\u00A0-\u00FF]", "", texto
        )  # remove caracteres não imprimíveis

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    def add_titulo(titulo):
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, titulo, ln=True)
        pdf.set_font("Arial", size=12)

    def add_texto(texto):
        def quebrar_palavras_longa(linha, max_len=60):
            import re

            palavras = re.split(r"(\s+)", linha)  # mantém os espaços
            quebradas = []
            for palavra in palavras:
                if len(palavra) > max_len and palavra.strip() != "":
                    for i in range(0, len(palavra), max_len):
                        quebradas.append(palavra[i : i + max_len])
                else:
                    quebradas.append(palavra)
            return "".join(quebradas)

        texto = limpar_texto(texto)
        for linha in texto.split("\n"):
            linha = quebrar_palavras_longa(linha)
            try:
                pdf.multi_cell(0, 8, linha)
            except Exception as e:
                print(f"Erro ao processar linha: {repr(linha)}")
                raise e
        pdf.ln(5)

    add_titulo("Proposta Técnica de Projeto de Data Science")

    add_titulo("1. Diagnóstico")
    add_texto(st.session_state.get("resultado_diagnostico", ""))

    add_titulo("2. Objetivos")
    add_texto(st.session_state.get("objetivos", ""))

    add_titulo("3. Solução Técnica")
    add_texto(st.session_state.get("solucao_tecnica", ""))

    add_titulo("4. Cronograma e Custo")
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
    add_texto(st.session_state.get("premissas_limitacoes", ""))

    nome_arquivo = f"proposta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    caminho = os.path.join(SALVAMENTO_DIR, nome_arquivo)
    pdf.output(caminho)
    return caminho


def render():
    st.subheader("✅ Etapa 7: Encerramento e Exportação da Proposta")

    preco_final = st.session_state.get("total_com_adicional", 0.0)
    st.markdown("### 💰 Preço Final Estimado")
    st.markdown(f"## `R$ {preco_final:,.2f}`")

    st.markdown("---")
    st.markdown("### 1. Diagnóstico")
    st.text_area(
        "Descreva o diagnóstico realizado:",
        value=st.session_state.get("resultado_diagnostico", ""),
        height=150,
        key="resultado_diagnostico",
    )

    st.markdown("### 2. Objetivos")
    st.text_area(
        "Defina os objetivos do projeto:",
        value=st.session_state.get("objetivos", ""),
        height=150,
        key="objetivos",
    )

    st.markdown("### 3. Solução Técnica")
    st.text_area(
        "Descreva a solução técnica proposta:",
        value=st.session_state.get("solucao_tecnica", ""),
        height=150,
        key="solucao_tecnica",
    )

    st.markdown("### 4. Cronograma e Custo")
    if "cronograma_df" in st.session_state:
        st.dataframe(st.session_state.cronograma_df, use_container_width=True)
        st.markdown(
            f"**Custo Total:** R$ {st.session_state.get('total_geral', 0):,.2f}"
        )
        st.markdown(
            f"**Preço Final Estimado com adicional:** R$ {st.session_state.get('total_com_adicional', 0):,.2f}"
        )
    else:
        st.info("Nenhum cronograma foi definido.")

    st.markdown("### 5. Modelo Comercial")
    proposta_tipo = st.selectbox(
        "Selecione o tipo de proposta comercial:",
        options=["Fixed-price", "Time & Materials"],
        index=["Fixed-price", "Time & Materials"].index(
            st.session_state.get("proposta_tipo", "Fixed-price")
        ),
    )
    st.session_state.proposta_tipo = proposta_tipo

    st.markdown("### 6. Premissas e Limitações")
    st.text_area(
        "Liste premissas e limitações relevantes:",
        value=st.session_state.get("premissas_limitacoes", ""),
        height=150,
        key="premissas_limitacoes",
    )

    st.markdown("---")
    st.markdown("### 💾 Salvar ou Carregar Simulação")

    if st.button("💾 Salvar Simulação em JSON"):
        file_name = f"simulacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_data = json.dumps(dict(st.session_state), indent=2, default=str)
        file_path = os.path.join(SALVAMENTO_DIR, file_name)
        with open(file_path, "w") as f:
            f.write(json_data)
        st.success(f"Simulação salva com sucesso em `{file_path}`")
        with open(file_path, "rb") as f:
            st.download_button(
                "📥 Baixar JSON", data=f, file_name=file_name, mime="application/json"
            )

    uploaded_file = st.file_uploader(
        "📂 Carregar simulação anterior (.json)", type=["json"]
    )
    if uploaded_file:
        data = json.load(uploaded_file)
        for key, value in data.items():
            st.session_state[key] = value
        st.success(
            "Simulação carregada com sucesso! Recarregue a página para ver as atualizações."
        )

    st.markdown("---")
    st.markdown("### 📄 Exportar Proposta em PDF")
    if st.button("📄 Gerar PDF da Proposta"):
        with st.spinner("Gerando PDF..."):
            caminho_pdf = gerar_pdf()
            with open(caminho_pdf, "rb") as f:
                st.download_button(
                    label="📥 Baixar PDF",
                    data=f,
                    file_name=os.path.basename(caminho_pdf),
                    mime="application/pdf",
                )
