const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.detail || `Health check failed (${res.status})`)
  }
  return res.json()
}

export async function getMetrics() {
  const res = await fetch(`${API_BASE}/metrics`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.detail || `Metrics fetch failed (${res.status})`)
  }
  return res.json()
}

export async function predict(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.detail || `Prediction failed (${res.status})`)
  }
  return res.json()
}

export async function predictBatch(files) {
  const formData = new FormData()
  files.forEach((f) => formData.append('files', f))
  const res = await fetch(`${API_BASE}/predict-batch`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.detail || `Batch prediction failed (${res.status})`)
  }
  return res.json()
}
