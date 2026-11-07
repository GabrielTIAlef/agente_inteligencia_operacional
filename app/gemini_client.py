import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Localiza a pasta principal do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(BASE_DIR / ".env")

def perguntar_ao_gemini(pergunta: str) -> str:
    """Envia uma pergunta ao modelo Gemini."""

    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        raise ValueError("A chave GEMINI_API_KEY não foi configurada.")

    with genai.Client(api_key=chave) as client:
        resposta = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=pergunta,
        )

        return resposta.text or "O modelo não retornou texto."


if __name__ == "__main__":
    pergunta = (
        "Explique resumidamente o que é um agente "
        "de inteligência artificial e como ele pode "
        "ajudar na análise de dados empresariais."
    )

    print("\n=== PERGUNTA ===")
    print(pergunta)

    print("\n=== RESPOSTA DO GEMINI ===")
    print(perguntar_ao_gemini(pergunta))
