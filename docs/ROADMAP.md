# Roadmap

## Entregue e validado localmente

- BI com filtros combináveis de período, região, categoria e status; gráficos/rankings clicáveis.
- Comparação com janela anterior e exportação JSON do recorte, aprovada por versão.
- Chat flutuante nas duas abas com contexto limitado e ferramentas de leitura.
- Monitor determinístico acionado por n8n, histórico PostgreSQL e idempotência diária.
- Inicialização Windows, migração sem recarga de pedidos, 56 testes Python e lint/build aprovados.

## Antes de disponibilizar publicamente

- Escolher hospedagem, domínio e orçamento; revisar versões e segurança.
- Autenticação, limite persistente e controle de custos Gemini.
- Contas de banco com privilégio mínimo, HTTPS e redes privadas.
- Backup e restauração testados, reinício automático, logs e observabilidade externa.
- Revalidar ambiente remoto e Gemini real; ativar agenda apenas com autorização.

## Evoluções possíveis, sem compromisso de entrega

- Fonte de dados real com contrato, qualidade e regras de privacidade definidos.
- Paginação e telemetria operacional do monitor, conforme necessidade.
- Notificações externas com destino, consentimento, deduplicação e tratamento de falhas.
- Testes automatizados de navegador no CI e avaliação ampliada do assistente.

Não há previsão ou resultado de negócio prometido para essas evoluções.
