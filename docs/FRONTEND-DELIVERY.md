> Registro histórico de validação anterior à atualização do GitHub. A interface e o contrato atuais estão no README e em [VALIDATION.md](VALIDATION.md). Referências a ausência de push descrevem a etapa original.

# Atualização BI — 12/11/2026

Esta atualização substitui o comportamento de filtros e exportação descrito na entrega inicial abaixo.

- Período, região e categoria atualizam automaticamente, sem botão Aplicar.
- Entregues, Cancelados e Em atraso são seleções clicáveis, com destaque e remoção por segundo clique. Rankings e dias também filtram. Filtros se combinam; seleções individuais podem ser removidas pelos chips ou todas pelo botão Limpar filtros.
- KPIs, série diária, rankings e comparação anterior usam todos os filtros, incluindo status. O gráfico seletor de status mantém as contagens dos três status considerando os demais filtros para permitir trocar a seleção, com essa abrangência identificada na tela.
- Prévia e JSON usam o mesmo período/região/categoria/status do Dashboard, inclusive no recorte inicial de 14 dias. O JSON inclui scope com filtros aplicados. Aprovações anteriores são invalidadas quando os filtros mudam; exportação não fica disponível enquanto o painel atualiza ou apresenta erro.
- GET /operations/dashboard aceita status opcional validado. GET /reports/operations aceita os mesmos filtros e preserva os campos anteriores. Chamadas sem parâmetros continuam exportando toda a base para manter compatibilidade com os clientes existentes, incluindo n8n.
- Verificação: lint e build aprovados; 56 testes Python aprovados com RUN_DB_TESTS=1, incluindo cruzamento de filtros, janela anterior e estado vazio em tabela PostgreSQL temporária com rollback.
- Navegador: seleção Entregues e combinação automática com Rio de Janeiro + Mercado produziram 25 pedidos e R$ 3.683,98. O JSON baixado foi aberto e conferido: mesmos totais e os quatro filtros em scope. Troca para Em atraso invalidou a aprovação anterior; segundo clique removeu status. Testes em desktop e 390 px; alteração de data revalidada após ajuste dos eventos do seletor.
- Nenhuma chamada Gemini foi necessária nesta atualização. Nenhum push, publicação, ativação de agenda, alteração de credenciais ou exclusão de dados. Início local e pendências 24/7 continuam como descritos abaixo.

---
# Entrega local — Dashboard, Monitoramento e chat

Validação em 12/11/2026. Referência: `docs/LOCAL-READINESS.md`. As alterações anteriores da árvore de trabalho foram preservadas. Nenhum push, publicação cloud, ativação de agenda ou exclusão de dados foi realizado.

## Produto entregue

- Navegação com apenas Dashboard operacional e Monitoramento.
- Dashboard com cartões KPI, filtros de datas/região/categoria, comparativo com janela anterior, status com barras, rankings com seleção de região/categoria e gráfico diário com tooltip por mouse/foco e seleção de dia. Os filtros são aplicados à API existente; rankings usam os mesmos filtros.
- Tabela acessível dos valores diários, títulos/labels, foco visível, atalho para o conteúdo, estados de carregamento/erro com nova tentativa e ausência de pedidos.
- Relatório operacional integrado ao Dashboard em painel de indicadores e revisão, com tabela regional, inspeção JSON, aprovação vinculada à versão e download local. O contrato existente exporta **toda a base**, independentemente dos filtros do Dashboard; isso está identificado na interface. A aprovação é removida após download e atualização da prévia.
- Monitoramento com contagens de registros/conclusões/falhas/alertas, indicadores da última análise, filtro de status, detalhes por execução e regras de cancelamento/atraso/queda de volume. Atualizar apenas relê os dados. Sem botão público para disparar o monitor.
- Chat flutuante em qualquer aba, expandir/recolher, Escape para fechar e devolver foco, foco inicial no campo, mensagens roláveis e histórico preservado durante a sessão da página. Recarregar a página inicia nova sessão; nada é salvo em armazenamento persistente do navegador.
- Envio real para `POST /agent/chat`. Campo `message` e resposta existentes preservados. Campo opcional `history` aceita até 6 mensagens com papéis user/assistant e até 1.500 caracteres por mensagem. A pergunta continua limitada a 500 caracteres. O frontend trunca o contexto; mensagens antigas continuam visíveis. Os filtros do painel não são enviados implicitamente à IA.
- Contexto passado ao SDK como histórico user/model. As mesmas ferramentas de leitura e instruções de fidelidade permanecem. Sem execução de SQL arbitrário ou alteração operacional pelo chat.
- Uma solicitação por vez, envio manual, nenhuma repetição automática, pausa de 30 segundos na interface após 429 (não garante renovação de cota). O SDK passa a usar uma tentativa por chamada; mantidos timeout de 15s, saída de 2.048 tokens e limite de 5 chamadas automáticas de ferramentas. A pausa no navegador não substitui autenticação/limitação persistente de produção.

