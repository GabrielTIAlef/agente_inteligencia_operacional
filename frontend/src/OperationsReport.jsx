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
      <h2>Relatório operacional</h2>
      <p>Prévia de todo o histórico de pedidos. Revise os dados antes de exportar uma cópia local.</p>
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
