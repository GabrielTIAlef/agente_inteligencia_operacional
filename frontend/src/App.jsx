import { useEffect, useRef, useState } from 'react'
import ChatPanel from './ChatPanel'
import OperationsReport from './OperationsReport'
import { apiUrl, errorWithTrace } from './api'
import './App.css'

const number = new Intl.NumberFormat('pt-BR')
const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const percent = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })
const statuses = { entregue: 'Entregues', cancelado: 'Cancelados', em_atraso: 'Em atraso' }
const day = (value) => value?.split('-').reverse().join('/')
const delta = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1, signDisplay: 'exceptZero' })
const rate = (value) => value == null ? '—' : percent.format(value) + '%'

function DataView({ path, children, retain = false }) {
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
        if (!controller.signal.aborted) setState(previous => ({ path, retry, data: retain ? previous?.data : undefined, error: error.message }))
      })
    return () => controller.abort()
  }, [path, retry, retain])

  const busy = state?.path !== path || state?.retry !== retry
  if (retain && state?.data) return children(state.data, { busy, error: busy ? null : state.error, retry: () => setRetry(retry + 1) })
  if (busy) return <div className="loading-state" role="status"><span className="loading-dot" /> Consultando PostgreSQL…</div>
  if (state.error) return <p className="error-state" role="alert">{state.error} <button onClick={() => setRetry(retry + 1)}>Tentar novamente</button></p>
  return children(state.data, { busy: false })
}

function Ranking({ title, rows, onSelect }) {
  const ordered = [...rows].sort((a, b) => b.orders - a.orders || a.label.localeCompare(b.label, 'pt-BR'))
  const total = ordered.reduce((sum, row) => sum + row.orders, 0)
  return <section className="report-section ranking-card">
    <div className="ranking-heading"><h2>{title}</h2><span className="ranking-label">POR PEDIDOS</span></div>

    <ol className="ranking-list">
      {ordered.map((row, index) => <li key={row.label}>
        <button className="ranking-item" onClick={() => onSelect(row.label)} aria-label={`${index + 1}º lugar, ${row.label}, ${number.format(row.orders)} pedidos, valor dos pedidos ${money.format(row.value)}. Filtrar por ${row.label}`}>
          <span className={'ranking-position place-' + (index + 1)} aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
          <span className="ranking-detail">
            <span className="ranking-topline"><strong>{row.label}</strong><span className="ranking-count">{number.format(row.orders)} <small>pedidos</small></span></span>
            <span className="ranking-track" aria-hidden="true"><span style={{width: `${total ? row.orders * 100 / total : 0}%`}} /></span>
            <span className="ranking-bottomline"><span>{money.format(row.value)} <small>em pedidos</small></span><span>{rate(total ? row.orders * 100 / total : 0)} do recorte</span></span>
          </span>
          <span className="ranking-arrow" aria-hidden="true">↗</span>
        </button>
      </li>)}
    </ol>
  </section>
}

function Daily({ rows, onSelect }) {
  if (!rows.length) return <p>Sem cobertura no intervalo.</p>
  const max = Math.max(1, ...rows.map((row) => row.orders))
  return <>
    <div className="chart-frame" aria-label="Gráfico de volume diário; use Tab para consultar cada dia">
      <div className="chart-scale"><span>{max}</span><span>0</span></div>
      <div className="chart">
      {rows.map((row) => <button type="button" onClick={() => onSelect(row.date)} key={row.date} aria-label={day(row.date) + ' · ' + row.orders + ' pedidos'} data-tooltip={day(row.date) + ' · ' + row.orders + ' pedidos'}
        style={{ height: Math.max(2, row.orders * 100 / max) + '%' }} />)}
    </div>
    </div>
    <p className="chart-label"><span>{day(rows[0].date)}</span><span>{day(rows.at(-1).date)}</span></p>
    <p className="legend"><i /> Pedidos por dia · selecione uma barra para detalhar o dia</p><details><summary>Consultar valores diários</summary>
      <table><thead><tr><th scope="col">Data</th><th scope="col">Pedidos</th></tr></thead>
        <tbody>{rows.map((row) => <tr key={row.date}><th scope="row">{day(row.date)}</th><td>{row.orders}</td></tr>)}</tbody>
      </table>
    </details>
  </>
}

