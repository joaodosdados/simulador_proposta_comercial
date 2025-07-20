import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from utils.navigation import render_sidebar
from utils.llm import gerar_resposta_ollama, gerar_resposta_watsonx
import json
import re

PROFISSIONAIS_DISPONIVEIS = [
    {"cargo": "Project Manager", "custo_hora": 369.68},
    {"cargo": "Scrum Master", "custo_hora": 254.48},
    {"cargo": "Architect", "custo_hora": 394.38},
    {"cargo": "Business Analyst", "custo_hora": 192.26},
    {"cargo": "Developer", "custo_hora": 192.26},
    {"cargo": "Data Scientist", "custo_hora": 227.37},
    {"cargo": "Data Engineer", "custo_hora": 227.37},
]


def gerar_cronograma_ia_openai(diagnostico, objetivos, meses, profissionais_ia):
    try:
        prompt = f"""
        You are a specialist in Data Science project planning.

        Diagnostic: {diagnostico}
        Objectives: {objetivos}
        Duration: {meses} months
        Involved professionals: {', '.join(profissionais_ia)}

        Your task is to suggest the number of hours each professional should work in each month.

        Expected format (only the integer matrix, no explanations):

        [
        [Hours for professional 1 in month 1, month 2, ..., month {meses}],
        [Hours for professional 2 in month 1, month 2, ..., month {meses}],
        ...
        ]

        ⚠️ The order of professionals must be: {', '.join(profissionais_ia)}
        ⚠️ Only the matrix. No comments, text, or additional explanations.
        """

        resposta = gerar_resposta_watsonx(
            prompt,
            temperature=0.5,
            max_tokens=1024,
        )

        # Extrai a matriz de horas da resposta
        matriz_match = re.search(r"\[\s*\[.*?\]\s*\]", resposta, re.DOTALL)
        if not matriz_match:
            raise ValueError("No valid array found in AI response")

        matriz_str = matriz_match.group(0)
        matriz = json.loads(matriz_str)

        if len(matriz) != len(profissionais_ia):
            raise ValueError(
                f"AI returned {len(matriz)} rows, but {len(profissionais_ia)} professionals were selected."
            )

        # Monta o DataFrame de cronograma
        data = []
        for i, profissional in enumerate(profissionais_ia):
            horas_por_mes = matriz[i]
            if len(horas_por_mes) != meses:
                raise ValueError(
                    f"The professional '{profissional}' does not have {meses} months of data."
                )
            custo_hora = next(
                (
                    p["custo_hora"]
                    for p in PROFISSIONAIS_DISPONIVEIS
                    if p["cargo"] == profissional
                ),
                None,
            )
            if custo_hora is None:
                raise ValueError(
                    f"Hourly cost not found for professional: {profissional}"
                )
            for mes in range(1, meses + 1):
                horas = horas_por_mes[mes - 1]
                data.append(
                    {
                        "Mês": mes,
                        "Profissional": profissional,
                        "Horas": horas,
                        "Custo Hora": custo_hora,
                        "Custo Total": horas * custo_hora,
                    }
                )

        df = pd.DataFrame(data)
        return df

    except Exception as e:
        st.error(f"Error interpreting AI response: {e}")
        st.text_area("Raw response received from AI:", value=resposta, height=300)
        return pd.DataFrame(
            columns=["Mês", "Profissional", "Horas", "Custo Hora", "Custo Total"]
        )


def gerar_dataframe_inicial(meses, profissionais):
    data = []
    for mes in range(1, meses + 1):
        for profissional in profissionais:
            custo_hora = next(
                p["custo_hora"]
                for p in PROFISSIONAIS_DISPONIVEIS
                if p["cargo"] == profissional
            )
            data.append(
                {
                    "Mês": mes,
                    "Profissional": profissional,
                    "Horas": 0,
                    "Custo Hora": custo_hora,
                    "Custo Total": 0,
                }
            )
    return pd.DataFrame(data)


