import { useState } from 'react'

export default function OperationsReport({ report, loading, error, refresh }) {
  const [approved, setApproved] = useState(null)
  const reportId = report?.request_id

  function download() {
    if (!report || loading || error || approved !== reportId) return
    const file = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(file)
    const link = document.createElement('a')
    link.href = url
    link.download = `relatorio-operacional-${reportId}.json`
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    setApproved(null)
  }

  return (
    <section className="content-card">
      <div className="report-toolbar"><div><h2>Relatório operacional</h2><span className="report-scope">EXPORTAÇÃO · RECORTE ATIVO DO DASHBOARD</span></div>
      <button type="button" className="secondary-button" disabled={loading} onClick={refresh}>Atualizar prévia</button></div>
      {report?.scope && <p className="export-scope">{report.scope.period ? `${report.scope.period.start.split('-').reverse().join('/')} a ${report.scope.period.end.split('-').reverse().join('/')}` : 'Sem período disponível'} · {report.scope.region || 'Todas as regiões'} · {report.scope.category || 'Todas as categorias'} · {{entregue:'Entregues',cancelado:'Cancelados',em_atraso:'Em atraso'}[report.scope.status] || 'Todos os status'}</p>}
      <p>1. Revise os indicadores e o JSON · 2. Aprove esta versão · 3. Baixe a cópia local. Esta ação não executa o monitor.</p>
      <p className="report-update-indicator" role="status">{loading ? 'Atualizando prévia; exportação disponível após a atualização.' : ''}</p>
      {error && <p role="alert">{error}</p>}
      {report && (
        <>
          <dl className="export-grid">{[
            ['Pedidos', new Intl.NumberFormat('pt-BR').format(report.summary.total_pedidos)],
            ['Valor dos pedidos', new Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'}).format(report.summary.valor_total)],
            ['Fonte', report.source],
          ].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
          <details><summary>Revisar indicadores por região</summary><table><thead><tr><th>Região</th><th>Pedidos</th><th>Cancelamento</th><th>Atraso</th></tr></thead><tbody>{report.regions.map(r => <tr key={r.regiao}><th scope="row">{r.regiao}</th><td>{r.total_pedidos}</td><td>{r.taxa_cancelamento}%</td><td>{r.taxa_atraso}%</td></tr>)}</tbody></table></details>
          <p>Gerado em {new Date(report.generated_at).toLocaleString('pt-BR')} · Referência {reportId}</p>
          <details>
            <summary>Revisar conteúdo da exportação</summary>
            <pre className="report-preview">{JSON.stringify(report, null, 2)}</pre>
          </details>
          <label className="report-approval">
            <input type="checkbox" disabled={loading || !!error} checked={!loading && !error && approved === reportId} onChange={(event) => setApproved(event.target.checked ? reportId : null)} />
            Aprovo a exportação local desta prévia
          </label>
          <button type="button" className="primary-button" disabled={loading || !!error || approved !== reportId} onClick={download}>Baixar relatório JSON</button>
        </>
      )}
    </section>
  )
}
