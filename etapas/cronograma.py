# etapas/cronograma.py

import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from utils.navigation import render_sidebar
from utils.llm import gerar_resposta_ollama
import json
import re

PROFISSIONAIS_DISPONIVEIS = [
    {"cargo": "Cientista de Dados", "custo_hora": 150},
    {"cargo": "Engenheiro de Dados", "custo_hora": 140},
    {"cargo": "Analista de Negócios", "custo_hora": 130},
    {"cargo": "Arquiteto de Soluções", "custo_hora": 160},
    {"cargo": "Gerente de Projetos", "custo_hora": 145},
]


def gerar_cronograma_ia_openai(diagnostico, objetivos, semanas):
    try:
        prompt = f"""
        Você é um especialista em planejamento de projetos de Data Science. Crie um cronograma em JSON com a seguinte estrutura:
        [
            {{
                "Semana": 1,
                "Profissional": "Cientista de Dados",
                "Horas": 10,
                "Custo Hora": 150,
                "Custo Total": 1500
            }},
            ...
        ]
        Geração para um projeto com {semanas} semanas, considerando o seguinte diagnóstico: "{diagnostico}" e os seguintes objetivos: "{objetivos}".
        Não inclua comentários, nem texto fora do JSON.
        """
        resposta = gerar_resposta_ollama(prompt)

        # 🔧 Limpa a resposta: extrai só o JSON entre colchetes
        match = re.search(r"\[\s*{.*?}\s*\]", resposta, re.DOTALL)
        if not match:
            raise ValueError("⚠️ Resposta da IA não contém JSON válido.")

        json_str = match.group(0)

        data = json.loads(json_str)
        df = pd.DataFrame(data)

        # Corrige colunas ausentes
        if "Custo Total" not in df.columns and {"Horas", "Custo Hora"}.issubset(
            df.columns
        ):
            df["Custo Total"] = df["Horas"] * df["Custo Hora"]

        return df

    except Exception as e:
        st.error(f"Erro ao interpretar resposta da IA: {e}")
        st.text_area("Resposta bruta recebida da IA:", value=resposta, height=300)
        raise e


def gerar_dataframe_inicial(semanas, profissionais):
    data = []
    for semana in range(1, semanas + 1):
        for profissional in profissionais:
            custo_hora = next(
                p["custo_hora"]
                for p in PROFISSIONAIS_DISPONIVEIS
                if p["cargo"] == profissional
            )
            data.append(
                {
                    "Semana": semana,
                    "Profissional": profissional,
                    "Horas": 0,
                    "Custo Hora": custo_hora,
                    "Custo Total": 0,
                }
            )
    return pd.DataFrame(data)


