import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
from utils.prompt_loader import carregar_prompt

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def gerar_texto_personalizado(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


def agente_identifica_oportunidades(texto: str) -> str:
    if not texto.strip():
        return "⚠️ Nenhum conteúdo fornecido para análise."

    try:
        prompt_template = carregar_prompt("default_prompt")
        prompt = prompt_template.replace("{texto}", texto)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um consultor sênior de Data Science",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=700,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Erro na chamada do modelo: {str(e)}"
