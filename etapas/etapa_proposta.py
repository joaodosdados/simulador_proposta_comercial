"""
Etapa 1 – Proposta
Unifica: informações do projeto, diagnóstico com IA, e itens de proposta
(oportunidade + objetivo SMART + solução técnica) como unidades atômicas.
"""

import json
import streamlit as st
from utils.benchmark_loader import carregar_benchmark
from utils.llm import gerar_resposta_watsonx
from PyPDF2 import PdfReader
import docx


# ── Helpers ───────────────────────────────────────────────────────────────────
def _extract_text(uploaded_file) -> str | None:
    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if (
        uploaded_file.type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        doc = docx.Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs)
    return None


def _items() -> list[dict]:
    """Retorna a lista de itens de proposta do session_state."""
    if "proposal_items" not in st.session_state:
        st.session_state.proposal_items = []
    return st.session_state.proposal_items


def _fix_newlines(val: str) -> str:
    """Converte \\n literal em quebra de linha real."""
    if not val:
        return val
    # Substitui \\n literal (que o JSON não converteu) em newline real
    return val.replace("\\n", "\n")


def _parse_ai_response(text: str) -> list[dict]:
    """Tenta extrair lista JSON da resposta da IA, mesmo com lixo ao redor."""
    if not text:
        return []

    cleaned = text.strip()

    # Remove blocos markdown ```json ... ```
    if "```" in cleaned:
        import re

        m = re.search(r"```(?:json)?\s*(\[.*?])\s*```", cleaned, re.DOTALL)
        if m:
            cleaned = m.group(1)

    # Tenta localizar o array JSON na string (pode vir com texto antes/depois)
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]

    try:
        items = json.loads(cleaned)
        if isinstance(items, list):
            return [
                {
                    "opportunity": _fix_newlines(it.get("opportunity", "")),
                    "objective": _fix_newlines(it.get("objective", "")),
                    "solution": _fix_newlines(it.get("solution", "")),
                }
                for it in items
                if isinstance(it, dict)
            ]
    except (json.JSONDecodeError, ValueError):
        pass
    return []


# ── Seção: Info do projeto ────────────────────────────────────────────────────
def _render_info():
    st.selectbox(
        "Modelo Comercial",
        [
            "Projeto — Escopo fixo com entregas e cronograma definidos",
            "Serviços — Manutenção, suporte e atualizações contínuas",
            "Parceria — Desenvolvimento conjunto de longo prazo, riscos e benefícios compartilhados",
        ],
        key="tipo_contrato",
    )


