# Interface de inteligência operacional

React/Vite com duas abas: Painel operacional e Monitoramento, além do chat flutuante compartilhado. A interface consulta a API local; não armazena chaves Gemini ou token do monitor.

Com Node 24 e a API na porta 8000:

```powershell
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
npm run lint
npm run build
```

Veja [instalação completa](../docs/SETUP.md), [contratos e entrega](../docs/FRONTEND-DELIVERY.md) e [evidências](../docs/VALIDATION.md). O teste opcional em `tests/demo.mjs` precisa de Playwright e Edge locais; não chama Gemini nem dispara o monitor.