function Dashboard({ data, onFilter, applied, busy = false, error, retry, version }) {
  const { coverage, period, summary, previous } = data
  const [invalid, setInvalid] = useState(false)
  const metrics = [
    ['Pedidos', number.format(summary.orders), applied.get('status') ? statuses[applied.get('status')] : 'Todos os status'],
    ['Valor dos pedidos', money.format(summary.value), 'Soma registrada no recorte ativo'],
    ['Valor médio', summary.average == null ? '—' : money.format(summary.average), 'Valor registrado ÷ total de pedidos'],
    ['Cancelamento', rate(summary.cancellation), 'Cancelados ÷ total de pedidos'],
    ['Atraso', rate(summary.late), 'Em atraso ÷ total de pedidos'],
  ]

  function update(key, value) {
    const next = new URLSearchParams(applied)
    if (period) {
      if (!next.has('start')) next.set('start', period.start)
      if (!next.has('end')) next.set('end', period.end)
    }
    if (value) next.set(key, value)
    else next.delete(key)
    const span = (Date.parse(next.get('end')) - Date.parse(next.get('start'))) / 86400000 + 1
    setInvalid(!(span >= 1 && span <= 366))
    onFilter(next.toString())
  }
  function drill(key, value) {
    update(key, applied.get(key) === value ? '' : value)
  }
  const start = applied.get('start') || period?.start || ''
  const end = applied.get('end') || period?.end || ''
  const span = (Date.parse(end) - Date.parse(start)) / 86400000 + 1
  const valid = !period || (span >= 1 && span <= 366)
  const exportParams = new URLSearchParams(applied)
  if (period) { exportParams.set('start', start); exportParams.set('end', end) }
  const context = data.status_context || summary
  return <>
    <p className="intro">{coverage ? 'Base de ' + day(coverage.start) + ' a ' + day(coverage.end) : 'A base ainda não contém pedidos.'}</p>
    {coverage && <div className="filters" aria-label="Filtros automáticos">
      <label>De<input type="date" name="start" min={coverage.start} max={coverage.end}
        value={start} onInput={e => update('start', e.currentTarget.value)} onChange={e => update('start', e.target.value)} required /></label>
      <label>Até<input type="date" name="end" min={coverage.start} max={coverage.end}
        value={end} onInput={e => update('end', e.currentTarget.value)} onChange={e => update('end', e.target.value)} required /></label>
      <label>Região<select name="region" value={applied.get('region') || ''} onChange={e => update('region', e.target.value)}>
        <option value="">Todas</option>{data.filters.regions.map(value => <option key={value}>{value}</option>)}
      </select></label>
      <label>Categoria<select name="category" value={applied.get('category') || ''} onChange={e => update('category', e.target.value)}>
        <option value="">Todas</option>{data.filters.categories.map(value => <option key={value}>{value}</option>)}
      </select></label>
      <button type="button" onClick={() => { setInvalid(false); onFilter('') }}>Limpar filtros</button>

    </div>}
    <div className="filter-chips" aria-label="Seleções ativas">{['region', 'category', 'status'].filter(key => applied.has(key)).map(key =>
      <button key={key} onClick={() => update(key, '')} aria-label={'Remover filtro ' + (statuses[applied.get(key)] || applied.get(key))}>{statuses[applied.get(key)] || applied.get(key)} ×</button>
    )}</div>
    {(!valid || invalid) && <p role="alert">Escolha um intervalo de 1 a 366 dias. Ajuste as datas para atualizar o painel e a exportação.</p>}
    <div className="update-indicator" role="status" aria-live="polite">{valid && busy ? 'Atualizando indicadores…' : ''}</div>
    {valid && !busy && error && <p className="error-state" role="alert">{error} <button onClick={retry}>Tentar novamente</button></p>}
    <div className="dashboard-results" aria-busy={busy} data-updating={busy || !valid || !!error}>

    <dl className="metrics">{metrics.map(([name, value, detail]) => <div key={name}>
      <dt>{name}</dt><dd>{value}</dd><small>{detail}</small>
    </div>)}</dl>
    {summary.orders === 0 && <p role="status">Nenhum pedido para este recorte.</p>}
    <div className="columns">
      <section className="report-section"><h2>Ritmo de pedidos</h2>
        <p>{previous ? 'Janela anterior de mesma duração · ' + number.format(previous.orders) +
          ' pedidos · diferença de ' + delta.format(summary.orders - previous.orders) :
          'A base não cobre integralmente as duas janelas para comparação.'}</p>
        <Daily rows={data.daily} onSelect={date => {
          const next = new URLSearchParams(applied)
          next.set('start', date); next.set('end', date); onFilter(next.toString())
        }} />
      </section>
      <section className="report-section"><h2>Status dos pedidos</h2>

        <ul className="status-list">{Object.entries(context.status).map(([key, value]) => <li key={key}>
          <button className="status-select" aria-pressed={applied.get('status') === key} onClick={() => drill('status', key)}>
            <span>{statuses[key]}</span><strong>{number.format(value)}</strong>
            <span className="status-track" aria-hidden="true"><span style={{width: `${value * 100 / (context.orders || 1)}%`}} /></span>
          </button>
        </li>)}</ul>
        {applied.has('status') && <button onClick={() => update('status', '')}>Mostrar todos os status</button>}
      </section>
    </div>
    {previous && <section className="report-section comparison">
      <h2>Comparação com a janela anterior</h2>
      <table><thead><tr><th scope="col">Indicador</th><th scope="col">Anterior</th><th scope="col">Atual</th></tr></thead>
        <tbody>{[
          ['Pedidos', number.format(previous.orders), number.format(summary.orders)],
          ['Valor dos pedidos', money.format(previous.value), money.format(summary.value)],
          ['Cancelamento', rate(previous.cancellation), rate(summary.cancellation)],
          ['Atraso', rate(previous.late), rate(summary.late)],
        ].map(([label, before, now]) => <tr key={label}><th scope="row">{label}</th><td>{before}</td><td>{now}</td></tr>)}</tbody>
      </table>
    </section>}
    {summary.orders > 0 && <div className="columns rankings">
      <Ranking title="Ranking por região" rows={data.regions} onSelect={v => drill('region', v)} /><Ranking title="Ranking por categoria" rows={data.categories} onSelect={v => drill('category', v)} />
    </div>}
    <ReportExport query={exportParams.toString()} revision={version} blocked={busy || !valid || invalid || !!error} />
    </div>
  </>
}