def mostrar_cronograma(cronograma_df, key_suffix="padrao"):
    st.markdown("### 📋 Tabela de Alocação (Editável)")

    gb = GridOptionsBuilder.from_dataframe(cronograma_df)
    gb.configure_default_column(editable=True)
    gb.configure_column("Semana", type=["numericColumn"])
    gb.configure_column("Horas", type=["numericColumn"])
    gb.configure_column("Custo Hora", type=["numericColumn"])
    grid_options = gb.build()

    grid_return = AgGrid(
        cronograma_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=True,
        height=300,
        key=f"cronograma_grid_{key_suffix}",
    )

    df_editado = grid_return["data"]
    df_editado["Custo Total"] = df_editado["Horas"] * df_editado["Custo Hora"]

    total_geral = df_editado["Custo Total"].sum()

    modelo_comercial = st.selectbox(
        "Modelo Comercial:",
        ["Fixed-price", "Time & Materials"],
        key=f"modelo_comercial_{key_suffix}",
    )
    if modelo_comercial == "Fixed-price":
        adicional = st.number_input(
            "Margem adicional (%)",
            min_value=0,
            max_value=100,
            value=30,
            key=f"margem_{key_suffix}",
        )
        total_com_adicional = total_geral * (1 + adicional / 100)
    else:
        total_com_adicional = total_geral

    st.session_state.cronograma_df = df_editado
    st.session_state.total_geral = total_geral
    st.session_state.total_com_adicional = total_com_adicional
    st.session_state.proposta_tipo = modelo_comercial

    st.markdown(f"**Custo Total:** R$ {total_geral:,.2f}")
    st.markdown(f"**Preço Final Estimado:** R$ {total_com_adicional:,.2f}")

    st.markdown("---")
    st.markdown("#### 📊 Visualização do Cronograma")

    tipo_visualizacao = st.selectbox(
        "Tipo de visualização:",
        ["Gráfico de Gantt", "Heatmap de Horas"],
        key=f"tipo_visualizacao_{key_suffix}",
    )

    if not df_editado.empty:
        if tipo_visualizacao == "Gráfico de Gantt":
            df = df_editado[df_editado["Horas"] > 0].copy()
            df["Start"] = pd.to_datetime("2025-01-01") + pd.to_timedelta(
                (df["Semana"] - 1) * 7, unit="d"
            )
            df["Finish"] = df["Start"] + pd.to_timedelta(7, unit="d")

            fig = px.timeline(
                df,
                x_start="Start",
                x_end="Finish",
                y="Profissional",
                color="Profissional",
                text="Horas",
                title="🗕️ Cronograma do Projeto (Gantt)",
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True, key=f"gantt_{key_suffix}")

        elif tipo_visualizacao == "Heatmap de Horas":
            df = df_editado[df_editado["Horas"] > 0].copy()
            pivot = df.pivot_table(
                index="Profissional", columns="Semana", values="Horas", fill_value=0
            )
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlGnBu", ax=ax)
            ax.set_title("Distribuição de Horas por Semana e Profissional")
            st.pyplot(fig, clear_figure=True)
    else:
        st.info("Nenhum dado disponível para visualização.")


def render():
    render_sidebar()
    st.subheader("🗓️ Etapa 4: Cronograma do Projeto")

    semanas = st.slider(
        "Duração do Projeto (em semanas):", min_value=1, max_value=52, value=12
    )

    if "last_profissionais" not in st.session_state:
        st.session_state["last_profissionais"] = [
            p["cargo"] for p in PROFISSIONAIS_DISPONIVEIS
        ]
    if "last_semanas" not in st.session_state:
        st.session_state["last_semanas"] = 12

    profissionais_selecionados = st.multiselect(
        "Selecione os profissionais envolvidos:",
        options=[p["cargo"] for p in PROFISSIONAIS_DISPONIVEIS],
        default=st.session_state["last_profissionais"],
    )

    if profissionais_selecionados:
        last_semanas = st.session_state.get("last_semanas")
        last_profissionais = st.session_state.get("last_profissionais", [])

        precisa_recriar = (
            "cronograma_df" not in st.session_state
            or last_semanas != semanas
            or set(last_profissionais) != set(profissionais_selecionados)
        )

        if precisa_recriar:
            st.session_state.cronograma_df = gerar_dataframe_inicial(
                semanas, profissionais_selecionados
            )
            st.session_state["cronograma_gerado_por_ia"] = False

        st.session_state["last_semanas"] = semanas
        st.session_state["last_profissionais"] = profissionais_selecionados

    else:
        st.warning("Selecione ao menos um profissional para configurar o cronograma.")
        return

    if st.button("✨ Gerar sugestão de cronograma com IA"):
        objetivos = st.session_state.get("objetivos", "")
        diagnostico = st.session_state.get("resultado_diagnostico", "")
        sugestao_df = gerar_cronograma_ia_openai(diagnostico, objetivos, semanas)

        st.session_state.cronograma_df = sugestao_df
        st.session_state["last_semanas"] = semanas
        st.session_state["last_profissionais"] = (
            sugestao_df["Profissional"].unique().tolist()
        )
        st.session_state["cronograma_gerado_por_ia"] = True
        st.success("Cronograma gerado com IA usando modelo local.")

    key_suffix = "ia" if st.session_state.get("cronograma_gerado_por_ia") else "manual"
    mostrar_cronograma(st.session_state.cronograma_df, key_suffix=key_suffix)
