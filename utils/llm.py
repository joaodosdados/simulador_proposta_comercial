# utils/llm.py
import requests


def gerar_resposta_ollama(prompt, modelo="mistral", temperature=0.4):
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
