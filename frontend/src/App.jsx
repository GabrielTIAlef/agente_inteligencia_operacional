import { useEffect, useState } from 'react'
import ChatPanel from './ChatPanel'
import { apiUrl, errorWithTrace } from './api'
import './App.css'

const number = new Intl.NumberFormat('pt-BR')
const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const percent = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })
const statuses = { entregue: 'Entregues', cancelado: 'Cancelados', em_atraso: 'Em atraso' }
const day = (value) => value?.split('-').reverse().join('/')
const rate = (value) => value == null ? '—' : percent.format(value) + '%'

function DataView({ path, children }) {
  const [state, setState] = useState(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    fetch(apiUrl(path), { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw errorWithTrace(response, 'A consulta falhou.')
        return response.json()
      })
      .then((data) => {
        if (!controller.signal.aborted) setState({ path, retry, data })
      })
      .catch((error) => {
        if (!controller.signal.aborted) setState({ path, retry, error: error.message })
      })
    return () => controller.abort()
  }, [path, retry])

  if (state?.path !== path || state.retry !== retry) return <p role="status">Consultando PostgreSQL…</p>
  if (state.error) return <p role="alert">{state.error} <button onClick={() => setRetry(retry + 1)}>Tentar novamente</button></p>
  return children(state.data)
}

function Ranking({ title, rows }) {
  return <section className="report-section">
    <h2>{title}</h2>
    <table>
      <thead><tr><th scope="col">Grupo</th><th scope="col">Pedidos</th><th scope="col">Valor</th></tr></thead>
      <tbody>{rows.map((row) => <tr key={row.label}>
        <th scope="row">{row.label}</th><td>{number.format(row.orders)}</td><td>{money.format(row.value)}</td>
      </tr>)}</tbody>
    </table>
  </section>
}

function Daily({ rows }) {
  if (!rows.length) return <p>Sem cobertura no intervalo.</p>
  const max = Math.max(1, ...rows.map((row) => row.orders))
  return <>
    <div className="chart" aria-hidden="true">
      {rows.map((row) => <span key={row.date} title={day(row.date) + ' · ' + row.orders}
        style={{ height: Math.max(1, row.orders * 100 / max) + '%' }} />)}
    </div>
    <p className="chart-label"><span>{day(rows[0].date)}</span><span>{day(rows.at(-1).date)}</span></p>
    <details><summary>Consultar valores diários</summary>
      <table><thead><tr><th scope="col">Data</th><th scope="col">Pedidos</th></tr></thead>
        <tbody>{rows.map((row) => <tr key={row.date}><th scope="row">{day(row.date)}</th><td>{row.orders}</td></tr>)}</tbody>
      </table>
    </details>
  </>
}

