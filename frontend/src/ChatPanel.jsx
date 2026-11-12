
import { useEffect, useRef, useState } from 'react'
import './ChatPanel.css'

import { apiUrl, errorWithTrace } from './api'

const sugestoes = [
  'Quantos pedidos existem na base?',
  'Qual região tem a maior taxa de cancelamento?',
  'Qual categoria apresenta mais atrasos?',
]

function ChatPanel({ onClose, active }) {
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
  const inputRef = useRef(null)
  const fimConversa = useRef(null)
  const [cooldown, setCooldown] = useState(false)
  useEffect(() => { if (active) inputRef.current?.focus() }, [active])
  useEffect(() => { if (!cooldown) return; const timer = setTimeout(() => setCooldown(false), 30000); return () => clearTimeout(timer) }, [cooldown])
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

    if (!mensagem || requisicaoAtual.current || cooldown || mensagem.length > 500) {
      return
    }

    adicionarMensagem('user', mensagem)
    setPergunta('')
    setCarregando(true)

    const controller = new AbortController()
    requisicaoAtual.current = controller

    try {
      const resposta = await fetch(apiUrl('/agent/chat'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: mensagem,
          history: mensagens.filter(m => (m.role === 'user' || m.role === 'assistant') && m.id !== 0).slice(-6).map(m => ({role: m.role, content: m.content.slice(0, 1500)})),
        }),
        signal: controller.signal,
      })

      if (!resposta.ok) {
        if (resposta.status === 429) setCooldown(true)
        const body = await resposta.json().catch(() => null)
        const message = typeof body?.detail === 'string' ? body.detail : 'Não foi possível consultar o agente.'
        throw errorWithTrace(resposta, message)
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
<button type="button" className="chat-close" aria-label="Recolher chat" onClick={onClose}>×</button>
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
        {cooldown && <p role="alert">Cota atingida. Envio pausado por 30 segundos; a renovação depende do Gemini.</p>}
        <p className="chat-disclaimer">{pergunta.length}/500 caracteres · envio manual, sem repetição automática</p>
        <div className="chat-suggestions">
          {sugestoes.map((sugestao) => (
            <button
              key={sugestao}
              type="button"
              disabled={carregando || cooldown}
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
            ref={inputRef}
            id="chat-input"
            placeholder="Pergunte sobre os indicadores..."
            value={pergunta}
            maxLength={500}
            rows={2}
            onChange={(evento) =>
              setPergunta(evento.target.value)
            }
            onKeyDown={(evento) => {
              if (evento.key === 'Enter' && !evento.shiftKey && !evento.nativeEvent.isComposing) {
                evento.preventDefault()
                enviarPergunta(pergunta)
              }
            }}
          />

          <button
            type="submit"
            disabled={!pergunta.trim() || carregando || cooldown}
          >
            {carregando ? 'Enviando...' : 'Enviar →'}
          </button>
        </form>

        <p className="chat-disclaimer">
          Respostas geradas por IA. Confira indicadores
          importantes na fonte de dados.
        </p>
        <p className="chat-disclaimer">
          Contexto: até 6 mensagens recentes, limitadas a 1.500 caracteres cada. Mensagens antigas ficam visíveis, mas saem do contexto. Filtros do painel não são enviados à IA.
        </p>
      </div>
    </section>
  )
}

export default ChatPanel
