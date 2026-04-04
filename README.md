# CostWise AI

Simulador interativo de propostas comerciais e estimativas de custo para projetos de consultoria. Construído com [Streamlit](https://streamlit.io/) e IBM Watsonx AI.

---

## Funcionalidades

- **Proposal** — Análise de oportunidades com IA (Watsonx), geração de diagnóstico, objetivos e soluções
- **Cost Estimator** — Staffing plan por banda, markup, NPV GP%, P&L, billing schedule, contingência, misc items
- **Premissas e Limitações** — Geração automática com IA baseada no contexto do projeto
- **Resume** — Visão consolidada com KPI cards, tabelas e exportação (JSON/PDF)

### Motor financeiro
- Cálculo de NPV GP% com desconto WACC mensal
- Markup mínimo automático (busca binária)
- 3 modos de billing schedule (proporcional, igualitário, customizado)
- Tabela de contingência Risk Profile × Work Type
- Preliminary P&L completo (Nominal GP, PTI, Rev. Apportionment, Contract GP)

---

## Stack

- Python 3.12+
- Streamlit + streamlit-option-menu
- IBM Watsonx AI (Mistral Small)
- WeasyPrint (PDF)
- Pandas

---

## Setup

### 1. Clone

```bash
git clone https://github.com/joaodosdados/simulador_proposta_comercial.git
cd simulador_proposta_comercial
```

### 2. Ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
```

### 3. Dependências

```bash
pip install -r requirements.txt
```

### 4. Configuração

Copie os templates e preencha com seus valores:

```bash
cp config.example.json config.json   # Taxas, WACC, contingência, etc.
cp .env.example .env                 # API keys do Watsonx
```

**`config.json`** — Constantes financeiras (taxas por banda, WACC, contingência, NPV mínimo, etc.)

**`.env`** — Credenciais:
```
IBM_KEY=sua_chave_watsonx
PROJECT_ID=seu_project_id
```

### 5. WeasyPrint (opcional, para PDF)

| OS | Comando |
|----|---------|
| macOS | `brew install cairo pango gdk-pixbuf libffi` |
| Ubuntu | `sudo apt-get install libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev` |

### 6. Executar

```bash
streamlit run app.py
```

---

## Estrutura

```
├── app.py                    # Entry point
├── config.json               # Dados sensíveis (gitignored)
├── config.example.json       # Template de configuração
├── .env                      # API keys (gitignored)
├── etapas/
│   ├── etapa_proposta.py     # Proposal com IA
│   ├── etapa_financeiro.py   # Cost Estimator
│   ├── restricoes.py         # Premissas e Limitações
│   └── encerramento.py       # Resume + PDF
├── utils/
│   ├── calculos.py           # Motor financeiro
│   ├── llm.py                # Integração Watsonx/Ollama
│   ├── navigation.py         # Sidebar
│   └── benchmark_loader.py   # Loader de benchmarks
└── static/css/               # Carbon Design theme
```

---

## Autor

**João Lucas dos Santos Oliveira**
Data Scientist | AI Engineer
[GitHub](https://github.com/joaodosdados) · [LinkedIn](https://linkedin.com/in/joaodosdados)

---

## Licença

MIT — veja [LICENSE](LICENSE).
