import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access_token')
  if (token && cfg.headers) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// Global 401 handler — do NOT redirect if the request itself is /auth/login
api.interceptors.response.use(
  r => r,
  err => {
    const isLoginRequest = err.config?.url?.includes('/auth/login')
    if (err.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export default api

/** Converts axios error to a user-friendly message */
export function friendlyError(err: unknown, fallback = 'Неизвестная ошибка'): string {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status
    const detail = err.response?.data?.detail
    if (status === 401) return 'Неверный email или пароль'
    if (status === 403) return 'Недостаточно прав доступа'
    if (status === 404) return 'Объект не найден'
    if (status === 409) return detail ?? 'Недопустимый переход статуса'
    if (status === 422) return 'Некорректные данные'
    if (detail) return String(detail)
  }
  return fallback
}