function ReportExport({ query, revision, blocked }) {
  const [version, setVersion] = useState(0)
  return <section className="export report-section">
    <DataView retain path={'/reports/operations?' + query + '&refresh=' + revision + '-' + version}>
      {(report, state) => <OperationsReport report={report} loading={blocked || state.busy} error={state.error} refresh={() => setVersion(version + 1)} />}
    </DataView>
  </section>
}

function Monitor({ runs }) {
  const [status, setStatus] = useState('all')
  const latest = runs.find(run => run.report)?.report
  const visible = runs.filter(run => status === 'all' || run.status === status)
  return <>
    <div className="notice">Monitor automático · histórico persistido pela API, acionado pelo n8n. A agenda e a duração das execuções não são informadas por esta API. Exportação operacional disponível no Dashboard.</div>
    <dl className="metrics monitor-metrics">{[
      ['Execuções registradas', runs.length],
      ['Concluídas', runs.filter(r => r.status === 'completed').length],
      ['Falhas', runs.filter(r => r.status === 'failed').length],
      ['Alertas na última análise', latest?.alerts.length ?? '—'],
    ].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd><small>Nos últimos 20 registros disponíveis</small></div>)}</dl>
    {latest && <section className="report-section"><h2>Última análise operacional</h2>
      <p>Janela de 14 dias até o último pedido da base · {day(latest.period?.start)} a {day(latest.period?.end)}</p>
      <dl className="metrics monitor-metrics">{[
        ['Volume', number.format(latest.metrics.orders)], ['Valor dos pedidos', money.format(latest.metrics.value)],
        ['Cancelamento', rate(latest.metrics.cancellation)], ['Atraso', rate(latest.metrics.late)],
      ].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
      <p>{latest.summary} · Método: {latest.method}</p>
    </section>}
    <div className="columns monitor-columns">
      <section className="report-section"><div className="section-heading"><h2>Histórico de execuções</h2>
        <label>Status <select value={status} onChange={e => setStatus(e.target.value)}><option value="all">Todos</option><option value="completed">Concluídas</option><option value="failed">Falhas</option></select></label></div>
        {!visible.length && <p role="status">Nenhuma execução para este filtro.</p>}
        {visible.map(run => <details key={run.id} className="run">
          <summary><span className={'badge ' + run.status}>{run.status === 'completed' ? 'Concluída' : 'Falha'}</span> #{run.id} · {new Date(run.finished_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })}</summary>
          {run.report ? <><p>{day(run.report.period?.start)} a {day(run.report.period?.end)} · {run.report.metrics.orders} pedidos</p>
            <p>{run.report.summary} · {run.report.method}</p>
            {run.report.alerts.length ? <ul>{run.report.alerts.map(alert => <li key={alert.label}><strong>{alert.label}</strong> · {rate(alert.value)} · limiar {rate(alert.threshold)} · amostra {alert.sample} pedidos</li>)}</ul> : <p>Nenhuma regra atingiu o limiar.</p>}
            <p>{run.report.notification_candidate ? 'Candidato a prévia de notificação; não confirma envio externo.' : 'Sem prévia de notificação selecionada.'}</p>
            <details><summary>Inspecionar relatório registrado</summary><pre className="report-preview">{JSON.stringify(run.report, null, 2)}</pre></details>
          </> : <p>A análise falhou. Consulte a execução no n8n; atualizar esta tela apenas relê o histórico.</p>}
        </details>)}
      </section>
      <section className="report-section"><h2>Regras e alertas</h2><p>Regras determinísticas aplicadas pelo backend.</p>
        <ul className="rules"><li><strong>Cancelamento ≥ 10%</strong><span>Mínimo de 30 pedidos na janela atual</span></li><li><strong>Atraso ≥ 15%</strong><span>Mínimo de 30 pedidos na janela atual</span></li><li><strong>Queda de volume ≥ 30%</strong><span>Janela anterior comparável com ao menos 30 pedidos</span></li></ul>

      </section>
    </div>
  </>
}

