import ChatPanel from './ChatPanel'
import { useEffect, useState } from 'react'
import './App.css'

const navigation = [
  { id: 'dashboard', icon: '▦', label: 'Dashboard' },
  { id: 'chat', icon: '✦', label: 'Chat com IA' },
  { id: 'automations', icon: '⚡', label: 'Automações' },
]


const formatarNumero = (valor) =>
  new Intl.NumberFormat('pt-BR').format(valor)

const formatarMoeda = (valor) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valor)

const formatarPercentual = (valor) =>
  `${new Intl.NumberFormat('pt-BR', {
    maximumFractionDigits: 2,
  }).format(valor)}%`

function criarCartoes(indicadores) {
  return [
    {
      label: 'Total de pedidos',
      value: formatarNumero(indicadores.total_pedidos),
      description: 'Registros consultados no PostgreSQL',
      icon: '▤',
    },
    {
      label: 'Valor dos pedidos',
      value: formatarMoeda(indicadores.valor_total),
      description: 'Soma dos valores registrados',
      icon: '◈',
    },
    {
      label: 'Taxa de cancelamento',
      value: formatarPercentual(
        indicadores.taxa_cancelamento
      ),
      description: 'Percentual de pedidos cancelados',
      icon: '⊘',
    },
    {
      label: 'Taxa de atraso',
      value: formatarPercentual(
        indicadores.taxa_atraso
      ),
      description: 'Percentual de pedidos em atraso',
      icon: '◷',
    },
  ]
}


function App() {
  const [activePage, setActivePage] = useState('dashboard')


  const [indicadores, setIndicadores] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    const controller = new AbortController()

    async function buscarIndicadores() {
      try {
        const resposta = await fetch(
          'http://127.0.0.1:8000/metrics/database',
          { signal: controller.signal }
        )

        if (!resposta.ok) {
          throw new Error(
            `Erro HTTP ${resposta.status}`
          )
        }

        const resultado = await resposta.json()

        if (
          resultado.status !== 'success' ||
          !resultado.data ||
          typeof resultado.data.total_pedidos !== 'number'
        ) {
          throw new Error('Formato de resposta inesperado')
        }

        setIndicadores(resultado.data)
        setErro(null)

      } catch (error) {
        if (error.name !== 'AbortError') {
          setErro(
            'Não foi possível carregar os indicadores. ' +
            'Verifique se a FastAPI está funcionando.'
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setCarregando(false)
        }
      }
    }

    buscarIndicadores()

    return () => controller.abort()
  }, [])

  const metricCards = indicadores
    ? criarCartoes(indicadores)
    : []


  const pageTitle = {
    dashboard: 'Visão geral',
    chat: 'Chat com IA',
    automations: 'Automações',
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">✦</div>

          <div>
            <strong>AI Operations</strong>
            <span>AGENT PLATFORM</span>
          </div>
        </div>

        <div className="navigation-label">WORKSPACE</div>

        <nav className="navigation" aria-label="Menu principal">
          {navigation.map((item) => (
            <button
              key={item.id}
              type="button"
              className={
                activePage === item.id
                  ? 'nav-item active'
                  : 'nav-item'
              }
              onClick={() => setActivePage(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="environment-dot" />
          <div>
            <strong>Ambiente local</strong>
            <span>Modo demonstração</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="eyebrow">OPERATIONS INTELLIGENCE</span>
            <h1>{pageTitle[activePage]}</h1>
          </div>

          <div className="topbar-actions">
            <span className="demo-badge">Dados sintéticos</span>
            <div className="avatar">AI</div>
          </div>
        </header>

        {activePage === 'dashboard' && (
          <div className="page-content">
            <section className="welcome-banner">
              <div>
                <span className="banner-label">
                  INTELIGÊNCIA OPERACIONAL
                </span>

                <h2>Decisões melhores começam com dados.</h2>

                <p>
                  Explore indicadores do marketplace fictício
                  e prepare análises com inteligência artificial.
                </p>

                <button
                  type="button"
                  className="primary-button"
                  onClick={() => setActivePage('chat')}
                >
                  Explorar assistente IA →
                </button>
              </div>

              <div className="banner-illustration">✦</div>
            </section>

            <div className="section-heading">
              <div>
                <h2>Indicadores operacionais</h2>
                <p>
                  Indicadores consultados no PostgreSQL • Dados sintéticos
                </p>
              </div>
              <span className="section-tag">
                Outubro de 2026
              </span>
            </div>

            
            <section className="metrics-grid">
              {carregando && (
                <div className="data-message">
                  Carregando indicadores do PostgreSQL...
                </div>
              )}

              {erro && !carregando && (
                <div className="data-message error-message" role="alert">
                  {erro}
                </div>
              )}

              {!carregando && !erro && metricCards.map((metric) => (
                <article className="metric-card" key={metric.label}>
                  <div className="metric-header">
                    <span>{metric.label}</span>
                    <span className="metric-icon">{metric.icon}</span>
                  </div>

                  <strong>{metric.value}</strong>
                  <p>{metric.description}</p>
                </article>
              ))}
            </section>


            <section className="content-grid">
              <article className="content-card">
                <h3>Análise operacional</h3>
                <p>
                  Em breve, esta área mostrará gráficos
                  conectados ao PostgreSQL.
                </p>

                <div className="empty-visual">
                  <span>▥</span>
                  <strong>Visualizações em preparação</strong>
                  <p>Integração prevista para a Etapa 30.</p>
                </div>
              </article>

              <article className="content-card">
                <h3>Assistente inteligente</h3>
                <p>
                  Analise os dados utilizando perguntas
                  em linguagem natural.
                </p>

                <div className="assistant-preview">
                  <span>✦</span>
                  <strong>AI Operations Agent</strong>
                  <p>
                    Consultas SQL, indicadores e análises
                    com Gemini.
                  </p>
                </div>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setActivePage('chat')}
                >
                  Abrir chat →
                </button>
              </article>
            </section>
          </div>
        )}

        {activePage === 'chat' && (
          <div className="page-content">
            <ChatPanel />
          </div>
        )}
        
        {activePage === 'automations' && (
          <div className="page-content">
            <section className="placeholder-page">
              <div className="placeholder-icon">⚡</div>
              <h2>Automações inteligentes</h2>
              <p>
                Nesta área, criaremos fluxos automatizados
                utilizando n8n.
              </p>
              <span className="coming-soon">
                Funcionalidade futura
              </span>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
