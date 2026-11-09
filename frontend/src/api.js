const baseUrl = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

export function apiUrl(path) {
  return baseUrl + path
}

export function errorWithTrace(response, message) {
  const id = response.headers.get('X-Request-ID')
  return new Error(id ? `${message} Referência: ${id}.` : message)
}

export async function fetchReport(signal) {
  const response = await fetch(apiUrl('/reports/operations'), { signal })
  if (!response.ok) {
    throw errorWithTrace(response, 'Não foi possível consultar o relatório operacional.')
  }
  const report = await response.json()
  if (!report.summary || !report.request_id || !Array.isArray(report.regions) || !Array.isArray(report.categories)) {
    throw new Error('Formato de relatório inesperado.')
  }
  return report
}