## Evidências e verificações

| Verificação | Resultado |
| --- | --- |
| `npm run lint` | Aprovado |
| `npm run build` | Aprovado |
| `RUN_DB_TESTS=1 .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider` | 48 aprovados, incluindo PostgreSQL |
| Novos testes de contexto | Encaminhamento ao agente, conversão user/model no SDK e rejeição de contexto excessivo/papel inválido |
| API Dashboard completo vs relatório | 1.000 pedidos; valor dos pedidos R$ 135.544,32 em ambos |
| API sem correspondência de região | Zero pedidos, sem dados inventados |
| Histórico real | 2 execuções concluídas; última análise de 460 pedidos, sem alertas |
| Monitor sem token | 403; nenhum disparo autorizado executado nesta tarefa |
| n8n `/healthz` | 200 |
| Navegador desktop, tablet 768 e celular 390 px | Layout, filtros, chat e navegação inspecionados |
| Ranking clicável | Rio de Janeiro: 99 pedidos no recorte de 18 a 31/10 |
| Barra do gráfico clicável | 18/10 + Rio de Janeiro: 15 pedidos, datas e KPIs atualizados |
| Histórico filtrado por falhas | Estado vazio correto; não existem falhas nos dois registros reais |
| Exportação no navegador mobile | Bloqueada antes de aprovação; download após aprovação; bloqueada novamente após download |
| Arquivo JSON baixado | PostgreSQL, 1.000 pedidos, 5 regiões, 3 categorias |
| Gemini real pelo widget | Segunda consulta respondeu “Existem 1.000 pedidos registrados na base.” |
| Erro real do provedor | Primeira consulta e pergunta de continuação retornaram 503/ServerError após cerca de 16s; referência de diagnóstico visível, sem retry automático |

O contexto de continuação foi validado pelos testes de contrato e SDK. A tentativa de continuação no provedor real encontrou indisponibilidade, portanto não é declarada como resposta contextual bem-sucedida. Foram feitas apenas três consultas reais; não se repetiram chamadas para tentar contornar a falha do provedor. O comportamento 429 está coberto pela suíte da API; a cota real não foi esgotada deliberadamente.

## Limites dos dados disponíveis

O histórico exposto é o de `monitor_runs`, persistido pela API quando acionada pelo n8n, e não a telemetria completa de execuções do editor n8n. A API retorna até 20 registros. Não há duração, execução em andamento, estado de agenda ou SLA de disponibilidade nessa resposta. Falhas anteriores ao acesso à API podem existir somente no n8n. A interface não inventa esses indicadores. “Cancelamento” e “atraso” se referem a pedidos, não a cancelamento de workflow ou atraso de agenda.

O monitor usa os 14 dias até o último pedido da base sintética (outubro de 2026), não os últimos 14 dias do relógio atual. Não há envio externo de alertas implementado; candidato a notificação representa apenas prévia. Valor dos pedidos soma todos os status; não é receita realizada.

## Início local

Na raiz `<raiz-do-projeto>`, com PostgreSQL iniciado:

```powershell
.\deploy\start-local.ps1
```

- Dashboard: http://127.0.0.1:5173
- API: http://127.0.0.1:8000/health
- Editor n8n: http://127.0.0.1:5678

O script não substitui serviços já presentes nas portas, nem ativa agendas. Logs `local-*.log` são locais e ignorados pelo Git. Os serviços foram iniciados para esta validação.

## Pendências para publicação 24/7

Seguir a etapa de implantação de `LOCAL-READINESS.md`, com autorização explícita: escolher hospedagem/domínio/orçamento, proteger o chat com autenticação e rate limit persistente, contas PostgreSQL de menor privilégio, backup e restauração testada, HTTPS/proxy, serviços com reinício automático, monitoramento externo e rotação de logs. Manter o editor n8n privado e a rota de disparo interna com MONITOR_TOKEN. Não enviar `.env`, token, chave Gemini ou chave de criptografia n8n ao GitHub. Validar novamente a disponibilidade/cota Gemini na implantação. Ativar agenda apenas após autorização e validação no servidor.

Nenhuma dessas etapas de publicação foi executada. As mudanças continuam locais, junto das correções anteriores.
