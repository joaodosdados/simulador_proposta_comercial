"""
Etapa 3 – Premissas e Limitações
Usa oportunidades/objetivos/soluções da Proposta + dados do Cost Estimator
para gerar premissas, limitações e riscos com IA.
"""

import streamlit as st
from utils.llm import gerar_resposta_watsonx


# ── Helpers ───────────────────────────────────────────────────────────────────
def _build_context() -> str:
    """Monta o contexto a partir de proposal_items + Cost Estimator."""
    parts: list[str] = []

    # --- Itens da proposta ---
    items = st.session_state.get("proposal_items", [])
    if items:
        for i, it in enumerate(items, 1):
            parts.append(f"### Oportunidade {i}")
            parts.append(f"Descrição: {it.get('opportunity', 'N/D')}")
            parts.append(f"Objetivo SMART:\n{it.get('objective', 'N/D')}")
            parts.append(f"Solução Técnica:\n{it.get('solution', 'N/D')}")
            parts.append("")
    else:
        # Fallback: campos legados
        obj = st.session_state.get("objetivos", "")
        sol = st.session_state.get("solucao_tecnica", "")
        if obj:
            parts.append(f"Objetivos:\n{obj}")
        if sol:
            parts.append(f"Solução Técnica:\n{sol}")

    # --- Prazo do projeto ---
    n_meses = st.session_state.get("n_meses", 12)
    tipo = st.session_state.get("tipo_contrato", "")

    fin_lines: list[str] = []
    if n_meses:
        fin_lines.append(f"- Duracao do projeto: {n_meses} meses")
    if tipo:
        fin_lines.append(f"- Modelo comercial: {tipo}")

    if fin_lines:
        parts.append("### Dados do Projeto")
        parts.extend(fin_lines)

    return "\n".join(parts)


def _build_prompt(contexto: str) -> str:
    return (
        "Voce e um consultor senior IBM especializado em propostas tecnicas de "
        "Data Science, IA e engenharia de software.\n"
        "Com base EXCLUSIVAMENTE no contexto abaixo, gere um documento de Premissas e Limitacoes "
        "para a proposta comercial.\n\n"
        "TODA A SAIDA DEVE SER EM PORTUGUES FORMAL DO BRASIL.\n\n"
        "=== REGRAS CRITICAS ===\n"
        "- NAO mencione profissionais, cargos, bandas ou tamanho de equipe\n"
        "- NAO invente custos, valores monetarios ou metricas nao fornecidos\n"
        "- Foque em premissas tecnicas, de escopo, riscos e compliance\n"
        "==================\n\n"
        "O documento deve conter as seguintes secoes:\n\n"
        "**1. Premissas Operacionais**\n"
        "- Acesso a dados, sistemas, ambientes e infraestrutura\n"
        "- Disponibilidade de stakeholders e ponto focal do cliente\n"
        "- Qualidade e formato dos dados disponiveis\n"
        "- Permissoes e credenciais necessarias\n\n"
        "**2. Premissas de Escopo**\n"
        "- O que esta incluido e o que NAO esta incluido no escopo\n"
        "- Integracoes previstas vs. integracoes fora do escopo\n"
        "- Criterios de aceitacao das entregas\n"
        "- Change requests: processo e impacto em prazo/custo\n\n"
        "**3. Limitacoes Tecnicas**\n"
        "- Restricoes de sistemas legados, versoes de software, dependencias\n"
        "- Limitacoes de performance, volumetria e escalabilidade\n"
        "- Dependencias externas (APIs, fornecedores, licencas)\n\n"
        "**4. Riscos e Salvaguardas**\n"
        "- Riscos identificados com probabilidade e impacto\n"
        "- Planos de mitigacao para cada risco\n"
        "- Clausulas contratuais recomendadas (SLA, penalidades, limites de responsabilidade)\n\n"
        "**5. Compliance e Protecao de Dados**\n"
        "- Requisitos LGPD aplicaveis ao projeto\n"
        "- Tratamento de dados pessoais e sensiveis\n"
        "- Recomendacoes de anonimizacao/pseudonimizacao\n"
        "- Necessidade de DPO ou DPIA\n\n"
        "**6. Premissas de Prazo**\n"
        "- Cronograma baseado na duracao prevista\n"
        "- Riscos de atraso e dependencias entre atividades\n"
        "- Condicoes para cumprimento dos marcos\n\n"
        "Regras adicionais:\n"
        "- Seja especifico ao projeto descrito\n"
        "- Considere as tecnologias mencionadas na solucao tecnica\n"
        "- Use bullet points (- ) para cada item\n"
        "- Retorne texto formatado em Markdown\n"
        "- NAO mencione nomes de cargos ou profissionais (ex: Data Scientist, Engenheiro, PM)\n"
        "- NAO mencione valores monetarios (ex: R$, custos, orcamento, economia)\n"
        "- Ignore qualquer mencao a equipe, cargos ou valores que aparecar no contexto\n"
        "- Foque SOMENTE em premissas tecnicas, de escopo, riscos, compliance e prazo\n\n"
        f"Contexto do Projeto:\n{contexto}"
    )


# ── Renderiza resumo do contexto usado ────────────────────────────────────────
def _render_context_summary():
    items = st.session_state.get("proposal_items", [])
    n_meses = st.session_state.get("n_meses", 12)

    cols = st.columns(2)
    with cols[0]:
        n_opp = len(items) if items else 0
        st.metric("Oportunidades", n_opp)
    with cols[1]:
        st.metric("Duracao", f"{n_meses} meses")

    if not items and not st.session_state.get("objetivos"):
        st.warning(
            "Nenhuma oportunidade definida na etapa de Proposta. "
            "Volte a etapa anterior para gerar oportunidades com IA."
        )


# ── Render principal ──────────────────────────────────────────────────────────
def render():
    st.subheader("Premissas e Limitações")
    st.caption(
        "Gere premissas, limitações e riscos baseados na proposta e no Cost Estimator"
    )

    _render_context_summary()

    st.divider()

    # Botão de geração
    if st.button("Gerar Premissas e Limitações com IA", key="btn_gerar_premissas"):
        contexto = _build_context()
        if not contexto.strip():
            st.error(
                "Sem dados disponíveis. Preencha a Proposta e/ou o Cost Estimator primeiro."
            )
            return

        with st.spinner("Gerando premissas e limitações..."):
            prompt = _build_prompt(contexto)
            resultado = gerar_resposta_watsonx(prompt, temperature=0.1, max_tokens=3000)
            if resultado:
                st.session_state.premissas_limitacoes = resultado
                st.session_state._premissas_contexto = contexto
                st.success("Premissas e limitações geradas com sucesso!")
                st.rerun()
            else:
                st.error("Falha ao gerar texto com IA.")

    # Debug: mostra contexto enviado para a IA
    ctx_debug = st.session_state.get("_premissas_contexto", "")
    if ctx_debug:
        with st.expander("Contexto enviado para a IA", expanded=False):
            st.code(ctx_debug, language=None)

    # Resultado
    texto_atual = st.session_state.get("premissas_limitacoes", "")

    if texto_atual:
        with st.expander("Copiar texto (clique no icone de copiar)", expanded=False):
            st.code(texto_atual, language=None)

        with st.expander("Visualizacao formatada", expanded=True):
            st.markdown(texto_atual)