function Dashboard({ data, onFilter, applied }) {
  const { coverage, period, summary, previous } = data
  const [invalid, setInvalid] = useState(false)
  const metrics = [
    ['Pedidos', number.format(summary.orders), 'Todos os status'],
    ['Valor dos pedidos', money.format(summary.value), 'Soma registrada em todos os status'],
    ['Valor médio', summary.average == null ? '—' : money.format(summary.average), 'Valor registrado ÷ total de pedidos'],
    ['Cancelamento', rate(summary.cancellation), 'Cancelados ÷ total de pedidos'],
    ['Atraso', rate(summary.late), 'Em atraso ÷ total de pedidos'],
  ]

  function filter(event) {
    event.preventDefault()
    const fields = new FormData(event.currentTarget)
    const span = (Date.parse(fields.get('end')) - Date.parse(fields.get('start'))) / 86400000 + 1
    setInvalid(!(span >= 1 && span <= 366))
    if (span >= 1 && span <= 366) onFilter(new URLSearchParams([...fields].filter(([, value]) => value)).toString())
  }

  return <>
    <p className="intro">{coverage ? 'Base de ' + day(coverage.start) + ' a ' + day(coverage.end) : 'A base ainda não contém pedidos.'}</p>
    {coverage && <form className="filters" onSubmit={filter}>
      <label>De<input type="date" name="start" min={coverage.start} max={coverage.end}
        defaultValue={period.start < coverage.start ? coverage.start : period.start} required /></label>
      <label>Até<input type="date" name="end" min={coverage.start} max={coverage.end} defaultValue={period.end} required /></label>
      <label>Região<select name="region" defaultValue={applied.get('region') || ''}>
        <option value="">Todas</option>{data.filters.regions.map((value) => <option key={value}>{value}</option>)}
      </select></label>
      <label>Categoria<select name="category" defaultValue={applied.get('category') || ''}>
        <option value="">Todas</option>{data.filters.categories.map((value) => <option key={value}>{value}</option>)}
      </select></label>
      <button type="submit">Aplicar</button><button type="button" onClick={() => onFilter('')}>Restaurar</button>
      {invalid && <p role="alert">Escolha um intervalo de 1 a 366 dias.</p>}
    </form>}
    {period && <p className="period">Recorte · {day(period.start)} a {day(period.end)}</p>}
    <dl className="metrics">{metrics.map(([name, value, detail]) => <div key={name}>
      <dt>{name}</dt><dd>{value}</dd><small>{detail}</small>
    </div>)}</dl>
    {summary.orders === 0 && <p role="status">Nenhum pedido para este recorte.</p>}
    <div className="columns">
      <section className="report-section"><h2>Ritmo de pedidos</h2>
        <p>{previous ? 'Janela anterior de mesma duração · ' + number.format(previous.orders) +
          ' pedidos · diferença de ' + number.format(summary.orders - previous.orders) :
          'A base não cobre integralmente as duas janelas para comparação.'}</p>
        <Daily rows={data.daily} />
      </section>
      <section className="report-section"><h2>Status dos pedidos</h2>
        <ul className="status-list">{Object.entries(summary.status).map(([key, value]) => <li key={key}>
          <span>{statuses[key]}</span><strong>{number.format(value)}</strong>
          <meter min="0" max={summary.orders || 1} value={value} aria-label={statuses[key]} />
        </li>)}</ul>
      </section>
    </div>
    {summary.orders > 0 && <div className="columns rankings">
      <Ranking title="Volume por região" rows={data.regions} /><Ranking title="Volume por categoria" rows={data.categories} />
    </div>}
  </>
}

function Monitor({ runs }) {
  return <section className="report-section">
    <h2>Registro de execuções</h2>
    <p>Monitor diário do n8n · até 20 registros · janela de 14 dias até o último pedido da base.</p>
    {!runs.length && <p role="status">Nenhuma execução registrada.</p>}
    {runs.map((run, index) => <details key={run.id} open={index === 0} className="run">
      <summary>{new Date(run.finished_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })} · {run.status === 'completed' ? 'Concluída' : 'Falha'}</summary>
      {run.report ? <>
        {run.report.period && <p>{day(run.report.period.start)} a {day(run.report.period.end)}</p>}
        <p>{run.report.summary} <small>({run.report.method})</small></p>
        {run.report.alerts.length > 0 && <ul>{run.report.alerts.map((alert) => <li key={alert.label}>
          {alert.label} · {rate(alert.value)} · limiar de {rate(alert.threshold)} · base de {alert.sample} pedidos
        </li>)}</ul>}
        {run.report.notification_candidate && <p>Alertas selecionados para prévia de notificação.</p>}
      </> : <p>A análise falhou. O fluxo pode ser executado novamente no n8n.</p>}
    </details>)}
  </section>
}

const pages = { dashboard: 'Boletim operacional', automations: 'Monitoramento', chat: 'Assistente de dados' }

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [query, setQuery] = useState('')
  const [reset, setReset] = useState(0)
  return <>
    <header className="masthead">
      <div><strong>Operação / Marketplace</strong><small>DEMONSTRAÇÃO · DADOS SINTÉTICOS</small></div>
      <nav aria-label="Menu principal">{Object.entries(pages).map(([key, label]) =>
        <button key={key} onClick={() => setPage(key)} aria-current={page === key ? 'page' : undefined}>{label}</button>)}</nav>
    </header>
    <main>
      <h1>{pages[page]}</h1>
      {page === 'dashboard' && <DataView key={reset} path={'/operations/dashboard' + (query ? '?' + query : '')}>
        {(data) => <Dashboard data={data} applied={new URLSearchParams(query)} onFilter={(next) => {
          setQuery(next)
          if (!next) setReset(reset + 1)
        }} />}
      </DataView>}
      {page === 'automations' && <DataView path="/operations/monitor/runs">{({ runs }) => <Monitor runs={runs} />}</DataView>}
      {page === 'chat' && <ChatPanel />}
    </main>
  </>
}
