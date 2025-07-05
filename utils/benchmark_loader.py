from pathlib import Path


def carregar_benchmark(nome: str) -> str:
    caminho = Path("benchmarks") / f"{nome}.txt"
    if caminho.exists():
        return caminho.read_text(encoding="utf-8")
    return ""
