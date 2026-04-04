import streamlit as st
import json
import os
import markdown as _md
from datetime import datetime

try:
    from weasyprint import HTML as _WeasyHTML

    _HAS_WEASYPRINT = True
except (ImportError, OSError):
    _HAS_WEASYPRINT = False
from utils.calculos import (
    Grupo,
    calcular_summary,
    calcular_pnl,
    summary_por_grupo,
    NPV_GP_MINIMO,
    CONTINGENCIA,
    CONTINGENCY_TABLE,
    HORAS_MES_DEFAULT,
    BILLING_MODES,
    WORK_TYPES,
    set_horas_mes,
)

SALVAMENTO_DIR = "simulacoes_salvas"
os.makedirs(SALVAMENTO_DIR, exist_ok=True)


# ── Helpers comuns ────────────────────────────────────────────────────────────


def _load_state():
    """Carrega todos os dados relevantes do session_state."""
    grupos = st.session_state.get("grupos", [])
    markup = st.session_state.get("markup_input", 1.66)
    n_meses = st.session_state.get("n_meses", 12)
    set_horas_mes(st.session_state.get("horas_mes", HORAS_MES_DEFAULT))
    risk = st.session_state.get("risk_profile", "Very Low")
    wtype = st.session_state.get("work_type", "III")
    cont = CONTINGENCY_TABLE.get(risk, {}).get(wtype, CONTINGENCIA)
    misc_items = st.session_state.get("misc_items", [])
    misc_total = sum(it.total for it in misc_items)
    billing_kw = {
        "billing_mode": st.session_state.get("billing_mode", "cost"),
        "billing_custom": st.session_state.get("billing_custom_pesos", None),
    }
    return {
        "grupos": grupos,
        "markup": markup,
        "n_meses": n_meses,
        "risk": risk,
        "wtype": wtype,
        "cont": cont,
        "misc_items": misc_items,
        "misc_total": misc_total,
        "billing_kw": billing_kw,
        "horas_mes": st.session_state.get("horas_mes", HORAS_MES_DEFAULT),
        "wacc_pct": st.session_state.get("wacc_pct", 18.5),
        "payment_terms": st.session_state.get("payment_terms", 40),
        "exch_rate": st.session_state.get("exch_rate", 5.50325),
        "diagnostico": st.session_state.get("resultado_diagnostico", ""),
        "objetivos": st.session_state.get("objetivos", ""),
        "solucao": st.session_state.get("solucao_tecnica", ""),
        "premissas": st.session_state.get("premissas_limitacoes", ""),
        "tipo_contrato": st.session_state.get("tipo_contrato", ""),
        "proposal_items": st.session_state.get("proposal_items", []),
    }


# ── PDF Generation ────────────────────────────────────────────────────────────


