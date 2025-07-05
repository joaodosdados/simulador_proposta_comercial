# 🧠 Simulador de Propostas Comerciais com Cronograma Inteligente

Este projeto é um simulador interativo desenvolvido em [Streamlit](https://streamlit.io/) para auxiliar na **criação de propostas comerciais técnicas** de projetos de Data Science. O destaque do sistema é a etapa de **cronograma inteligente**, que permite calcular e visualizar a alocação de profissionais, custos e margens de forma flexível e visual.

---

## ✨ Funcionalidades

- ✅ Estrutura passo a passo para construção da proposta
- ✅ Definição de objetivos, diagnóstico e solução técnica
- ✅ Cronograma de alocação por semana com tabela editável
- ✅ Cálculo automático de custos e margens (Fixed-price ou Time & Materials)
- ✅ Visualizações interativas (Gantt e Heatmap de horas)
- ✅ Exportação da proposta em **PDF** ou salvamento em **JSON**
- 🔜 IA generativa para sugestão de cronograma (em desenvolvimento)

---

## 🧩 Tecnologias Utilizadas

- [Python 3.12+](https://www.python.org)
- [Streamlit](https://streamlit.io)
- [FPDF](https://pyfpdf.github.io)
- [Plotly](https://plotly.com/python/)
- [Seaborn + Matplotlib](https://seaborn.pydata.org/)
- [st-aggrid](https://github.com/PablocFonseca/streamlit-aggrid)

---

## 🚀 Como Rodar Localmente

### 1. Clone o repositório

```bash
git clone https://github.com/joaolso/simulador_proposta_comercial.git
cd simulador_proposta_comercial
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate   # Windows
```

### 3. Instale as dependências com uv

```bash
uv sync
```

### 4. Execute a aplicação

```bash
streamlit run app.py
```

---

## 🧑‍💻 Autor

**João Lucas dos Santos Oliveira**  
Data Scientist | AI Engineer  
[GitHub](https://github.com/joaolso) · [LinkedIn](https://linkedin.com/in/joaodosdados)

---

## 🛡️ Licença

Este projeto está sob a licença MIT. Veja o arquivo [`LICENSE`](LICENSE) para mais detalhes.
