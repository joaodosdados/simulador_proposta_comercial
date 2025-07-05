from pathlib import Path


def carregar_prompt(nome="default_prompt") -> str:
    caminho = Path("prompts") / f"{nome}.txt"
    if caminho.exists():
        return caminho.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"Prompt '{nome}' não encontrado.")
