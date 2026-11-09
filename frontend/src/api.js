const baseUrl = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

export function apiUrl(path) {
  return baseUrl + path
}

export function errorWithTrace(response, message) {
  const id = response.headers.get('X-Request-ID')
  return new Error(id ? `${message} Referência: ${id}.` : message)
}
