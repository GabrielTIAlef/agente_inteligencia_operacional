# Validação da atualização do repositório

Data: 12/11/2026. Base anterior: `3b3391c`, branch `main`. As alterações locais anteriores foram preservadas e incluídas na atualização após revisão.

## Verificações repetidas

| Verificação | Resultado e escopo |
| --- | --- |
| Python | `RUN_DB_TESTS=1 .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`: 56 aprovados em 4,00 s |
| Frontend | `npm run lint` e `npm run build`: aprovados, Node 24.22.3 |
| Painel real | 460 pedidos e R$ 62.047,31 no recorte inicial de 18 a 31/10/2026 |
| Filtros combinados | Entregues + Rio de Janeiro + Mercado: 25 pedidos e R$ 3.683,98 |
| Monitoramento real | Dois registros concluídos; filtro Falhas mostra estado vazio; nenhum disparo |
| Responsividade | Desktop 1440 px e mobile 390 px; mobile sem rolagem horizontal, cabeçalho sticky, chat acessível e Escape para recolher |
| JSON baixado | Mesmos totais; `scope` com período, região, categoria e status; download novamente bloqueado após uso |

Os testes PostgreSQL usam tabelas temporárias com rollback. Não foram apagados pedidos, disparado o monitor ou ativada a agenda nesta revisão. Lint/build não equivalem a testes completos de navegador.

## Capturas

Imagens JPEG reais da aplicação em execução local, com FastAPI/PostgreSQL e dados sintéticos; sem mockups ou respostas de IA fabricadas. Desktop em 1440 × 940 e celular em 390 × 940. Capturas completas podem ter altura maior que o viewport.

- [Painel atual](evidence/painel-atual.jpg)
- [Filtros combinados](evidence/filtros-atuais.jpg)
- [Monitoramento](evidence/monitoramento-atual.jpg)
- [Chat aberto](evidence/chat-atual.jpg)
- [Painel mobile](evidence/painel-mobile.jpg)

As imagens antigas `.png` são evidências históricas preservadas; não ilustram a apresentação atual do README. O chat foi capturado aberto, sem nova consulta paga ao Gemini. A validação anterior inclui resposta real sobre os 1.000 pedidos e falhas 503; a continuação contextual não teve sucesso comprovado no provedor real. Veja [FRONTEND-DELIVERY.md](FRONTEND-DELIVERY.md).

## Limites da revisão

Não foi repetido o Compose nem o teste de falhas n8n nesta revisão. CI remoto deve ser consultado em [Actions](https://github.com/GabrielTIAlef/agente_inteligencia_operacional/actions). Não declarar aprovação remota com base apenas na suíte local.

A revisão editorial está registrada em [DOCUMENTATION-REVIEW.md](DOCUMENTATION-REVIEW.md). São verificados links relativos, arquivos candidatos ao commit e padrões de credenciais, além de comparação silenciosa com valores privados do ambiente. Isso reduz risco de publicação acidental e não constitui garantia de ausência de toda vulnerabilidade.

O teste opcional `frontend/tests/demo.mjs` foi atualizado para remover seletores da interface antiga. Sua sintaxe foi conferida; o roteiro completo não foi executado nesta revisão. As interações acima foram conferidas diretamente no navegador. O CI foi ampliado para executar também os testes opt-in com PostgreSQL 17 dedicado e migração antes da suíte.
