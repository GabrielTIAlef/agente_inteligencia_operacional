import { useState } from 'react'

const percent = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 })

export function Breakdown({ title, rows, dimension }) {
  return (
    <section className="content-card">
      <h3>{title}</h3>
      {rows.length === 0 ? <p>Nenhum pedido encontrado.</p> : (
        <div className="breakdown-scroll">
          <table className="breakdown-table">
            <thead>
              <tr><th>Grupo</th><th>Pedidos</th><th>Cancelamento</th><th>Atraso</th></tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row[dimension]}>
                  <th scope="row">{row[dimension]}</th>
                  <td>{row.total_pedidos.toLocaleString('pt-BR')}</td>
                  <td>{percent.format(row.taxa_cancelamento)}%</td>
                  <td>{percent.format(row.taxa_atraso)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

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
      <h2>Relatório operacional</h2>
      <p>O n8n consulta a mesma fonte do painel e gera uma prévia de leitura. Revise os dados antes de exportar uma cópia local.</p>
      <button type="button" className="secondary-button" disabled={loading} onClick={refresh}>Atualizar prévia</button>
      {loading && <p role="status">Consultando PostgreSQL…</p>}
      {error && <p role="alert">{error}</p>}
      {report && !loading && !error && (
        <>
          <p>Gerado em {new Date(report.generated_at).toLocaleString('pt-BR')} · Referência {reportId}</p>
          <details>
            <summary>Revisar conteúdo da exportação</summary>
            <pre className="report-preview">{JSON.stringify(report, null, 2)}</pre>
          </details>
          <label className="report-approval">
            <input type="checkbox" checked={approved === reportId} onChange={(event) => setApproved(event.target.checked ? reportId : null)} />
            Aprovo a exportação local desta prévia
          </label>
          <button type="button" className="primary-button" disabled={approved !== reportId} onClick={download}>Baixar relatório JSON</button>
        </>
      )}
    </section>
  )
}
