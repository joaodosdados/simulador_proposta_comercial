import requests
import os
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

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
        model_inference = ModelInference(
            model_id=modelo,
            credentials=Credentials(
                api_key=IAM_API_KEY, url=f"https://{REGION}.ml.cloud.ibm.com"
            ),
            project_id=PROJECT_ID,
        )

        messages = [{"role": "user", "content": prompt}]
        resposta = model_inference.chat(
            messages=messages,
            params={
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        choices = resposta.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return ""

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