# ── Seção: Input de contexto ─────────────────────────────────────────────────
def _render_input():
    st.markdown("##### Contexto")
    st.caption("Forneça o contexto do cliente para análise com IA")

    tab_manual, tab_upload = st.tabs(["Texto", "Upload de arquivo"])

    with tab_manual:
        manual_text = st.text_area(
            "Digite ou cole o conteúdo para análise:",
            value=st.session_state.get("texto_extraido", carregar_benchmark("cemig")),
            height=220,
            label_visibility="collapsed",
        )
        if manual_text != st.session_state.get("texto_extraido", ""):
            st.session_state.texto_extraido = manual_text

    with tab_upload:
        uploaded = st.file_uploader(
            "Selecione um arquivo (TXT, PDF ou DOCX):",
            type=["txt", "pdf", "docx"],
            label_visibility="collapsed",
        )
        if uploaded:
            texto = _extract_text(uploaded)
            if texto:
                st.session_state.texto_extraido = texto
                with st.expander("Pré-visualização", expanded=False):
                    st.text_area(
                        "Conteúdo",
                        value=texto,
                        height=180,
                        disabled=True,
                        label_visibility="collapsed",
                    )
            else:
                st.warning("Não foi possível extrair texto deste arquivo")

    # Botão único que gera tudo
    if st.button("Analisar e Gerar Oportunidades", key="btn_generate"):
        texto = st.session_state.get("texto_extraido", "").strip()
        if not texto:
            st.error("Insira um texto ou faça upload de um arquivo")
            return

        with st.spinner("Analisando contexto e gerando oportunidades..."):
            prompt = (
                "Você é um arquiteto de soluções IBM sênior, com profundo conhecimento técnico em "
                "Data Science, IA, MLOps e engenharia de software.\n"
                "Analise o conteúdo abaixo e produza um array JSON de oportunidades de projeto.\n"
                "TODA A SAÍDA DEVE SER EM PORTUGUÊS FORMAL DO BRASIL.\n\n"
                "Cada item deve ter exatamente 3 campos:\n\n"
                '═══ "opportunity" (máx 200 caracteres) ═══\n'
                "Descrição em uma linha da oportunidade: área de aplicação + impacto esperado.\n\n"
                '═══ "objective" (objetivo SMART com bullet points, use \\n para quebras) ═══\n'
                "Formato obrigatório:\n"
                "- S (Específico): O que será feito, escopo, beneficiários diretos\\n"
                "- M (Mensurável): KPIs concretos, metas numéricas, marcos de acompanhamento\\n"
                "- A (Alcançável): Recursos necessários, competências, por que é viável\\n"
                "- R (Relevante): Justificativa de negócio, ROI estimado, alinhamento estratégico\\n"
                "- T (Temporal): Cronograma com marcos intermediários e prazo final\n\n"
                '═══ "solution" (solução técnica DETALHADA com bullet points, use \\n) ═══\n'
                "A solução técnica deve ser ESPECÍFICA e IMPLEMENTÁVEL, não genérica.\n"
                "Para cada oportunidade, selecione as tecnologias MAIS ADEQUADAS ao problema.\n"
                "NÃO repita a mesma stack para todas as oportunidades — cada problema exige ferramentas diferentes.\n\n"
                "Formato obrigatório:\n"
                "- Arquitetura: descreva a arquitetura da solução (componentes, fluxo de dados, integrações)\\n"
                "- IBM: ferramentas IBM específicas para o caso — Watson Assistant para chatbots, "
                "watsonx.ai para LLMs/foundation models, watsonx.data para lakehouse, "
                "Cloud Pak for Data para MLOps, Watson Discovery para busca semântica, "
                "Instana para observabilidade, etc.\\n"
                "- Open-source: frameworks e libs específicas ao problema:\n"
                "  * NLP/Agentes: LangChain, LangGraph, LlamaIndex, Hugging Face Transformers, spaCy\n"
                "  * ML/Deep Learning: Scikit-learn, XGBoost, LightGBM, PyTorch, TensorFlow\n"
                "  * Dados: PySpark, Pandas, dbt, Great Expectations\n"
                "  * Orquestração: Airflow, Prefect, Dagster\n"
                "  * MLOps: MLflow, DVC, Weights & Biases\n"
                "  * Mensageria/Streaming: Kafka, RabbitMQ, Redis Streams\n"
                "  * APIs/Canais: FastAPI, WhatsApp Business API, Twilio\n"
                "  * Vetores/Busca: Elasticsearch, Milvus, ChromaDB, Pinecone\n"
                "  * Infra: Docker, Kubernetes, Terraform\\n"
                "- Cloud: se o conteúdo mencionar Azure/AWS/GCP, inclua serviços nativos "
                "(Azure OpenAI, Amazon Bedrock, Vertex AI, etc.)\\n"
                "- Etapas: 4 etapas de implementação concretas e sequenciais\n\n"
                "Regras:\n"
                "- Identifique APENAS oportunidades explicitamente presentes no conteúdo\n"
                "- NÃO invente dados, métricas ou números não mencionados\n"
                "- A solução técnica deve ser realista e implementável, não uma lista genérica de buzzwords\n"
                "- Escolha ferramentas que façam sentido para o problema específico\n"
                "- NÃO inclua a linguagem R\n"
                "- Retorne APENAS um array JSON válido, sem markdown, sem texto antes ou depois\n"
                "- Use \\n dentro dos valores JSON para bullet points\n\n"
                f"Conteúdo:\n{texto}"
            )
            response = gerar_resposta_watsonx(prompt, temperature=0.4, max_tokens=4000)
            if response:
                items = _parse_ai_response(response)
                if items:
                    st.session_state.proposal_items = items
                    _sync_legacy_fields()
                    st.success(f"{len(items)} oportunidades geradas")
                    st.rerun()
                else:
                    st.error("Não foi possível interpretar a resposta da IA como JSON.")
                    st.session_state["_raw_ai_response"] = response
            else:
                st.error("Sem resposta do modelo de IA")


