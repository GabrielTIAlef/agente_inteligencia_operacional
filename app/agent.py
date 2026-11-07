
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.access import trace_id
from app.tools import executar_ferramenta


logger = logging.getLogger("uvicorn.error")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_general_metrics() -> dict:
    """Consulta os indicadores gerais dos pedidos.

    Retorna total de pedidos, soma dos valores registrados,
    taxa de cancelamento e taxa de atraso.
    """
    logger.info("request_id=%s tool=get_general_metrics", trace_id.get())

    return executar_ferramenta("get_general_metrics")


def get_regions_metrics() -> list[dict]:
    """Consulta os indicadores dos pedidos por região.

    Retorna total, soma dos valores, cancelamentos
    e atrasos para cada região.
    """
    logger.info("request_id=%s tool=get_regions_metrics", trace_id.get())

    return executar_ferramenta("get_regions_metrics")


def get_categories_metrics() -> list[dict]:
    """Consulta indicadores por categoria de pedidos.

    Retorna quantidade de pedidos, soma dos valores,
    taxa de cancelamento e taxa de atraso
    para Restaurante, Mercado e Farmácia.
    """
    logger.info("request_id=%s tool=get_categories_metrics", trace_id.get())

    return executar_ferramenta("get_categories_metrics")



def get_regions_by_period(
    data_inicio: str,
    data_fim: str,
) -> list[dict]:
    """Consulta indicadores regionais em um período.

    Args:
        data_inicio: Data inicial no formato AAAA-MM-DD.
        data_fim: Data final no formato AAAA-MM-DD.
    """
    logger.info("request_id=%s tool=get_regions_by_period", trace_id.get())

    return executar_ferramenta(
        "get_regions_by_period",
        {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        },
    )





INSTRUCOES = """
Você é o AI Operations Agent, um assistente
especializado em análise operacional de um
marketplace fictício de entregas.

REGRAS:
1. Responda sempre em português do Brasil.
2. Consulte as ferramentas quando o usuário
   solicitar indicadores operacionais.
3. Nunca invente quantidades, taxas ou valores.
4. Não use conhecimentos gerais para preencher
   indicadores ausentes.
5. Diferencie soma dos valores dos pedidos
   de receita efetivamente realizada.
6. Se o usuário informar datas, utilize a
   ferramenta de consulta por período.
7. Para rankings, informe os critérios utilizados.
8. Considere o tamanho da amostra ao interpretar taxas.
9. Não afirme causalidade apenas com base em correlação.
10. Se não houver ferramenta para responder com
    segurança, explique a limitação.
11. Nunca afirme ter executado alterações operacionais.
12. Não trate os dados fictícios como dados reais do iFood.
"""



def criar_chat():
    """Cria uma sessão de chat com histórico."""

    chave = os.environ["GEMINI_API_KEY"]

    client = genai.Client(api_key=chave, http_options=types.HttpOptions(timeout=15000))

    try:
        chat = client.chats.create(
            model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCOES,
                tools=[
                    get_general_metrics,
                    get_regions_metrics,
                    get_categories_metrics,
                    get_regions_by_period,
                ],
                temperature=0.2,
                max_output_tokens=2048,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=5,
                ),
            ),
        )
    except Exception:
        client.close()
        raise

    return client, chat


def perguntar_ao_agente(pergunta: str) -> str:
    """Permite realizar uma consulta independente."""

    client, chat = criar_chat()

    try:
        resposta = chat.send_message(pergunta)
        return resposta.text or "Não foi gerada uma resposta."
    finally:
        client.close()




if __name__ == "__main__":
    pergunta = (
        "Compare as categorias Restaurante, Mercado "
        "e Farmácia. Qual apresenta a maior taxa "
        "de atraso e qual possui mais pedidos?"
    )

    print("\n=== PERGUNTA ===")
    print(pergunta)

    print("\n=== RESPOSTA DO AGENTE ===")
    print(perguntar_ao_agente(pergunta))
