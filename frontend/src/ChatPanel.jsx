
import { useEffect, useRef, useState } from 'react'
import './ChatPanel.css'

const API_URL = 'http://127.0.0.1:8000/agent/chat'

const sugestoes = [
  'Quantos pedidos existem na base?',
  'Qual região tem a maior taxa de cancelamento?',
  'Qual categoria apresenta mais atrasos?',
]

function ChatPanel() {
  const [mensagens, setMensagens] = useState([
    {
      id: 0,
      role: 'assistant',
      content:
        'Olá! Sou o AI Operations Agent. ' +
        'Posso consultar indicadores operacionais ' +
        'do nosso marketplace fictício.',
    },
  ])

  const [pergunta, setPergunta] = useState('')
  const [carregando, setCarregando] = useState(false)
  const fimConversa = useRef(null)
  const proximoId = useRef(1)
  const requisicaoAtual = useRef(null)

  useEffect(() => {
    fimConversa.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    })
  }, [mensagens, carregando])

  useEffect(() => {
    return () => requisicaoAtual.current?.abort()
  }, [])

  function adicionarMensagem(role, content) {
    setMensagens((anteriores) => [
      ...anteriores,
      {
        id: proximoId.current++,
        role,
        content,
      },
    ])
  }

  async function enviarPergunta(texto) {
    const mensagem = texto.trim()

    if (!mensagem || carregando || mensagem.length > 500) {
      return
    }

    adicionarMensagem('user', mensagem)
    setPergunta('')
    setCarregando(true)

    const controller = new AbortController()
    requisicaoAtual.current = controller

    try {
      const resposta = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: mensagem,
        }),
        signal: controller.signal,
      })

      if (resposta.status === 429) {
        throw new Error(
          'O limite de uso do Gemini foi atingido. ' +
          'Tente novamente após a renovação da cota.'
        )
      }

      if (!resposta.ok) {
        throw new Error(
          'Não foi possível consultar o agente. ' +
          `Código HTTP: ${resposta.status}.`
        )
      }

      const dados = await resposta.json()

      if (
        dados.status !== 'success' ||
        typeof dados.response !== 'string'
      ) {
        throw new Error(
          'O servidor retornou uma resposta inesperada.'
        )
      }

      adicionarMensagem('assistant', dados.response)

    } catch (erro) {
      if (erro.name !== 'AbortError') {
        adicionarMensagem(
          'error',
          erro instanceof TypeError
            ? 'Não foi possível conectar à FastAPI. ' +
              'Verifique se o backend está ligado.'
            : erro.message
        )
      }
    } finally {
      if (requisicaoAtual.current === controller) {
        requisicaoAtual.current = null
        setCarregando(false)
      }
    }
  }

  function enviarFormulario(evento) {
    evento.preventDefault()
    enviarPergunta(pergunta)
  }

  return (
    <section className="chat-panel">
      <header className="chat-panel-header">
        <div className="chat-agent-avatar">✦</div>
        <div>
          <h2>AI Operations Agent</h2>
          <p>Assistente de inteligência operacional</p>
        </div>
        <span className="chat-mode-badge">
          Dados sintéticos
        </span>
      </header>

      <div
        className="chat-messages"
        aria-live="polite"
        aria-relevant="additions"
      >
        {mensagens.map((mensagem) => (
          <div
            key={mensagem.id}
            className={`chat-message ${mensagem.role}`}
          >
            <span className="message-author">
              {mensagem.role === 'user'
                ? 'Você'
                : mensagem.role === 'error'
                  ? 'Aviso'
                  : 'AI Operations Agent'}
            </span>
            <div className="message-bubble">
              {mensagem.content}
            </div>
          </div>
        ))}

        {carregando && (
          <div className="chat-message assistant">
            <span className="message-author">
              AI Operations Agent
            </span>
            <div className="message-bubble">
              Analisando sua pergunta...
            </div>
          </div>
        )}

        <div ref={fimConversa} />
      </div>

      <div className="chat-bottom">
        <div className="chat-suggestions">
          {sugestoes.map((sugestao) => (
            <button
              key={sugestao}
              type="button"
              disabled={carregando}
              onClick={() => enviarPergunta(sugestao)}
            >
              {sugestao}
            </button>
          ))}
        </div>

        <form
          className="chat-form"
          onSubmit={enviarFormulario}
        >
          <label
            htmlFor="chat-input"
            className="sr-only"
          >
            Sua pergunta
          </label>

          <textarea
            id="chat-input"
            placeholder="Pergunte sobre os indicadores..."
            value={pergunta}
            maxLength={500}
            rows={2}
            onChange={(evento) =>
              setPergunta(evento.target.value)
            }
            onKeyDown={(evento) => {
              if (evento.key === 'Enter' && !evento.shiftKey) {
                evento.preventDefault()
                enviarPergunta(pergunta)
              }
            }}
          />

          <button
            type="submit"
            disabled={!pergunta.trim() || carregando}
          >
            {carregando ? 'Enviando...' : 'Enviar →'}
          </button>
        </form>

        <p className="chat-disclaimer">
          Respostas geradas por IA. Confira indicadores
          importantes na fonte de dados.
        </p>
        <p className="chat-disclaimer">
          Cada pergunta é independente; o histórico visual
          não é enviado ao Gemini.
        </p>
      </div>
    </section>
  )
}

export default ChatPanel
