import ChatPanel from './ChatPanel'
import OperationsReport, { Breakdown } from './OperationsReport'
import { fetchReport } from './api'
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


  const [report, setReport] = useState(null)
  const [refreshCount, setRefreshCount] = useState(0)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)

  function refresh() {
    setCarregando(true)
    setErro(null)
    setRefreshCount((previous) => previous + 1)
  }

  useEffect(() => {
    const controller = new AbortController()
    fetchReport(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setReport(data)
      })
      .catch((error) => {
        if (!controller.signal.aborted) {
          setErro(error instanceof TypeError ? 'Não foi possível conectar à FastAPI.' : error.message)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setCarregando(false)
      })
    return () => controller.abort()
  }, [refreshCount])

  const metricCards = report ? criarCartoes(report.summary) : []

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
              aria-current={activePage === item.id ? "page" : undefined}
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
                Todo o histórico
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
                  <button type="button" className="secondary-button" onClick={refresh}>Tentar novamente</button>
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


            {report && !carregando && !erro && (
              <section className="breakdown-grid" aria-label="Detalhamento dos indicadores">
                <Breakdown title="Pedidos por região" rows={report.regions} dimension="regiao" />
                <Breakdown title="Pedidos por categoria" rows={report.categories} dimension="categoria" />
              </section>
            )}
          </div>
        )}

        {activePage === 'chat' && (
          <div className="page-content">
            <ChatPanel />
          </div>
        )}
        
        {activePage === 'automations' && (
          <div className="page-content">
            <OperationsReport report={report} loading={carregando} error={erro} refresh={refresh} />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
