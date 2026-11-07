
from app.agent import criar_chat


def iniciar_chat():
    """Inicia o chat interativo do AI Operations Agent."""

    print("=" * 55)
    print("        AI OPERATIONS AGENT")
    print("        Chat interativo com Gemini")
    print("=" * 55)

    print("\nBem-vindo ao AI Operations Agent!")
    print("Faça perguntas sobre os pedidos do marketplace.")
    print("Digite 'sair' para encerrar a conversa.")
    print("Digite 'limpar' para iniciar uma nova conversa.\n")

    client, chat = criar_chat()

    try:
        while True:
            try:
                pergunta = input("\nVocê: ").strip()

            except (KeyboardInterrupt, EOFError):
                print("\nEncerrando o chat...")
                break

            if not pergunta:
                continue
            
            if len(pergunta) > 500:
                print(
                    "\nSua pergunta ultrapassou o limite "
                    "de 500 caracteres."
                )
                continue

            if pergunta.lower() in {"sair", "exit", "quit"}:
                print("\nAté a próxima!")
                break

            if pergunta.lower() == "limpar":
                # Reinicia a sessão e apaga o histórico
                # da conversa atual.
                client.close()
                client, chat = criar_chat()

                print("\nHistórico da conversa reiniciado.")
                continue


            try:
                resposta = chat.send_message(pergunta)

                print("\nAgente:")
                print(
                    resposta.text
                    or "Não foi possível gerar uma resposta textual."
                )

            except Exception as erro:
                print("\nNão foi possível processar sua pergunta.")

                tipo_erro = type(erro).__name__
                print(f"Tipo do erro: {tipo_erro}")

                print(
                    "A conversa será reiniciada para evitar "
                    "um histórico inconsistente."
                )

                client.close()
                client, chat = criar_chat()


            except Exception as erro:
                print("\nOcorreu um erro ao processar sua pergunta.")
                print(f"Tipo do erro: {type(erro).__name__}")
                # Não exibimos a mensagem completa para evitar
                # exposição acidental de dados internos.

    finally:
        client.close()


if __name__ == "__main__":
    iniciar_chat()
