import requests
import os
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# Carrega .env na importação do módulo
load_dotenv()
IAM_API_KEY = os.getenv("IBM_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
REGION = "us-south"


def gerar_resposta_watsonx(
    prompt,
    modelo="mistralai/mistral-small-3-1-24b-instruct-2503",
    temperature=0.4,
    max_tokens=512,
):
    try:
        generate_params = {
            GenParams.MAX_NEW_TOKENS: max_tokens,
            GenParams.TEMPERATURE: temperature,
            GenParams.DECODING_METHOD: "sample",  # ou "greedy"
        }

        model_inference = ModelInference(
            model_id=modelo,
            params=generate_params,
            credentials=Credentials(
                api_key=IAM_API_KEY, url=f"https://{REGION}.ml.cloud.ibm.com"
            ),
            project_id=PROJECT_ID,
        )

        resposta = model_inference.generate_text(prompt)
        return resposta.strip()

    except Exception as e:
        print("Erro ao consultar o modelo via Watsonx:", e)
        return None


def gerar_resposta_ollama(prompt, modelo="llama3:latest", temperature=0.4):
    try:
        resposta = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": modelo,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
            },
            timeout=60,
        )
        resposta.raise_for_status()
        return resposta.json()["response"].strip()
    except Exception as e:
        print("Erro ao consultar o modelo via Ollama:", e)
        return None