const pages = { dashboard: 'Painel operacional', automations: 'Monitoramento' }

function FloatingChat() {
  const [open, setOpen] = useState(false)
  const trigger = useRef(null)
  return <aside className="chat-widget" aria-label="Assistente de IA">
    <div id="floating-chat" hidden={!open} onKeyDown={event => {
      if (event.key === 'Escape') { setOpen(false); trigger.current?.focus() }
    }}><ChatPanel onClose={() => { setOpen(false); trigger.current?.focus() }} active={open} /></div>
    <button ref={trigger} className="chat-launcher" aria-expanded={open} aria-controls="floating-chat" onClick={() => setOpen(!open)}>{open ? 'Recolher conversa' : '✦ Conversar com IA'}</button>
  </aside>
}

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [query, setQuery] = useState('')
  const [reset, setReset] = useState(0)
  return <>
    <a className="skip-link" href="#main">Ir para o conteúdo</a>
    <header className="masthead">
      <div className="brand"><span className="brand-icon">◈</span><div><strong>Inteligência operacional</strong></div></div>
      <nav aria-label="Menu principal">{Object.entries(pages).map(([key, label]) =>
        <button key={key} onClick={() => setPage(key)} aria-current={page === key ? 'page' : undefined}>{label}</button>)}</nav>
    </header>
    <main id="main">
      <div className="page-heading"><div><p className="eyebrow">INTELIGÊNCIA OPERACIONAL</p><h1>{pages[page]}</h1><p className="subtitle">{page === 'dashboard' ? 'Explore os indicadores e transforme dados em decisões.' : 'Acompanhe análises, execuções e sinais de atenção.'}</p></div>
        <button onClick={() => setReset(reset + 1)}>↻ Atualizar {page === 'dashboard' ? 'indicadores' : 'histórico'}</button></div>
      {page === 'dashboard' && <DataView retain path={'/operations/dashboard' + (query ? '?' + query : '') + (query ? '&' : '?') + 'refresh=' + reset}>
        {(data, state) => <Dashboard data={data} applied={new URLSearchParams(query)} onFilter={setQuery} version={reset} {...state} />}
      </DataView>}
      {page === 'automations' && <DataView key={'monitor' + reset} path="/operations/monitor/runs">{({ runs }) => <Monitor runs={runs} />}</DataView>}

    </main>
    <FloatingChat />
  </>
}