def gerar_html_proposta():
    d = _load_state()
    grupos = d["grupos"]
    markup = d["markup"]
    n_meses = d["n_meses"]

    summary = (
        calcular_summary(
            grupos,
            markup,
            n_meses,
            contingencia=d["cont"],
            misc_total=d["misc_total"],
            **d["billing_kw"],
        )
        if grupos
        else {}
    )
    pnl = (
        calcular_pnl(
            grupos,
            markup,
            n_meses,
            contingencia=d["cont"],
            misc_total=d["misc_total"],
            **d["billing_kw"],
        )
        if grupos
        else {}
    )
    grupo_rows = (
        summary_por_grupo(grupos, markup, n_meses, misc_total=d["misc_total"])
        if grupos
        else []
    )

    # ── KPI cards HTML for PDF ──
    kpi_html = ""
    if summary:
        npv_color = (
            "#24a148" if summary.get("npv_gp", 0) >= NPV_GP_MINIMO else "#da1e28"
        )
        kpis = [
            ("TCV", f"R$ {summary.get('total_tcv', 0):,.0f}"),
            ("NPV GP%", f"{summary.get('npv_gp', 0)*100:.2f}%"),
            ("Markup", f"{summary.get('markup', 0):.2f}x"),
            ("Markup mín.", f"{summary.get('markup_min', 0):.4f}x"),
            ("Taxa/hora", f"R$ {summary.get('taxa_hora', 0):,.0f}/h"),
            ("Duração", f"{n_meses} meses"),
        ]
        kpi_html = '<div style="display:flex;gap:12px;margin:16px 0;flex-wrap:wrap">'
        for label, val in kpis:
            color = npv_color if label == "NPV GP%" else "#161616"
            kpi_html += (
                f'<div style="background:#f4f4f4;padding:14px 18px;flex:1;min-width:120px;'
                f'text-align:center;border-radius:4px">'
                f'<div style="font-size:18pt;font-weight:700;color:{color}">{val}</div>'
                f'<div style="font-size:9pt;color:#525252;margin-top:4px">{label}</div></div>'
            )
        kpi_html += "</div>"

    # ── Group table ──
    group_table = ""
    if grupo_rows:
        group_table = (
            "<table><tr><th>Grupo</th><th>Horas</th><th>Base Cost</th>"
            "<th>Base %</th><th>TCV</th><th>Markup</th><th>Taxa/h</th></tr>"
        )
        for r in grupo_rows:
            group_table += (
                f"<tr><td>{r['grupo']}</td><td>{r['horas']:,.0f} h</td>"
                f"<td>R$ {r['base_cost']:,.0f}</td><td>{r['base_pct']*100:.1f}%</td>"
                f"<td>R$ {r['tcv']:,.0f}</td><td>{r['markup']:.2f}x</td>"
                f"<td>R$ {r['taxa_hora']:,.0f}</td></tr>"
            )
        if summary:
            group_table += (
                f'<tr style="font-weight:bold;border-top:2px solid #161616">'
                f"<td>TOTAL</td><td>{summary['total_horas']:,.0f} h</td>"
                f"<td>R$ {summary['total_base_cost']:,.0f}</td><td>100%</td>"
                f"<td>R$ {summary['total_tcv']:,.0f}</td>"
                f"<td>{summary['markup']:.2f}x</td>"
                f"<td>R$ {summary['taxa_hora']:,.0f}</td></tr>"
            )
        group_table += "</table>"

    # ── P&L table ──
    pnl_table = ""
    if pnl:
        rows = [
            ("TCV (com impostos)", f"R$ {pnl['tcv']:,.0f}", ""),
            (
                "Sales Taxes (ISS + PIS/COFINS)",
                f"R$ {pnl['tcv'] - pnl['net_price']:,.0f}",
                f"{pnl['sales_taxes_pct']*100:.2f}%",
            ),
            ("Net Price / Revenue", f"R$ {pnl['revenue']:,.0f}", ""),
            ("Base Cost", f"R$ {pnl['base_cost']:,.0f}", ""),
            (
                "Risk & Contingency",
                f"R$ {pnl['risk_contingency']:,.0f}",
                f"{pnl['risk_contingency_pct']*100:.1f}%",
            ),
            ("Total Cost", f"R$ {pnl['total_cost']:,.0f}", ""),
            (
                "Nominal GP",
                f"R$ {pnl['nominal_gp']:,.0f}",
                f"{pnl['nominal_gp_pct']*100:.2f}%",
            ),
            (
                "Rev. Apportionment",
                f"R$ {pnl['rev_apportionment']:,.0f}",
                f"{pnl['rev_apportionment_pct']*100:.1f}%",
            ),
            (
                "Nominal PTI",
                f"R$ {pnl['nominal_pti']:,.0f}",
                f"{pnl['nominal_pti_pct']*100:.2f}%",
            ),
            ("NPV GP", f"R$ {pnl['npv_gp']:,.0f}", f"{pnl['npv_gp_pct']*100:.2f}%"),
            ("NPV PTI", f"R$ {pnl['npv_pti']:,.0f}", f"{pnl['npv_pti_pct']*100:.2f}%"),
            (
                "Contract GP (excl. Contingency)",
                f"R$ {pnl['contract_gp']:,.0f}",
                f"{pnl['contract_gp_pct']*100:.2f}%",
            ),
        ]
        highlight = {"Nominal GP", "NPV GP", "Contract GP (excl. Contingency)"}
        pnl_table = (
            '<table><tr><th style="width:55%">Item</th><th>Valor</th><th>%</th></tr>'
        )
        for label, val, pct in rows:
            style = (
                ' style="background:#fff3cd;font-weight:700"'
                if label in highlight
                else ""
            )
            pnl_table += f"<tr{style}><td>{label}</td><td>{val}</td><td>{pct}</td></tr>"
        pnl_table += "</table>"

    # ── Parameters box ──
    billing_label = BILLING_MODES.get(
        d["billing_kw"]["billing_mode"], "Proporcional ao Custo"
    )
    wtype_label = WORK_TYPES.get(d["wtype"], d["wtype"])
    params_html = (
        '<table class="params">'
        f"<tr><td>Duração</td><td>{n_meses} meses</td></tr>"
        f"<tr><td>Markup</td><td>{markup:.2f}x</td></tr>"
        f"<tr><td>Horas/mês</td><td>{d['horas_mes']:.0f}</td></tr>"
        f"<tr><td>WACC</td><td>{d['wacc_pct']:.1f}%</td></tr>"
        f"<tr><td>Payment Terms</td><td>{d['payment_terms']} dias</td></tr>"
        f"<tr><td>Câmbio USD/BRL</td><td>{d['exch_rate']:.5f}</td></tr>"
        f"<tr><td>Risk Profile</td><td>{d['risk']}</td></tr>"
        f"<tr><td>Work Type</td><td>{d['wtype']} — {wtype_label}</td></tr>"
        f"<tr><td>Contingência</td><td>{d['cont']*100:.0f}%</td></tr>"
        f"<tr><td>Billing</td><td>{billing_label}</td></tr>"
        "</table>"
    )

    # ── Misc items ──
    misc_html = ""
    if d["misc_items"]:
        misc_html = "<table><tr><th>Descrição</th><th>Qtd</th><th>Valor Unit.</th><th>Total</th></tr>"
        for it in d["misc_items"]:
            misc_html += (
                f"<tr><td>{it.descricao}</td><td>{it.quantidade}</td>"
                f"<td>R$ {it.valor_unitario:,.0f}</td><td>R$ {it.total:,.0f}</td></tr>"
            )
        misc_html += (
            f'<tr style="font-weight:700;border-top:2px solid #161616">'
            f"<td colspan='3'>TOTAL</td><td>R$ {d['misc_total']:,.0f}</td></tr></table>"
        )

    # ── Proposal items ──
    proposal_html = ""
    for i, item in enumerate(d["proposal_items"], 1):
        proposal_html += f"<h3>Oportunidade {i}: {item.get('opportunity', '')}</h3>"
        proposal_html += f"<p><b>Objetivo:</b> {item.get('objective', '')}</p>"
        proposal_html += f"<p><b>Solução:</b> {item.get('solution', '')}</p>"

    # ── Final HTML ──
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'IBM Plex Sans', sans-serif; color: #161616; margin: 0; padding: 0; }}

    .cover {{
        background: linear-gradient(135deg, #0f62fe 0%, #0043ce 100%);
        color: white; padding: 60px 48px; min-height: 280px;
        display: flex; flex-direction: column; justify-content: flex-end;
    }}
    .cover h1 {{ font-size: 32pt; font-weight: 700; margin-bottom: 8px; }}
    .cover .subtitle {{ font-size: 14pt; opacity: 0.85; }}
    .cover .meta {{ font-size: 10pt; opacity: 0.7; margin-top: 20px; }}

    .content {{ padding: 32px 48px; }}
    h2 {{
        color: #0f62fe; font-size: 14pt; font-weight: 700;
        border-bottom: 2px solid #0f62fe; padding-bottom: 4px;
        margin: 28px 0 12px 0;
    }}
    h3 {{ color: #161616; font-size: 12pt; margin: 12px 0 6px 0; }}
    p, li {{ font-size: 10pt; line-height: 1.6; color: #393939; }}
    ul {{ padding-left: 20px; }}

    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 9pt; }}
    th {{ background: #e0e0e0; color: #161616; padding: 8px 10px; text-align: left; font-weight: 600; }}
    td {{ padding: 7px 10px; border-bottom: 1px solid #e0e0e0; }}
    tr:nth-child(even) {{ background: #f9f9f9; }}

    table.params {{ width: auto; }}
    table.params td:first-child {{ font-weight: 600; color: #525252; padding-right: 24px; }}
    table.params td {{ border-bottom: 1px solid #f0f0f0; }}

    .footer {{
        text-align: center; font-size: 8pt; color: #a8a8a8;
        padding: 20px 48px; border-top: 1px solid #e0e0e0; margin-top: 32px;
    }}
    @media print {{
        .cover {{ page-break-after: always; }}
        h2 {{ page-break-after: avoid; }}
        table {{ page-break-inside: avoid; }}
    }}
</style>
</head>
<body>

<!-- Cover page -->
<div class="cover">
    <div class="subtitle">IBM Consulting</div>
    <h1>Proposta Técnica e Comercial</h1>
    <div class="subtitle">{d['tipo_contrato']}</div>
    <div class="meta">Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} &bull; Confidencial</div>
</div>

<div class="content">

<h2>1. Oportunidades e Soluções</h2>
{proposal_html if proposal_html else f"<p>{d['diagnostico'].replace(chr(10), '<br>')}</p>"}

<h2>2. Objetivos</h2>
<p>{d['objetivos'].replace(chr(10), '<br>')}</p>

<h2>3. Solução Técnica</h2>
<p>{d['solucao'].replace(chr(10), '<br>')}</p>

<h2>4. Parâmetros do Projeto</h2>
{params_html}

<h2>5. Resumo Financeiro</h2>
{kpi_html}
{group_table}

{"<h2>6. Despesas Adicionais (Miscellaneous)</h2>" + misc_html if misc_html else ""}

<h2>{"7" if misc_html else "6"}. Preliminary P&amp;L</h2>
{pnl_table}

<h2>{"8" if misc_html else "7"}. Premissas e Limitações</h2>
{_md.markdown(d['premissas']) if d['premissas'] else '<p>—</p>'}

</div>

<div class="footer">
    CostWise AI &bull; Este documento é confidencial e de uso exclusivo IBM
</div>

</body>
</html>"""
    return html


def gerar_pdf():
    if not _HAS_WEASYPRINT:
        return None
    html_content = gerar_html_proposta()
    nome_arquivo = f"proposta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    caminho = os.path.join(SALVAMENTO_DIR, nome_arquivo)
    _WeasyHTML(string=html_content).write_pdf(caminho)
    return caminho


# ── Render UI ─────────────────────────────────────────────────────────────────


def _card(title: str, content: str, icon: str = ""):
    """Render a Carbon-style read-only card."""
    st.markdown(
        f"""<div style="background:#fff;border:1px solid #e0e0e0;border-left:3px solid #0f62fe;
        padding:16px 20px;margin-bottom:12px;border-radius:2px">
        <div style="font-size:0.8rem;font-weight:600;color:#0f62fe;margin-bottom:8px">{icon} {title}</div>
        <div style="font-size:0.88rem;color:#393939;line-height:1.6;white-space:pre-wrap">{content}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def render():
    d = _load_state()
    grupos = d["grupos"]
    markup = d["markup"]
    n_meses = d["n_meses"]

    st.markdown(
        '<h2 style="margin-bottom:0">📋 Resume</h2>'
        '<p style="color:#525252;font-size:0.85rem;margin-top:4px">'
        "Visão consolidada de todos os dados da simulação.</p>",
        unsafe_allow_html=True,
    )

    # ── 1. Proposal ──
    st.markdown("---")
    st.markdown("#### 1 · Proposta")

    tipo = d["tipo_contrato"]
    if tipo:
        st.markdown(
            f'<div style="display:inline-block;background:#0f62fe;color:white;'
            f'padding:4px 14px;border-radius:12px;font-size:0.82rem;font-weight:600">{tipo}</div>',
            unsafe_allow_html=True,
        )

    items = d["proposal_items"]
    if items:
        for i, item in enumerate(items, 1):
            with st.expander(
                f"Oportunidade {i}: {item.get('opportunity', '—')}", expanded=i == 1
            ):
                st.markdown(f"**Objetivo:** {item.get('objective', '—')}")
                st.markdown(f"**Solução:** {item.get('solution', '—')}")
    else:
        cols = st.columns(3)
        if d["diagnostico"]:
            with cols[0]:
                _card("Diagnóstico", d["diagnostico"], "🔍")
        if d["objetivos"]:
            with cols[1]:
                _card("Objetivos", d["objetivos"], "🎯")
        if d["solucao"]:
            with cols[2]:
                _card("Solução Técnica", d["solucao"], "💡")

    # ── 2. KPI Bar ──
    if grupos:
        summary = calcular_summary(
            grupos,
            markup,
            n_meses,
            contingencia=d["cont"],
            misc_total=d["misc_total"],
            **d["billing_kw"],
        )
        pnl = calcular_pnl(
            grupos,
            markup,
            n_meses,
            contingencia=d["cont"],
            misc_total=d["misc_total"],
            **d["billing_kw"],
        )
        has_data = summary.get("total_horas", 0) > 0
    else:
        summary = {}
        pnl = {}
        has_data = False

    if has_data:
        st.markdown("---")
        st.markdown("#### 2 · Resumo Financeiro")

        npv_val = summary["npv_gp"] * 100
        npv_ok = summary["npv_gp_ok"]
        npv_color = "#24a148" if npv_ok else "#da1e28"
        npv_icon = "✓" if npv_ok else "✗"

        kpi_items = [
            (f"R$ {summary['total_tcv']:,.0f}", "TCV", "#161616"),
            (f"{npv_val:.2f}% {npv_icon}", "NPV GP%", npv_color),
            (f"{summary['markup']:.2f}x", "Markup", "#161616"),
            (f"{summary['markup_min']:.4f}x", "Markup mínimo", "#161616"),
            (f"R$ {summary['taxa_hora']:,.0f}/h", "Taxa/hora", "#161616"),
            (f"{n_meses} meses", "Duração", "#161616"),
        ]
        kpi_html = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin:8px 0">'
        for val, label, color in kpi_items:
            border = (
                f"border-left:3px solid {npv_color}"
                if label == "NPV GP%"
                else "border-left:3px solid #e0e0e0"
            )
            kpi_html += (
                f'<div style="flex:1;min-width:130px;background:#fff;{border};'
                f'padding:14px 16px;border:1px solid #e0e0e0;border-radius:2px">'
                f'<div style="font-size:1.2rem;font-weight:700;color:{color}">{val}</div>'
                f'<div style="font-size:0.75rem;color:#525252;margin-top:2px">{label}</div></div>'
            )
        kpi_html += "</div>"
        st.markdown(kpi_html, unsafe_allow_html=True)

        # ── Group table ──
        grupo_rows = summary_por_grupo(
            grupos, markup, n_meses, misc_total=d["misc_total"]
        )
        if grupo_rows:
            html_table = (
                '<table style="width:100%;border-collapse:collapse;font-size:0.82rem;margin-top:12px">'
                '<tr style="background:#e0e0e0">'
                '<th style="padding:8px;text-align:left">Grupo</th>'
                '<th style="padding:8px;text-align:right">Horas</th>'
                '<th style="padding:8px;text-align:right">Base Cost</th>'
                '<th style="padding:8px;text-align:right">Base %</th>'
                '<th style="padding:8px;text-align:right">TCV</th>'
                '<th style="padding:8px;text-align:right">Markup</th>'
                '<th style="padding:8px;text-align:right">Taxa/h</th></tr>'
            )
            for r in grupo_rows:
                html_table += (
                    f'<tr style="border-bottom:1px solid #e0e0e0">'
                    f'<td style="padding:7px 8px">{r["grupo"]}</td>'
                    f'<td style="padding:7px 8px;text-align:right">{r["horas"]:,.0f} h</td>'
                    f'<td style="padding:7px 8px;text-align:right">R$ {r["base_cost"]:,.0f}</td>'
                    f'<td style="padding:7px 8px;text-align:right">{r["base_pct"]*100:.1f}%</td>'
                    f'<td style="padding:7px 8px;text-align:right">R$ {r["tcv"]:,.0f}</td>'
                    f'<td style="padding:7px 8px;text-align:right">{r["markup"]:.2f}x</td>'
                    f'<td style="padding:7px 8px;text-align:right">R$ {r["taxa_hora"]:,.0f}</td></tr>'
                )
            html_table += (
                f'<tr style="font-weight:700;border-top:2px solid #161616">'
                f'<td style="padding:8px">TOTAL</td>'
                f'<td style="padding:8px;text-align:right">{summary["total_horas"]:,.0f} h</td>'
                f'<td style="padding:8px;text-align:right">R$ {summary["total_base_cost"]:,.0f}</td>'
                f'<td style="padding:8px;text-align:right">100%</td>'
                f'<td style="padding:8px;text-align:right">R$ {summary["total_tcv"]:,.0f}</td>'
                f'<td style="padding:8px;text-align:right">{summary["markup"]:.2f}x</td>'
                f'<td style="padding:8px;text-align:right">R$ {summary["taxa_hora"]:,.0f}</td></tr>'
            )
            html_table += "</table>"
            st.markdown(html_table, unsafe_allow_html=True)

        # ── P&L Summary ──
        st.markdown("---")
        st.markdown("#### 3 · Preliminary P&L")

        pnl_rows = [
            ("TCV (com impostos)", f"R$ {pnl['tcv']:,.0f}", "", False),
            (
                "Sales Taxes (ISS + PIS/COFINS)",
                f"(R$ {pnl['tcv'] - pnl['net_price']:,.0f})",
                f"{pnl['sales_taxes_pct']*100:.2f}%",
                False,
            ),
            ("Net Price / Revenue", f"R$ {pnl['revenue']:,.0f}", "", False),
            ("Base Cost", f"R$ {pnl['base_cost']:,.0f}", "", False),
            (
                "Risk & Contingency",
                f"R$ {pnl['risk_contingency']:,.0f}",
                f"{pnl['risk_contingency_pct']*100:.1f}%",
                False,
            ),
            ("Total Cost", f"R$ {pnl['total_cost']:,.0f}", "", False),
            (
                "Nominal GP",
                f"R$ {pnl['nominal_gp']:,.0f}",
                f"{pnl['nominal_gp_pct']*100:.2f}%",
                True,
            ),
            (
                "Rev. Apportionment (19.5%)",
                f"(R$ {pnl['rev_apportionment']:,.0f})",
                "",
                False,
            ),
            (
                "Nominal PTI",
                f"R$ {pnl['nominal_pti']:,.0f}",
                f"{pnl['nominal_pti_pct']*100:.2f}%",
                False,
            ),
            (
                "NPV GP",
                f"R$ {pnl['npv_gp']:,.0f}",
                f"{pnl['npv_gp_pct']*100:.2f}%",
                True,
            ),
            (
                "NPV PTI",
                f"R$ {pnl['npv_pti']:,.0f}",
                f"{pnl['npv_pti_pct']*100:.2f}%",
                False,
            ),
            (
                "Contract GP (excl. Contingency)",
                f"R$ {pnl['contract_gp']:,.0f}",
                f"{pnl['contract_gp_pct']*100:.2f}%",
                True,
            ),
        ]
        pnl_html = (
            '<table style="width:100%;max-width:700px;border-collapse:collapse;font-size:0.82rem">'
            '<tr style="background:#e0e0e0">'
            '<th style="padding:8px;text-align:left;width:55%">Item</th>'
            '<th style="padding:8px;text-align:right">Valor</th>'
            '<th style="padding:8px;text-align:right">%</th></tr>'
        )
        for label, val, pct, hl in pnl_rows:
            bg = "background:#fff3cd;" if hl else ""
            fw = "font-weight:700;" if hl else ""
            pnl_html += (
                f'<tr style="{bg}border-bottom:1px solid #e0e0e0">'
                f'<td style="padding:7px 8px;{fw}">{label}</td>'
                f'<td style="padding:7px 8px;text-align:right;{fw}">{val}</td>'
                f'<td style="padding:7px 8px;text-align:right;{fw}">{pct}</td></tr>'
            )
        pnl_html += "</table>"
        st.markdown(pnl_html, unsafe_allow_html=True)

    else:
        st.markdown("---")
        st.info("Sem dados financeiros. Configure o Cost Estimator primeiro.")

    # ── 4. Parameters ──
    st.markdown("---")
    st.markdown("#### 4 · Parâmetros do Projeto")

    billing_label = BILLING_MODES.get(
        d["billing_kw"]["billing_mode"], "Proporcional ao Custo"
    )
    wtype_label = WORK_TYPES.get(d["wtype"], d["wtype"])

    p1, p2 = st.columns(2)
    with p1:
        params_left = [
            ("Duração", f"{n_meses} meses"),
            ("Markup", f"{markup:.2f}x"),
            ("Horas/mês", f"{d['horas_mes']:.0f}"),
            ("WACC", f"{d['wacc_pct']:.1f}%"),
            ("Payment Terms", f"{d['payment_terms']} dias"),
        ]
        html_l = '<table style="font-size:0.82rem;border-collapse:collapse">'
        for label, val in params_left:
            html_l += (
                f'<tr style="border-bottom:1px solid #f0f0f0">'
                f'<td style="padding:6px 16px 6px 0;font-weight:600;color:#525252">{label}</td>'
                f'<td style="padding:6px 0">{val}</td></tr>'
            )
        html_l += "</table>"
        st.markdown(html_l, unsafe_allow_html=True)

    with p2:
        params_right = [
            ("Câmbio USD/BRL", f"{d['exch_rate']:.5f}"),
            ("Risk Profile", d["risk"]),
            ("Work Type", f"{d['wtype']} — {wtype_label}"),
            ("Contingência", f"{d['cont']*100:.0f}%"),
            ("Billing", billing_label),
        ]
        html_r = '<table style="font-size:0.82rem;border-collapse:collapse">'
        for label, val in params_right:
            html_r += (
                f'<tr style="border-bottom:1px solid #f0f0f0">'
                f'<td style="padding:6px 16px 6px 0;font-weight:600;color:#525252">{label}</td>'
                f'<td style="padding:6px 0">{val}</td></tr>'
            )
        html_r += "</table>"
        st.markdown(html_r, unsafe_allow_html=True)

    # ── 5. Misc items ──
    if d["misc_items"]:
        st.markdown("---")
        st.markdown("#### 5 · Despesas Adicionais")
        misc_html = (
            '<table style="width:100%;max-width:600px;border-collapse:collapse;font-size:0.82rem">'
            '<tr style="background:#e0e0e0">'
            '<th style="padding:8px;text-align:left">Descrição</th>'
            '<th style="padding:8px;text-align:right">Qtd</th>'
            '<th style="padding:8px;text-align:right">Valor Unit.</th>'
            '<th style="padding:8px;text-align:right">Total</th></tr>'
        )
        for it in d["misc_items"]:
            misc_html += (
                f'<tr style="border-bottom:1px solid #e0e0e0">'
                f'<td style="padding:7px 8px">{it.descricao}</td>'
                f'<td style="padding:7px 8px;text-align:right">{it.quantidade}</td>'
                f'<td style="padding:7px 8px;text-align:right">R$ {it.valor_unitario:,.0f}</td>'
                f'<td style="padding:7px 8px;text-align:right">R$ {it.total:,.0f}</td></tr>'
            )
        misc_html += (
            f'<tr style="font-weight:700;border-top:2px solid #161616">'
            f'<td style="padding:8px" colspan="3">TOTAL</td>'
            f'<td style="padding:8px;text-align:right">R$ {d["misc_total"]:,.0f}</td></tr></table>'
        )
        st.markdown(misc_html, unsafe_allow_html=True)
        next_section = 6
    else:
        next_section = 5

    # ── 6. Premissas ──
    if d["premissas"]:
        st.markdown("---")
        st.markdown(f"#### {next_section} · Premissas e Limitações")
        st.markdown(d["premissas"])

    # ── Actions ──
    st.markdown("---")
    st.markdown(
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">'
        '<span style="font-size:1.1rem;font-weight:700">⚡ Ações</span></div>',
        unsafe_allow_html=True,
    )

    act1, act2, act3 = st.columns(3)

    # Save JSON
    with act1:
        if st.button("💾 Salvar Simulação", use_container_width=True):
            file_name = f"simulacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_data = json.dumps(dict(st.session_state), indent=2, default=str)
            file_path = os.path.join(SALVAMENTO_DIR, file_name)
            with open(file_path, "w") as f:
                f.write(json_data)
            st.success(f"Salvo: {file_name}")
            with open(file_path, "rb") as fp:
                st.download_button(
                    "⬇ Download JSON",
                    data=fp,
                    file_name=file_name,
                    mime="application/json",
                    use_container_width=True,
                )

    # Export PDF
    with act2:
        if not _HAS_WEASYPRINT:
            st.button(
                "📄 Exportar PDF",
                use_container_width=True,
                disabled=True,
                help="WeasyPrint não está instalado neste ambiente",
            )
        elif st.button("📄 Exportar PDF", use_container_width=True):
            with st.spinner("Gerando PDF..."):
                caminho_pdf = gerar_pdf()
                if caminho_pdf:
                    with open(caminho_pdf, "rb") as fp:
                        st.download_button(
                            "⬇ Download PDF",
                            data=fp,
                            file_name=os.path.basename(caminho_pdf),
                            mime="application/pdf",
                            use_container_width=True,
                        )

    # Load JSON
    with act3:
        uploaded = st.file_uploader(
            "📂 Carregar simulação (.json)", type=["json"], label_visibility="collapsed"
        )
        if uploaded:
            data = json.load(uploaded)
            for key, value in data.items():
                st.session_state[key] = value
            st.success("Simulação carregada! Recarregue a página.")
            st.rerun()
