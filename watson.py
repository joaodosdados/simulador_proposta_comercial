# watson_test.py

import os
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

supported_models = [
    # Google FLAN
    "google/flan-t5-xl",
    "google/flan-t5-xxl",
    "google/flan-ul2",
    # IBM Granite - instrução geral
    "ibm/granite-3-2b-instruct",
    "ibm/granite-3-2-8b-instruct",
    "ibm/granite-3-3-8b-instruct",
    "ibm/granite-3-8b-instruct",
    "ibm/granite-13b-instruct-v2",
    # IBM Granite - código
    "ibm/granite-3b-code-instruct",
    "ibm/granite-8b-code-instruct",
    "ibm/granite-20b-code-instruct",
    "ibm/granite-34b-code-instruct",
    # IBM Granite - segurança e visão (experimental)
    "ibm/granite-guardian-3-2b",
    "ibm/granite-guardian-3-8b",
    "ibm/granite-vision-3-2-2b",
    # Meta LLaMA
    "meta-llama/llama-2-13b-chat",
    "meta-llama/llama-3-2-1b-instruct",
    "meta-llama/llama-3-2-3b-instruct",
    "meta-llama/llama-3-3-70b-instruct",
    # Mistral / Mixtral
    "mistralai/mistral-large",
    "mistralai/mistral-medium-2505",
    "mistralai/mistral-small-3-1-24b-instruct-2503",
    "mistralai/mixtral-8x7b-instruct-v01",
    "mistralai/pixtral-12b",
]


# Carrega variáveis do .env
load_dotenv()
IAM_API_KEY = os.getenv("IBM_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")  # Inclua isso no seu .env

# Configurações
REGION = "us-south"  # ajuste se sua região for diferente

# Parâmetros da geração
generate_params = {
    GenParams.MAX_NEW_TOKENS: 1024,
    GenParams.TEMPERATURE: 0.2,
    GenParams.DECODING_METHOD: "sample",
}

# Inicializa o modelo
model_inference = ModelInference(
    model_id="mistralai/mistral-medium-2505",  # ou outro suportado, ex: LLAMA_2_70B_CHAT
    params=generate_params,
    credentials=Credentials(
        api_key=IAM_API_KEY, url=f"https://{REGION}.ml.cloud.ibm.com"
    ),
    project_id=PROJECT_ID,
)

# Prompt de teste
prompt = "Explique o que é aprendizado de máquina em linguagem simples."

# Geração
try:
    texto = model_inference.generate_text(prompt)
    print("Resposta do modelo:")
    print(texto)
except Exception as e:
    print("Erro ao gerar resposta:")
    print(e)