def render():
    st.subheader("🗓️ Stage 4: Project Timeline")

    # Inicialização robusta do session_state
    required_keys = {
        "cronograma_df": pd.DataFrame(),
        "last_meses": 6,
        "last_profissionais": [p["cargo"] for p in PROFISSIONAIS_DISPONIVEIS],
        "modelo_comercial": "Time & Materials",
        "margem_fixed_price": 20,
        "total_geral": 0,
        "total_com_adicional": 0,
        "force_grid_update": False,  # Adicionamos uma flag para forçar atualização
    }

    for key, default_value in required_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    # Seção de configuração do projeto
    with st.expander("⚙️ Project Configure", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            modelo_comercial = st.selectbox(
                "Commercial Model:",
                options=["Time & Materials", "Fixed-price"],
                index=0
                if st.session_state.modelo_comercial == "Time & Materials"
                else 1,
                key="select_modelo_comercial",
            )

        with col2:
            meses = st.slider(
                "Duration (months):",
                min_value=1,
                max_value=24,
                value=st.session_state.last_meses,
                key="slider_meses",
            )

        profissionais_selecionados = st.multiselect(
            "Professionals:",
            options=[p["cargo"] for p in PROFISSIONAIS_DISPONIVEIS],
            default=st.session_state.last_profissionais,
            key="multiselect_profissionais",
        )

    # Verifica se houve mudança nos parâmetros
    parametros_alterados = (
        meses != st.session_state.last_meses
        or set(profissionais_selecionados) != set(st.session_state.last_profissionais)
        or modelo_comercial != st.session_state.modelo_comercial
    )

    # Botão para forçar atualização quando parâmetros mudam
    if parametros_alterados:
        st.warning("⚠️ Parameters changed. Click 'Update Schedule' to apply.")
        if st.button("🔄 Update Schedule", key="force_update"):
            st.session_state.cronograma_df = gerar_dataframe_inicial(
                meses, profissionais_selecionados
            )
            st.session_state.last_meses = meses
            st.session_state.last_profissionais = profissionais_selecionados
            st.session_state.modelo_comercial = modelo_comercial
            st.session_state.force_grid_update = True  # Ativa a flag
            st.rerun()
    else:
        if st.button("🔄 Update Schedule", key="normal_update"):
            st.session_state.cronograma_df = gerar_dataframe_inicial(
                meses, profissionais_selecionados
            )
            st.session_state.force_grid_update = True  # Ativa a flag
            st.rerun()

    # Botão de geração por IA
    if st.button("✨ Generate Suggestion with AI"):
        objetivos = st.session_state.get("objetivos", "")
        diagnostico = st.session_state.get("resultado_diagnostico", "")
        profissionais_selecionados = st.session_state.get(
            "multiselect_profissionais", []
        )
        df = gerar_cronograma_ia_openai(
            diagnostico, objetivos, meses, profissionais_selecionados
        )

        if not df.empty:
            st.session_state.cronograma_df = df
            st.session_state.last_meses = meses
            st.session_state.last_profissionais = profissionais_selecionados
            st.session_state.force_grid_update = True  # Ativa a flag
            st.rerun()
        else:
            st.warning(
                "⚠️ The AI did not return a valid timeline. Please check the response above."
            )

    # Seção de valores financeiros com destaque
    if not st.session_state.cronograma_df.empty:
        df = st.session_state.cronograma_df.copy()

        # Garante que as colunas necessárias existam
        if "Custo Hora" not in df.columns:
            df["Custo Hora"] = df["Profissional"].map(
                {p["cargo"]: p["custo_hora"] for p in PROFISSIONAIS_DISPONIVEIS}
            )

        if "Horas" in df.columns and "Custo Hora" in df.columns:
            df["Custo Total"] = df["Horas"] * df["Custo Hora"]
            custo_total = df["Custo Total"].sum()

            if st.session_state.modelo_comercial == "Fixed-price":
                margem = st.number_input(
                    "Margem (%):",
                    min_value=0,
                    max_value=100,
                    value=st.session_state.margem_fixed_price,
                    key="input_margem",
                )
                preco_final = custo_total * (1 + margem / 100)
                st.session_state.margem_fixed_price = margem
            else:
                preco_final = custo_total

            # Exibição dos valores com destaque
            st.markdown(
                """
            <style>
            .financial-card {
                border-radius: 10px;
                padding: 15px;
                background-color: #f8f9fa;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 5px solid #2e86de;
            }
            .financial-title {
                font-size: 16px;
                color: #495057;
                margin-bottom: 5px;
            }
            .financial-value {
                font-size: 24px;
                font-weight: bold;
                color: #2b2d42;
            }
            </style>
            """,
                unsafe_allow_html=True,
            )

            cols = st.columns(3)
            with cols[0]:
                st.markdown(
                    f"""
                <div class="financial-card">
                    <div class="financial-title">Total Base Cost</div>
                    <div class="financial-value">R$ {custo_total:,.2f}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with cols[1]:
                if st.session_state.modelo_comercial == "Fixed-price":
                    st.markdown(
                        f"""
                    <div class="financial-card">
                        <div class="financial-title">Final Price(+{margem}%)</div>
                        <div class="financial-value">R$ {preco_final:,.2f}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                    <div class="financial-card">
                        <div class="financial-title">T&M Estimate</div>
                        <div class="financial-value">R$ {preco_final:,.2f}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            with cols[2]:
                horas_totais = df["Horas"].sum()
                st.markdown(
                    f"""
                <div class="financial-card">
                    <div class="financial-title">Total Hours</div>
                    <div class="financial-value">{horas_totais:,.0f}h</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Atualiza os totais no session_state
            st.session_state.total_geral = custo_total
            st.session_state.total_com_adicional = preco_final

    # Visualizações em abas
    if not st.session_state.cronograma_df.empty:
        # Filtra apenas pelos profissionais selecionados
        df_filtrado = st.session_state.cronograma_df[
            st.session_state.cronograma_df["Profissional"].isin(
                profissionais_selecionados
            )
        ].copy()

        tab1, tab2, tab3 = st.tabs(["📋 Editable Table", "📊 Views", "📅 Timeline"])

        with tab1:
            # Configuração da tabela interativa
            gb = GridOptionsBuilder.from_dataframe(df_filtrado)
            gb.configure_default_column(editable=True)
            gb.configure_column("Mês", type=["numericColumn"], editable=False)
            gb.configure_column("Profissional", editable=False)
            gb.configure_column("Horas", type=["numericColumn"])
            gb.configure_column("Custo Hora", type=["numericColumn"])
            gb.configure_column("Custo Total", type=["numericColumn"], editable=False)

            grid_options = gb.build()

            # Usamos a flag force_grid_update como parte da chave para forçar recriação
            grid_key = f"cronograma_grid_{st.session_state.force_grid_update}"

            grid_response = AgGrid(
                df_filtrado,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.VALUE_CHANGED,
                fit_columns_on_grid_load=True,
                height=400,
                theme="streamlit",
                key=grid_key,
            )

            # Reseta a flag após a atualização
            st.session_state.force_grid_update = False

            # Atualiza o session_state imediatamente após edições
            if grid_response["data"] is not None:
                df_editado = pd.DataFrame(grid_response["data"])

                if st.button("💾 Save Changes", key="salvar_alteracoes"):
                    df_editado["Custo Total"] = (
                        df_editado["Horas"] * df_editado["Custo Hora"]
                    )
                    st.session_state.cronograma_df = df_editado
                    st.session_state.salvar_alteracoes_pendente = True
                    st.success("✅ Changes Saved!")
                    st.rerun()

            # Recalcular valores totais após rerun
            if st.session_state.get("salvar_alteracoes_pendente"):
                df = st.session_state.cronograma_df
                st.session_state.total_geral = df["Custo Total"].sum()

                if st.session_state.modelo_comercial == "Fixed-price":
                    margem = st.session_state.margem_fixed_price
                    preco_final = st.session_state.total_geral * (1 + margem / 100)
                else:
                    preco_final = st.session_state.total_geral

                st.session_state.total_com_adicional = preco_final

                # Resetar a flag após uso
                st.session_state.salvar_alteracoes_pendente = False

        with tab2:
            col1, col2 = st.columns(2)

            with col1:
                # Gráfico de distribuição percentual de horas
                if not df_filtrado.empty and "Horas" in df_filtrado.columns:
                    total_horas = df_filtrado["Horas"].sum()
                    df_perc = (
                        df_filtrado.groupby("Profissional")["Horas"].sum().reset_index()
                    )
                    df_perc["% Total"] = (df_perc["Horas"] / total_horas * 100).round(1)

                    fig = px.bar(
                        df_perc.sort_values("Horas", ascending=True),
                        x="Horas",
                        y="Profissional",
                        orientation="h",
                        text="% Total",
                        title=f"Distribuição de Horas (Total: {total_horas}h)",
                        color="Profissional",
                    )

                    fig.update_traces(
                        texttemplate="%{text}%",
                        textposition="inside",
                        marker_line_color="white",
                        marker_line_width=1,
                    )

                    fig.update_layout(
                        showlegend=False,
                        xaxis=dict(title="Horas", range=[0, total_horas * 1.1]),
                        yaxis=dict(title=""),
                        uniformtext_minsize=10,
                    )

                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Gráfico de horas por profissional
                if not df_filtrado.empty and "Horas" in df_filtrado.columns:
                    df_sum = (
                        df_filtrado.groupby("Profissional")["Horas"].sum().reset_index()
                    )
                    fig2 = px.bar(
                        df_sum,
                        x="Profissional",
                        y="Horas",
                        title="Horas por Profissional",
                        color="Profissional",
                        text="Horas",
                    )

                    fig2.update_traces(
                        texttemplate="%{text:.0f}h",
                        textposition="outside",
                        textfont_size=12,
                        marker_line_width=0.5,
                    )

                    fig2.update_layout(
                        showlegend=False,
                        xaxis_title="Profissionais",
                        yaxis_title="Horas Totais",
                        uniformtext_minsize=8,
                    )

                    st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            # Gráfico de Gantt
            df_gantt = df_filtrado[df_filtrado["Horas"] > 0].copy()

            if not df_gantt.empty:
                try:
                    # Cálculo das datas para o Gantt
                    df_gantt["Start"] = pd.to_datetime("2023-01-01") + pd.to_timedelta(
                        (df_gantt["Mês"] - 1) * 30, unit="days"
                    )
                    df_gantt["Finish"] = df_gantt["Start"] + pd.to_timedelta(
                        30, unit="days"
                    )

                    # Criar label com horas
                    df_gantt["Label"] = df_gantt["Horas"].astype(str) + "h"

                    fig = px.timeline(
                        df_gantt,
                        x_start="Start",
                        x_end="Finish",
                        y="Profissional",
                        color="Profissional",
                        title="Cronograma (Gantt Chart)",
                        hover_data=["Horas", "Custo Total"],
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        text="Label",
                    )

                    fig.update_traces(
                        textposition="inside",
                        textfont_size=12,
                        textfont_color="white",
                        insidetextanchor="middle",
                    )

                    fig.update_yaxes(autorange="reversed", title="Profissionais")

                    fig.update_xaxes(
                        title="Timeline", tickformat="%b %Y", dtick="M1", tickangle=45
                    )

                    fig.update_layout(
                        height=500,
                        showlegend=False,
                        margin=dict(l=50, r=50, t=80, b=50),
                        hoverlabel=dict(
                            bgcolor="white", font_size=12, font_family="Arial"
                        ),
                    )

                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Erro ao gerar gráfico Gantt: {str(e)}")
                    st.text_area(
                        "Dados usados no Gantt:", value=df_gantt.to_string(), height=200
                    )

    # Botão de exportação (só aparece se houver dados)
    if not st.session_state.cronograma_df.empty:
        st.download_button(
            "💾 Export Timeline (CSV)",
            data=st.session_state.cronograma_df.to_csv(index=False, sep=";").encode(
                "utf-8"
            ),
            file_name=f"cronograma_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            help="Exporta o cronograma atual para arquivo CSV",
        )

    # Mensagem inicial se não houver dados
    if st.session_state.cronograma_df.empty:
        st.info("ℹ️ Configure the parameters and click 'Update Schedule' to begin")
