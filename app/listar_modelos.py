import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def listar_modelos():
    with genai.Client(
        api_key=os.environ["GEMINI_API_KEY"]
    ) as client:
        for modelo in client.models.list():
            acoes = modelo.supported_actions or []

            if "generateContent" in acoes:
                print(modelo.name)


if __name__ == "__main__":
    listar_modelos()