# ── Renderiza um item de proposta ─────────────────────────────────────────────
def _auto_height(text: str, min_h: int = 68, chars_per_line: int = 100) -> int:
    """Calcula altura do text_area com base no conteúdo."""
    if not text:
        return min_h
    lines = text.count("\n") + 1
    wrapped_lines = sum(
        max(1, (len(line) // chars_per_line) + 1) for line in text.split("\n")
    )
    return max(min_h, wrapped_lines * 24 + 20)


def _render_item(idx: int, item: dict):
    items = _items()
    with st.container(border=True):
        col_title, col_del = st.columns([6, 1])
        with col_title:
            st.markdown(f"**Oportunidade {idx + 1}**")
        with col_del:
            if st.button("Remover", key=f"rm_{idx}", width="stretch"):
                items.pop(idx)
                _sync_legacy_fields()
                st.rerun()

        opp_val = item.get("opportunity", "")
        obj_val = item.get("objective", "")
        sol_val = item.get("solution", "")

        opp = st.text_area(
            "Oportunidade",
            value=opp_val,
            height=_auto_height(opp_val),
            key=f"opp_{idx}",
        )
        obj = st.text_area(
            "Objetivo SMART",
            value=obj_val,
            height=_auto_height(obj_val),
            key=f"obj_{idx}",
        )
        sol = st.text_area(
            "Solução Técnica",
            value=sol_val,
            height=_auto_height(sol_val),
            key=f"sol_{idx}",
        )

        # Salva edições inline
        item["opportunity"] = opp
        item["objective"] = obj
        item["solution"] = sol


def _sync_legacy_fields():
    """Sincroniza campos usados por outras etapas (encerramento, etc.)."""
    items = _items()
    st.session_state.resultado_diagnostico = "\n".join(
        f"- {it['opportunity']}" for it in items
    )
    st.session_state.objetivos = "\n".join(f"- {it['objective']}" for it in items)
    st.session_state.solucao_tecnica = "\n".join(f"- {it['solution']}" for it in items)


# ── Seção: Itens da proposta ──────────────────────────────────────────────────
def _render_items():
    items = _items()
    if not items:
        return

    st.divider()
    st.markdown(f"##### Oportunidades ({len(items)})")

    for idx, item in enumerate(items):
        _render_item(idx, item)

    # Sincroniza campos legados após renderizar tudo
    _sync_legacy_fields()

    # Botão para adicionar oportunidade manualmente
    if st.button("+ Adicionar oportunidade", key="btn_add_item"):
        items.append({"opportunity": "", "objective": "", "solution": ""})
        st.rerun()


# ── Render principal ──────────────────────────────────────────────────────────
def render():
    st.subheader("Proposta")

    _render_info()
    st.divider()

    # Contexto (esquerda) + Resposta bruta da IA (direita)
    has_raw = bool(st.session_state.get("_raw_ai_response"))
    if has_raw:
        col_ctx, col_raw = st.columns([1, 1])
        with col_ctx:
            _render_input()
        with col_raw:
            st.markdown("##### Resposta bruta da IA")
            st.caption("O parsing JSON falhou — revise ou copie o conteudo")
            st.code(st.session_state["_raw_ai_response"], language="json")
            if st.button("Limpar", key="btn_clear_raw"):
                del st.session_state["_raw_ai_response"]
                st.rerun()
    else:
        _render_input()

    _render_items()
