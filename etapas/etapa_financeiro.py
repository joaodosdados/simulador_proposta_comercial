"""
Etapa Financeiro — Cost Estimator
Grupos, profissionais, grid de alocação mensal, NPV GP% ao vivo.
Interface compacta tipo planilha com layout similar ao IBM Cost Case.
"""

import streamlit as st
import pandas as pd

from utils.calculos import (
    Grupo,
    Profissional,
    ItemMisc,
    BANDAS,
    TAXAS_BANDA,
    HORAS_MES,
    HORAS_MES_DEFAULT,
    NPV_GP_MINIMO,
    CONTINGENCIA,
    CONTINGENCY_TABLE,
    RISK_PROFILES,
    WORK_TYPES,
    PAYMENT_TERMS_DEFAULT,
    BILLING_MODES,
    billing_mensal,
    _base_cost_mensal,
    _custo_mensal_com_misc,
    calcular_summary,
    summary_por_grupo,
    calcular_pnl,
    set_horas_mes,
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _grupos() -> list[Grupo]:
    if "grupos" not in st.session_state:
        st.session_state["grupos"] = []
    return st.session_state["grupos"]


def _n_meses() -> int:
    return st.session_state.get("n_meses", 12)


def _markup() -> float:
    return st.session_state.get("markup_input", 1.66)


def _contingencia() -> float:
    """Retorna a contingência selecionada via Risk Profile + Work Type."""
    risk = st.session_state.get("risk_profile", "Very Low")
    wtype = st.session_state.get("work_type", "III")
    return CONTINGENCY_TABLE.get(risk, {}).get(wtype, CONTINGENCIA)


def _misc_items() -> list[ItemMisc]:
    if "misc_items" not in st.session_state:
        st.session_state["misc_items"] = []
    return st.session_state["misc_items"]


def _misc_total() -> float:
    return sum(it.total for it in _misc_items())


def _billing_mode() -> str:
    return st.session_state.get("billing_mode", "cost")


def _billing_custom() -> list[float] | None:
    return st.session_state.get("billing_custom_pesos", None)


def _billing_kwargs() -> dict:
    """Retorna kwargs de billing para passar às funções de cálculo."""
    return {
        "billing_mode": _billing_mode(),
        "billing_custom": _billing_custom(),
    }


# ── CSS customizado para layout compacto ──────────────────────────────────────
def _inject_css():
    st.markdown(
        """
    <style>
    /* KPI cards */
    .kpi-bar { display: flex; gap: 12px; margin: 8px 0 16px 0; }
    .kpi-card {
        flex: 1; padding: 16px; border: 1px solid #e0e0e0;
        border-radius: 4px; text-align: center; background: #fff;
    }
    .kpi-card.highlight { border: 2px solid #24a148; background: #f0fdf4; }
    .kpi-card.danger { border: 2px solid #da1e28; background: #fff1f1; }
    .kpi-value { font-size: 1.5rem; font-weight: 700; color: #161616; }
    .kpi-value.green { color: #24a148; }
    .kpi-value.red { color: #da1e28; }
    .kpi-label { font-size: 0.75rem; color: #525252; margin-top: 4px; }

    /* Grupo container */
    .grupo-header {
        display: flex; align-items: center; gap: 8px;
        padding: 8px 0; margin-bottom: 4px;
    }

    /* Grid compacto de meses */
    .prof-grid { display: flex; align-items: center; gap: 4px; margin: 4px 0; padding: 6px 0; }
    .prof-info { min-width: 150px; }
    .prof-name { font-weight: 600; font-size: 0.85rem; color: #161616; }
    .prof-band { font-size: 0.75rem; color: #525252; }
    .mes-cell {
        width: 36px; height: 32px; text-align: center; font-size: 0.8rem;
        border: 1px solid #e0e0e0; border-radius: 2px; background: #fff;
        padding: 4px;
    }
    .mes-cell.active { background: #e8f0fe; color: #4589ff; font-weight: 600; }
    .prof-total { min-width: 70px; text-align: right; font-size: 0.85rem; font-weight: 600; }

    /* Total do grupo */
    .grupo-total {
        display: flex; justify-content: flex-end; gap: 24px;
        padding: 8px 12px; background: #f4f4f4; border-radius: 4px;
        font-weight: 600; font-size: 0.9rem; margin-top: 8px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


# ── Painel de KPIs ────────────────────────────────────────────────────────────
def _summary_bar(grupos: list[Grupo]):
    n = _n_meses()
    mk = _markup()
    if not grupos or n == 0:
        return

    cont = _contingencia()
    misc = _misc_total()
    bk = _billing_kwargs()
    s = calcular_summary(grupos, mk, n, contingencia=cont, misc_total=misc, **bk)
    if s["total_horas"] == 0:
        return

    npv_ok = s["npv_gp_ok"]
    npv_class = "highlight" if npv_ok else "danger"
    npv_val_class = "green" if npv_ok else "red"
    check = " ✓" if npv_ok else ""

    st.markdown(
        f"""
    <div class="kpi-bar">
        <div class="kpi-card">
            <div class="kpi-value">R$ {s['total_base_cost']:,.0f}</div>
            <div class="kpi-label">Base Cost</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">R$ {s['total_tcv']:,.0f}</div>
            <div class="kpi-label">TCV</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{s['markup']:.2f}x</div>
            <div class="kpi-label">Markup</div>
        </div>
        <div class="kpi-card {npv_class}">
            <div class="kpi-value {npv_val_class}">{s['npv_gp'] * 100:.2f}%{check}</div>
            <div class="kpi-label">NPV GP%</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if s["markup_min"] > 0:
        st.caption(
            f"Markup mínimo para NPV GP% ≥ {NPV_GP_MINIMO * 100:.1f}%: **{s['markup_min']:.4f}x**"
        )


# ── Tabela summary por grupo ─────────────────────────────────────────────────
def _tabela_summary(grupos: list[Grupo]):
    if not grupos:
        return
    rows = summary_por_grupo(grupos, _markup(), _n_meses(), misc_total=_misc_total())
    if not rows:
        return

    df = pd.DataFrame(rows)
    df["base_pct"] = df["base_pct"].map(lambda x: f"{x * 100:.1f}%")
    df["base_cost"] = df["base_cost"].map(lambda x: f"R$ {x:,.0f}")
    df["tcv"] = df["tcv"].map(lambda x: f"R$ {x:,.0f}")
    df["markup"] = df["markup"].map(lambda x: f"{x:.2f}x" if x > 0 else "—")
    df["taxa_hora"] = df["taxa_hora"].map(lambda x: f"R$ {x:,.0f}" if x > 0 else "—")
    df["horas"] = df["horas"].map(lambda x: f"{x:,.0f} h" if x > 0 else "—")
    df = df.rename(
        columns={
            "grupo": "Grupo",
            "horas": "Horas",
            "base_cost": "Base Cost",
            "base_pct": "Base %",
            "tcv": "TCV",
            "markup": "Markup",
            "taxa_hora": "Taxa/hora",
        }
    )
    st.dataframe(
        df[["Grupo", "Horas", "Base Cost", "Base %", "TCV", "Markup", "Taxa/hora"]],
        width="stretch",
        hide_index=True,
    )


# ── Renderiza profissional como uma linha compacta ────────────────────────────
def _render_profissional(prof: Profissional, gidx: int, pidx: int, n_meses: int):
    while len(prof.meses) < n_meses:
        prof.meses.append(0.0)

    # Dividir em: [nome+banda] [M1..Mn] [horas] [base_cost] [X]
    # Proporções: nome=2, banda=1.5, meses=n_meses * peso, horas=1, cost=1.2, x=0.5
    col_sizes = [2, 1.5] + [0.6] * n_meses + [1, 1.2, 0.5]
    cols = st.columns(col_sizes)

    # Nome
    with cols[0]:
        novo_nome = st.text_input(
            "nome",
            value=prof.nome,
            key=f"pn_{gidx}_{pidx}",
            label_visibility="collapsed",
            placeholder="Nome",
        )
        if novo_nome != prof.nome:
            prof.nome = novo_nome

    # Banda
    with cols[1]:
        banda_idx = BANDAS.index(prof.banda) if prof.banda in BANDAS else 8
        nova_banda = st.selectbox(
            "banda",
            BANDAS,
            index=banda_idx,
            key=f"pb_{gidx}_{pidx}",
            label_visibility="collapsed",
        )
        if nova_banda != prof.banda:
            prof.banda = nova_banda

    # Meses M1..Mn
    for m in range(n_meses):
        with cols[2 + m]:
            cell_key = f"u_{gidx}_{pidx}_{m}"
            val = st.number_input(
                f"M{m+1}",
                min_value=0.0,
                max_value=1.0,
                value=float(prof.meses[m]),
                step=0.5,
                format="%.1f",
                key=cell_key,
                label_visibility="collapsed",
            )
            prof.meses[m] = val

    # Horas
    with cols[2 + n_meses]:
        st.markdown(
            f"<div style='padding-top:28px;text-align:right;font-weight:600;font-size:0.85rem'>{prof.total_horas:,.0f} h</div>",
            unsafe_allow_html=True,
        )

    # Base Cost
    with cols[3 + n_meses]:
        st.markdown(
            f"<div style='padding-top:28px;text-align:right;font-weight:600;font-size:0.85rem'>R$ {prof.total_base_cost:,.0f}</div>",
            unsafe_allow_html=True,
        )

    # Remover
    with cols[4 + n_meses]:
        st.markdown("<div style='padding-top:24px'></div>", unsafe_allow_html=True)
        if st.button("✕", key=f"dp_{gidx}_{pidx}"):
            _grupos()[gidx].profissionais.pop(pidx)
            st.rerun()


# ── Renderiza um grupo ────────────────────────────────────────────────────────
def _render_grupo(grupo: Grupo, gidx: int, n_meses: int):
    with st.container(border=True):
        # Header: nome do grupo | nome prof | + profissional | remover grupo
        col_nome, col_prof_nome, col_add, col_del = st.columns([3, 2, 1.5, 1.5])
        with col_nome:
            novo_nome = st.text_input(
                "Grupo",
                value=grupo.nome,
                key=f"gn_{gidx}",
                label_visibility="collapsed",
            )
            if novo_nome != grupo.nome:
                grupo.nome = novo_nome
        with col_prof_nome:
            nome_prof = st.text_input(
                "Nome profissional",
                key=f"np_{gidx}",
                placeholder="Nome do profissional",
                label_visibility="collapsed",
            )
        with col_add:
            if st.button(
                "➕ Profissional",
                key=f"ap_{gidx}",
                width="stretch",
            ):
                nome_final = (
                    nome_prof.strip() if nome_prof.strip() else "Novo profissional"
                )
                grupo.profissionais.append(
                    Profissional(nome=nome_final, banda="Band 8", meses=[0.0] * n_meses)
                )
                st.rerun()
        with col_del:
            if st.button("🗑 Remover grupo", key=f"dg_{gidx}", width="stretch"):
                _grupos().pop(gidx)
                st.rerun()

        # Header de colunas
        if grupo.profissionais:
            header_sizes = [2, 1.5] + [0.6] * n_meses + [1, 1.2, 0.5]
            hdr = st.columns(header_sizes)
            with hdr[0]:
                st.caption("Profissional / Banda")
            for m in range(n_meses):
                with hdr[2 + m]:
                    st.caption(f"M{m+1}")
            with hdr[2 + n_meses]:
                st.caption("Horas")
            with hdr[3 + n_meses]:
                st.caption("Base Cost")

        # Profissionais
        for pidx, prof in enumerate(grupo.profissionais):
            _render_profissional(prof, gidx, pidx, n_meses)

        # Total do grupo
        if grupo.profissionais:
            st.markdown(
                f"""
            <div class="grupo-total">
                <span>Total {grupo.nome}</span>
                <span>{grupo.total_horas:,.0f} h</span>
                <span>R$ {grupo.total_base_cost:,.0f}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )


# ── Preliminary P&L ───────────────────────────────────────────────────────────
def _render_pnl(grupos: list[Grupo]):
    mk = _markup()
    n = _n_meses()
    exch = st.session_state.get("exch_rate", 5.50325)
    cont = _contingencia()
    misc = _misc_total()
    pnl = calcular_pnl(
        grupos, mk, n, exch, contingencia=cont, misc_total=misc, **_billing_kwargs()
    )

    def _row(
        label: str,
        brl: float,
        is_pct: bool = False,
        bold: bool = False,
        bg: str = "",
        color: str = "#161616",
    ):
        """Gera uma linha da tabela P&L."""
        fw = "font-weight:700;" if bold else ""
        bg_style = f"background:{bg};" if bg else ""
        if is_pct:
            brl_fmt = f"{brl * 100:.1f}%"
            usd_fmt = f"{brl * 100:.1f}%"
        else:
            usd = brl / exch if exch else 0
            brl_fmt = f"R$ {brl:,.0f}"
            usd_fmt = f"$ {usd:,.0f}"
        return (
            f'<tr style="{bg_style}{fw}color:{color}">'
            f"<td style='padding:6px 12px'>{label}</td>"
            f"<td style='padding:6px 12px;text-align:right'>{brl_fmt}</td>"
            f"<td style='padding:6px 12px;text-align:right'>{usd_fmt}</td>"
            f"</tr>"
        )

    html = """
    <table style="width:100%;border-collapse:collapse;font-size:0.85rem;font-family:monospace">
        <thead>
            <tr style="background:#525252;color:white">
                <th style="padding:8px 12px;text-align:left">Preliminary P&L</th>
                <th style="padding:8px 12px;text-align:right">BRL</th>
                <th style="padding:8px 12px;text-align:right">USD</th>
            </tr>
        </thead>
        <tbody>
    """
    # TCV / Receita
    html += _row("TCV (with taxes)", pnl["tcv"], bold=True, bg="#e8e8e8")
    html += _row("Sales Taxes %", pnl["sales_taxes_pct"], is_pct=True, color="#525252")
    html += _row("Net Price", pnl["net_price"], bold=True)
    html += _row("Revenue", pnl["revenue"], bold=True, bg="#e8e8e8")

    # Custos
    html += _row("Base Cost", pnl["base_cost"], bold=True)
    html += _row("Risk Contingency", pnl["risk_contingency"])
    html += _row(
        "Risk Contingency %", pnl["risk_contingency_pct"], is_pct=True, color="#525252"
    )
    html += _row("Total Cost", pnl["total_cost"], bold=True, bg="#e8e8e8")

    # Nominal GP / PTI
    html += _row("Nominal Gross Profit", pnl["nominal_gp"], bold=True)
    html += _row("Nominal GP %", pnl["nominal_gp_pct"], is_pct=True, color="#525252")
    html += _row("Revenue Apportionment", pnl["rev_apportionment"])
    html += _row(
        "Revenue Apportionment %",
        pnl["rev_apportionment_pct"],
        is_pct=True,
        color="#525252",
    )
    html += _row("Nominal PTI", pnl["nominal_pti"], bold=True)
    html += _row("Nominal PTI %", pnl["nominal_pti_pct"], is_pct=True, color="#525252")

    # NPV
    npv_color = "#24a148" if pnl["npv_gp_pct"] >= NPV_GP_MINIMO else "#da1e28"
    html += f'<tr style="background:#d0e2ff;font-weight:700;color:{npv_color}">'
    npv_usd = pnl["npv_gp"] / exch if exch else 0
    html += f"<td style='padding:6px 12px'>NPV GP</td>"
    html += (
        f"<td style='padding:6px 12px;text-align:right'>R$ {pnl['npv_gp']:,.0f}</td>"
    )
    html += f"<td style='padding:6px 12px;text-align:right'>$ {npv_usd:,.0f}</td></tr>"
    html += _row(
        "NPV GP %", pnl["npv_gp_pct"], is_pct=True, color=npv_color, bg="#d0e2ff"
    )
    html += _row("NPV PTI", pnl["npv_pti"], bold=True)
    html += _row("NPV PTI %", pnl["npv_pti_pct"], is_pct=True, color="#525252")

    # Contract GP
    html += f'<tr style="background:#fff3cd;font-weight:700">'
    cgp_usd = pnl["contract_gp"] / exch if exch else 0
    html += f"<td style='padding:6px 12px'>Contract GP (excl. TVM & Contingency)</td>"
    html += f"<td style='padding:6px 12px;text-align:right'>R$ {pnl['contract_gp']:,.0f}</td>"
    html += f"<td style='padding:6px 12px;text-align:right'>$ {cgp_usd:,.0f}</td></tr>"
    html += _row("CGP %", pnl["contract_gp_pct"], is_pct=True, bg="#fff3cd")

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


def _normalize_billing_pesos():
    """Callback: normaliza todos os pesos de billing para somar 100%."""
    n = _n_meses()
    pesos = [st.session_state.get(f"bill_pct_{m}", 0.0) for m in range(n)]
    total = sum(pesos)
    if total > 0:
        normalized = [p / total * 100 for p in pesos]
        for m in range(n):
            st.session_state[f"bill_pct_{m}"] = round(normalized[m], 1)
        st.session_state["billing_custom_pesos"] = normalized


# ── Billing Schedule ──────────────────────────────────────────────────────────
def _render_billing_schedule(grupos: list[Grupo]):
    """Seção de Billing Schedule — define como a receita é distribuída por mês."""
    st.subheader("📆 Billing Schedule")
    st.caption(
        "Define quando o cliente paga. Impacta diretamente o **NPV GP%** "
        "(receber antes → NPV sobe; receber depois → NPV desce)."
    )

    n = _n_meses()
    mk = _markup()
    misc = _misc_total()

    # Calcula base cost mensal (custo real por mês)
    bc_mensal = _base_cost_mensal(grupos, n)
    custo_m = _custo_mensal_com_misc(bc_mensal, misc)
    total_base = sum(custo_m)
    net_price_total = total_base * mk

    if net_price_total == 0:
        st.info("Adicione profissionais aos grupos para configurar o billing.")
        return

    # Seletor de modo
    mode_keys = list(BILLING_MODES.keys())
    current_mode = st.session_state.get("billing_mode", "cost")
    mode_idx = mode_keys.index(current_mode) if current_mode in mode_keys else 0
    chosen_mode = st.radio(
        "Modo de faturamento",
        mode_keys,
        index=mode_idx,
        format_func=lambda k: BILLING_MODES[k],
        key="billing_mode",
        horizontal=True,
    )

    # Calcula receita mensal conforme modo
    custom_pesos = st.session_state.get("billing_custom_pesos", None)
    if chosen_mode == "custom":
        # Inicializa pesos custom se necessário
        if custom_pesos is None or len(custom_pesos) < n:
            # Default: proporcional ao custo
            if total_base > 0:
                custom_pesos = [bc / total_base * 100 for bc in custo_m]
            else:
                custom_pesos = [100.0 / n] * n
            st.session_state["billing_custom_pesos"] = custom_pesos
        elif len(custom_pesos) > n:
            custom_pesos = custom_pesos[:n]
            st.session_state["billing_custom_pesos"] = custom_pesos

    receita_m = billing_mensal(
        chosen_mode,
        n,
        net_price_total,
        custo_m,
        custom_pesos if chosen_mode == "custom" else None,
    )
    tcv_m = [r / (1 - 0.0655) for r in receita_m]

    # Grid de edição (modo custom) ou visualização (outros modos)
    with st.container(border=True):
        # Header row
        header_cols = st.columns([1.2] + [1] * n + [1.2])
        with header_cols[0]:
            st.caption("")
        for m in range(n):
            with header_cols[1 + m]:
                st.caption(f"M{m+1}")
        with header_cols[-1]:
            st.caption("Total")

        # Row 1: Custo mensal (referência, não editável)
        cost_cols = st.columns([1.2] + [1] * n + [1.2])
        with cost_cols[0]:
            st.markdown(
                "<div style='font-size:0.8rem;color:#525252;padding-top:8px'>Base Cost</div>",
                unsafe_allow_html=True,
            )
        for m in range(n):
            with cost_cols[1 + m]:
                bc_val = custo_m[m]
                bg = "#f4f4f4" if bc_val == 0 else "#e8f0fe"
                st.markdown(
                    f"<div style='text-align:center;font-size:0.8rem;padding:6px;background:{bg};border-radius:4px'>"
                    f"R$ {bc_val:,.0f}</div>",
                    unsafe_allow_html=True,
                )
        with cost_cols[-1]:
            st.markdown(
                f"<div style='text-align:center;font-weight:700;font-size:0.85rem;padding-top:6px'>"
                f"R$ {total_base:,.0f}</div>",
                unsafe_allow_html=True,
            )

        # Row 2: Billing (TCV mensal) — editável em custom, readonly nos outros
        bill_cols = st.columns([1.2] + [1] * n + [1.2])
        with bill_cols[0]:
            st.markdown(
                "<div style='font-size:0.8rem;font-weight:700;color:#161616;padding-top:8px'>TCV Billing</div>",
                unsafe_allow_html=True,
            )

        if chosen_mode == "custom":
            # Inicializa session_state para cada widget (evita conflito value + session_state)
            for m in range(n):
                if f"bill_pct_{m}" not in st.session_state:
                    st.session_state[f"bill_pct_{m}"] = (
                        float(custom_pesos[m]) if custom_pesos else 0.0
                    )

            # Inputs editáveis — o usuário edita % (auto-normalizado)
            for m in range(n):
                with bill_cols[1 + m]:
                    st.number_input(
                        f"M{m+1}%",
                        min_value=0.0,
                        max_value=100.0,
                        step=1.0,
                        format="%.1f",
                        key=f"bill_pct_{m}",
                        label_visibility="collapsed",
                        on_change=_normalize_billing_pesos,
                    )

            # Ler pesos atualizados (já normalizados pelo callback)
            custom_pesos = [
                st.session_state.get(f"bill_pct_{m}", 0.0) for m in range(n)
            ]
            st.session_state["billing_custom_pesos"] = custom_pesos

            # Recalcular com pesos atualizados
            receita_m = billing_mensal(
                "custom",
                n,
                net_price_total,
                custo_m,
                custom_pesos,
            )
            tcv_m = [r / (1 - 0.0655) for r in receita_m]

            with bill_cols[-1]:
                st.markdown(
                    "<div style='text-align:center;font-weight:700;font-size:0.85rem;"
                    "padding-top:6px;color:#24a148'>100.0%</div>",
                    unsafe_allow_html=True,
                )

            st.caption("💡 Os pesos são auto-normalizados para somar 100%.")
        else:
            # Somente exibição
            for m in range(n):
                with bill_cols[1 + m]:
                    val = tcv_m[m]
                    bg = "#f4f4f4" if val == 0 else "#d0e2ff"
                    st.markdown(
                        f"<div style='text-align:center;font-size:0.8rem;padding:6px;"
                        f"background:{bg};border-radius:4px;font-weight:600'>"
                        f"R$ {val:,.0f}</div>",
                        unsafe_allow_html=True,
                    )
            with bill_cols[-1]:
                st.markdown(
                    f"<div style='text-align:center;font-weight:700;font-size:0.85rem;padding-top:6px'>"
                    f"R$ {sum(tcv_m):,.0f}</div>",
                    unsafe_allow_html=True,
                )

        # Row 3: Net Price mensal
        np_cols = st.columns([1.2] + [1] * n + [1.2])
        with np_cols[0]:
            st.markdown(
                "<div style='font-size:0.8rem;color:#525252;padding-top:8px'>Net Price</div>",
                unsafe_allow_html=True,
            )
        for m in range(n):
            with np_cols[1 + m]:
                val = receita_m[m]
                bg = "#f4f4f4" if val == 0 else "#e8f0fe"
                st.markdown(
                    f"<div style='text-align:center;font-size:0.8rem;padding:6px;"
                    f"background:{bg};border-radius:4px'>"
                    f"R$ {val:,.0f}</div>",
                    unsafe_allow_html=True,
                )
        with np_cols[-1]:
            st.markdown(
                f"<div style='text-align:center;font-weight:700;font-size:0.85rem;padding-top:6px'>"
                f"R$ {sum(receita_m):,.0f}</div>",
                unsafe_allow_html=True,
            )

    # Info sobre impacto no NPV
    if chosen_mode == "cost":
        st.info(
            "**Proporcional ao Custo**: faturamento segue o staffing plan. "
            "Meses com mais profissionais alocados faturam mais."
        )
    elif chosen_mode == "equal":
        st.info(
            "**Igualitário**: mesmo valor em cada mês ativo. "
            "Se os custos são concentrados no início, o NPV tende a cair pois "
            "a receita é diluída ao longo do contrato."
        )
    else:
        st.info(
            "**Customizado**: distribua a receita conforme acordo com o cliente. "
            "Front-loading (mais nos primeiros meses) melhora o NPV. "
            "Back-loading (mais nos últimos) reduz o NPV."
        )

    # NPV GP% replicado para referência rápida
    cont = _contingencia()
    bk = _billing_kwargs()
    s = calcular_summary(grupos, mk, n, contingencia=cont, misc_total=misc, **bk)
    if s["total_horas"] > 0:
        npv = s["npv_gp"]
        npv_ok = s["npv_gp_ok"]
        color = "#24a148" if npv_ok else "#da1e28"
        border = f"2px solid {color}"
        bg = "#f0fdf4" if npv_ok else "#fff1f1"
        check = " ✓" if npv_ok else ""
        st.markdown(
            f'<div style="display:flex;gap:12px;margin:8px 0">'
            f'<div style="flex:1;padding:12px;border:{border};border-radius:4px;'
            f'text-align:center;background:{bg}">'
            f'<div style="font-size:1.3rem;font-weight:700;color:{color}">'
            f'{npv * 100:.2f}%{check}</div>'
            f'<div style="font-size:0.75rem;color:#525252">NPV GP%</div></div>'
            f'<div style="flex:1;padding:12px;border:1px solid #e0e0e0;'
            f'border-radius:4px;text-align:center;background:#fff">'
            f'<div style="font-size:1.3rem;font-weight:700;color:#161616">'
            f'R$ {s["total_tcv"]:,.0f}</div>'
            f'<div style="font-size:0.75rem;color:#525252">TCV</div></div>'
            f'<div style="flex:1;padding:12px;border:1px solid #e0e0e0;'
            f'border-radius:4px;text-align:center;background:#fff">'
            f'<div style="font-size:1.3rem;font-weight:700;color:#161616">'
            f'{s["markup_min"]:.4f}x</div>'
            f'<div style="font-size:0.75rem;color:#525252">Markup mínimo</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_glossario():
    with st.expander("📖 Glossário de siglas e termos", expanded=False):
        st.markdown("""
| Sigla | Significado |
|-------|-------------|
| **TCV** | *Total Contract Value* — Valor total do contrato incluindo impostos (ISS + PIS/COFINS). |
| **Net Price** | Preço líquido (TCV sem impostos). Equivale a Base Cost × Markup. |
| **Revenue** | Receita reconhecida = Net Price (sem penalty contingency). |
| **Base Cost** | Custo-base total: soma de (horas × taxa/hora da banda) de todos os profissionais. |
| **Risk Contingency** | Reserva de contingência aplicada sobre o Base Cost (padrão 2%). |
| **Total Cost** | Base Cost + Risk Contingency. |
| **Markup** | Fator multiplicador aplicado ao Base Cost para gerar o Net Price. |
| **Nominal GP** | *Gross Profit* nominal = Revenue − Total Cost. |
| **GP %** | Margem bruta = Nominal GP / Revenue. |
| **Revenue Apportionment** | Alocação corporativa IBM (19.5% da Revenue). |
| **PTI** | *Pre-Tax Income* = Nominal GP − Revenue Apportionment. |
| **NPV GP** | *Net Present Value* do Gross Profit — GP descontado mensalmente pelo WACC. |
| **NPV GP %** | NPV GP / NPV Revenue. Piso mínimo IBM: **5.70%**. |
| **NPV PTI** | NPV do GP menos NPV do Revenue Apportionment. |
| **Contract GP** | Revenue − Base Cost (sem contingência nem TVM). |
| **CGP %** | Contract GP / Revenue. |
| **WACC** | *Weighted Average Cost of Capital* — Taxa de desconto (18.5% a.a. → ~1.42% a.m.). |
| **ISS** | Imposto Sobre Serviços (2.9%). |
| **PIS/COFINS** | Contribuições federais (3.65%). |
| **TVM** | *Time Value of Money* — Efeito do desconto temporal (WACC). |
""")


# ── Render principal ──────────────────────────────────────────────────────────
def render():
    st.subheader("💰 Cost Estimator")
    _inject_css()

    # Sincroniza HORAS_MES com session_state antes de qualquer cálculo/render
    set_horas_mes(st.session_state.get("horas_mes", HORAS_MES_DEFAULT))

    # Tabela de referência de taxas
    with st.expander("📋 IBM Band Rates (2026 Cost Case)", expanded=False):
        rates_df = pd.DataFrame(
            [
                {
                    "Banda": b,
                    "Taxa/hora (BRL)": f"R$ {t:,.2f}",
                    "Horas/mês": f"{HORAS_MES:.0f}",
                    "Custo/mês (full)": f"R$ {t * HORAS_MES:,.0f}",
                }
                for b, t in TAXAS_BANDA.items()
            ]
        )
        st.dataframe(rates_df, width="stretch", hide_index=True)

    # Configurações globais
    with st.expander("Project Settings", expanded=False):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.number_input(
                "Duration (months)",
                min_value=1,
                max_value=120,
                value=_n_meses(),
                key="n_meses",
                step=1,
            )
        with c2:
            st.number_input(
                "Markup",
                min_value=1.0,
                max_value=5.0,
                value=_markup(),
                key="markup_input",
                step=0.01,
                format="%.2f",
            )
        with c3:
            horas_mes = st.number_input(
                "Hours/month",
                min_value=40.0,
                max_value=250.0,
                value=float(st.session_state.get("horas_mes", HORAS_MES_DEFAULT)),
                key="horas_mes",
                step=1.0,
                format="%.0f",
                help="Horas mensais do profissional (ex: 160, 168, 173, 176)",
            )
            set_horas_mes(horas_mes)
        with c4:
            st.number_input(
                "Exchange rate (USD/BRL)",
                min_value=1.0,
                value=5.50325,
                key="exch_rate",
                step=0.001,
                format="%.5f",
            )
        with c5:
            st.number_input(
                "WACC anual (%)",
                min_value=0.0,
                max_value=50.0,
                value=18.5,
                key="wacc_pct",
                step=0.1,
                format="%.1f",
            )

        # Segunda linha: Payment Terms + Risk Contingency
        st.markdown("---")
        st.caption("Payment Terms & Risk Contingency")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.number_input(
                "Payment Terms (dias)",
                min_value=0,
                max_value=180,
                value=st.session_state.get("payment_terms", PAYMENT_TERMS_DEFAULT),
                key="payment_terms",
                step=10,
                help="Prazo de pagamento em dias. Cliente diz 30 = IBM usa 40, Cliente diz 60 = IBM usa 70.",
            )
        with r2:
            risk_idx = RISK_PROFILES.index(
                st.session_state.get("risk_profile", "Very Low")
            )
            st.selectbox(
                "Risk Profile",
                RISK_PROFILES,
                index=risk_idx,
                key="risk_profile",
                help="Very Low (DRA 1-2), Low (DRA 3-4), Moderate (DRA 5-6), High (DRA 7-9)",
            )
        with r3:
            wt_keys = list(WORK_TYPES.keys())
            wt_labels = [f"{k} — {v}" for k, v in WORK_TYPES.items()]
            wt_idx = wt_keys.index(st.session_state.get("work_type", "III"))
            chosen_wt = st.selectbox(
                "Work Type",
                wt_keys,
                index=wt_idx,
                key="work_type",
                format_func=lambda k: f"{k} — {WORK_TYPES[k]}",
            )

        # Mostra tabela de contingência como referência
        cont_pct = _contingencia()
        st.info(
            f"Contingencia aplicada: **{cont_pct * 100:.0f}%** (Risk: {st.session_state.get('risk_profile', 'Very Low')}, Work Type: {st.session_state.get('work_type', 'III')})"
        )

        with st.expander("Tabela de Contingencia (referencia)", expanded=False):
            rows = []
            for rp, dra_map in [
                ("Very Low", "1, 2"),
                ("Low", "3, 4"),
                ("Moderate", "5, 6"),
                ("High", "7, 8, 9"),
            ]:
                row = {"Risk Profile": rp, "DRA": dra_map}
                for wt in ["I", "II", "III"]:
                    row[f"Type {wt}"] = f"{CONTINGENCY_TABLE[rp][wt] * 100:.0f}%"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    grupos = _grupos()
    n = _n_meses()

    # Painel de resultado ao vivo (KPI cards)
    _summary_bar(grupos)

    # Header "Grupos" + botão "+ Novo grupo"
    col_label, col_spacer, col_nome, col_btn = st.columns([1, 2, 3, 1.5])
    with col_label:
        st.markdown("**Grupos**")
    with col_nome:
        novo_grupo_nome = st.text_input(
            "nome",
            key="_novo_grupo_nome",
            placeholder="Ex: TRANSITION, GOVERNANCE...",
            label_visibility="collapsed",
        )
    with col_btn:
        if st.button("+ Novo grupo", width="stretch"):
            nome = novo_grupo_nome.strip() or f"GRUPO {len(grupos) + 1}"
            grupos.append(Grupo(nome=nome))
            st.rerun()

    # Renderiza cada grupo
    for gidx, grupo in enumerate(grupos):
        _render_grupo(grupo, gidx, n)

    # ── Miscellaneous (viagens, licenças, despesas avulsas) ───────────────
    misc_items = _misc_items()

    with st.container(border=True):
        # Header: mesmo padrão dos grupos
        col_nome, col_desc_input, col_add, col_del_all = st.columns([3, 2, 1.5, 1.5])
        with col_nome:
            st.markdown("**MISCELLANEOUS**")
            st.caption("Viagens, licencas, despesas avulsas")
        with col_desc_input:
            novo_desc = st.text_input(
                "desc_novo",
                key="_novo_misc_desc",
                placeholder="Descricao do item",
                label_visibility="collapsed",
            )
        with col_add:
            if st.button("+ Item", key="add_misc", width="stretch"):
                desc_final = novo_desc.strip() if novo_desc.strip() else "Novo item"
                misc_items.append(
                    ItemMisc(descricao=desc_final, quantidade=1, valor_unitario=0.0)
                )
                st.rerun()
        with col_del_all:
            if misc_items and st.button(
                "Limpar tudo", key="clear_misc", width="stretch"
            ):
                misc_items.clear()
                st.rerun()

        # Header de colunas
        if misc_items:
            hdr = st.columns([3, 1.5, 2, 2, 0.5])
            with hdr[0]:
                st.caption("Descricao")
            with hdr[1]:
                st.caption("Qtd")
            with hdr[2]:
                st.caption("Valor unit. (BRL)")
            with hdr[3]:
                st.caption("Total")

        # Itens
        for midx, item in enumerate(misc_items):
            cols = st.columns([3, 1.5, 2, 2, 0.5])
            with cols[0]:
                desc = st.text_input(
                    "desc",
                    value=item.descricao,
                    key=f"misc_d_{midx}",
                    label_visibility="collapsed",
                    placeholder="Ex: Viagem SP-BH",
                )
                item.descricao = desc
            with cols[1]:
                qtd = st.number_input(
                    "qtd",
                    min_value=1,
                    value=item.quantidade,
                    key=f"misc_q_{midx}",
                    label_visibility="collapsed",
                    step=1,
                )
                item.quantidade = qtd
            with cols[2]:
                val = st.number_input(
                    "val",
                    min_value=0.0,
                    value=item.valor_unitario,
                    key=f"misc_v_{midx}",
                    label_visibility="collapsed",
                    step=100.0,
                    format="%.2f",
                )
                item.valor_unitario = val
            with cols[3]:
                st.markdown(
                    f"<div style='padding-top:28px;text-align:right;font-weight:600;font-size:0.85rem'>R$ {item.total:,.0f}</div>",
                    unsafe_allow_html=True,
                )
            with cols[4]:
                st.markdown(
                    "<div style='padding-top:24px'></div>", unsafe_allow_html=True
                )
                if st.button("X", key=f"misc_rm_{midx}"):
                    misc_items.pop(midx)
                    st.rerun()

        # Total do misc (mesmo estilo do grupo-total)
        total_misc = _misc_total()
        if total_misc > 0:
            st.markdown(
                f"""
            <div class="grupo-total">
                <span>Total Miscellaneous</span>
                <span>R$ {total_misc:,.0f}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Highlight células ativas (valor > 0) com fundo azul claro
    active_keys = []
    for gidx, grupo in enumerate(grupos):
        for pidx, prof in enumerate(grupo.profissionais):
            for m in range(min(n, len(prof.meses))):
                if prof.meses[m] > 0:
                    active_keys.append(f"u_{gidx}_{pidx}_{m}")
    if active_keys:
        rules = ", ".join(
            f'div[data-testid="stNumberInput"]:has(input[aria-label="M{k.split("_")[-1]}"]) input'
            for k in active_keys
        )
        # Approach: target by unique key class Streamlit adds to widget containers
        css_rules = "\n".join(
            f"div.st-key-{k} input {{ background-color: #e8f0fe !important; color: #4589ff !important; font-weight: 600 !important; }}"
            for k in active_keys
        )
        st.markdown(f"<style>{css_rules}</style>", unsafe_allow_html=True)

    # Tabela summary
    if grupos and any(g.total_horas > 0 for g in grupos):
        # ── Billing Schedule ──────────────────────────────────────────
        st.divider()
        _render_billing_schedule(grupos)

        st.divider()
        st.subheader("📊 Summary por grupo")
        _tabela_summary(grupos)

        # ── Preliminary P&L ───────────────────────────────────────────
        st.divider()
        st.subheader("📋 Preliminary P&L")
        _render_pnl(grupos)

        # ── Glossário ─────────────────────────────────────────────────
        _render_glossario()
