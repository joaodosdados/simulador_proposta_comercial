# etapas/cronograma.py

import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from utils.navigation import render_sidebar

PROFISSIONAIS_DISPONIVEIS = [
    {"cargo": "Cientista de Dados", "custo_hora": 150},
    {"cargo": "Engenheiro de Dados", "custo_hora": 140},
    {"cargo": "Analista de Negócios", "custo_hora": 130},
    {"cargo": "Arquiteto de Soluções", "custo_hora": 160},
    {"cargo": "Gerente de Projetos", "custo_hora": 145},
]


def gerar_cronograma_ia(diagnostico, objetivos, semanas):
    perfis = {
        "modelo preditivo": [
            "Cientista de Dados",
            "Engenheiro de Dados",
            "Analista de Negócios",
        ],
        "dashboard": [
            "Analista de Negócios",
            "Cientista de Dados",
            "Arquiteto de Soluções",
        ],
        "etl": ["Engenheiro de Dados", "Arquiteto de Soluções", "Gerente de Projetos"],
        "projeto generico": [
            "Cientista de Dados",
            "Engenheiro de Dados",
            "Analista de Negócios",
            "Gerente de Projetos",
        ],
    }

    texto = (diagnostico + " " + objetivos).lower()
    if "modelo" in texto or "classificação" in texto or "regressão" in texto:
        tipo = "modelo preditivo"
    elif "dashboard" in texto or "visualização" in texto:
        tipo = "dashboard"
    elif "etl" in texto or "pipeline" in texto or "dados brutos" in texto:
        tipo = "etl"
    else:
        tipo = "projeto generico"

    profissionais = perfis[tipo]
    data = []
    horas_base = 12

    for semana in range(1, semanas + 1):
        for prof in profissionais:
            if prof == "Gerente de Projetos":
                horas = 4 if semana in [1, semanas] else 2
            elif semana in [1, semanas]:
                horas = horas_base // 2
            else:
                horas = horas_base

            custo_hora = next(
                p["custo_hora"]
                for p in [
                    {"cargo": "Cientista de Dados", "custo_hora": 150},
                    {"cargo": "Engenheiro de Dados", "custo_hora": 140},
                    {"cargo": "Analista de Negócios", "custo_hora": 130},
                    {"cargo": "Arquiteto de Soluções", "custo_hora": 160},
                    {"cargo": "Gerente de Projetos", "custo_hora": 145},
                ]
                if p["cargo"] == prof
            )

            data.append(
                {
                    "Semana": semana,
                    "Profissional": prof,
                    "Horas": horas,
                    "Custo Hora": custo_hora,
                    "Custo Total": horas * custo_hora,
                }
            )

    df = pd.DataFrame(data)
    return tipo, df


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
        "Modelo Comercial:", ["Fixed-price", "Time & Materials"]
    )
    if modelo_comercial == "Fixed-price":
        adicional = st.number_input(
            "Margem adicional (%)", min_value=0, max_value=100, value=30
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
        "Tipo de visualização:", ["Gráfico de Gantt", "Heatmap de Horas"]
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
                title="📅 Cronograma do Projeto (Gantt)",
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        elif tipo_visualizacao == "Heatmap de Horas":
            df = df_editado[df_editado["Horas"] > 0].copy()
            pivot = df.pivot_table(
                index="Profissional", columns="Semana", values="Horas", fill_value=0
            )
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlGnBu", ax=ax)
            ax.set_title("Distribuição de Horas por Semana e Profissional")
            st.pyplot(fig)
    else:
        st.info("Nenhum dado disponível para visualização.")


def render():
    render_sidebar()

    st.subheader("🗓️ Etapa 4: Cronograma do Projeto")

    semanas = st.slider(
        "Duração do Projeto (em semanas):", min_value=1, max_value=52, value=12
    )

    profissionais_selecionados = st.multiselect(
        "Selecione os profissionais envolvidos:",
        options=[p["cargo"] for p in PROFISSIONAIS_DISPONIVEIS],
        default=st.session_state.get("last_profissionais", []),
    )

    if profissionais_selecionados:
        # Verifica valores anteriores salvos
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

        # Atualiza os parâmetros apenas depois da verificação
        st.session_state["last_semanas"] = semanas
        st.session_state["last_profissionais"] = profissionais_selecionados

        mostrar_cronograma(sugestao_df, key_suffix="ia")
    else:
        st.warning("Selecione ao menos um profissional para configurar o cronograma.")

    if profissionais_selecionados:
        st.markdown("---")
    if st.button("✨ Gerar sugestão de cronograma com IA"):
        objetivos = st.session_state.get("objetivos", "")
        diagnostico = st.session_state.get("resultado_diagnostico", "")
        tipo, sugestao_df = gerar_cronograma_ia(diagnostico, objetivos, semanas)
        st.session_state.cronograma_df = sugestao_df
        st.session_state["last_semanas"] = semanas
        st.session_state["last_profissionais"] = (
            sugestao_df["Profissional"].unique().tolist()
        )
        st.success(
            f"Cronograma sugerido com base em um projeto do tipo: **{tipo.upper()}**"
        )
        mostrar_cronograma(sugestao_df, key_suffix="ia")
