import { useState, FormEvent } from 'react'
import { login } from '../api/auth'
import { friendlyError } from '../api/client'
import './LoginPage.css'

export default function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    if (!email.trim())    { setError('Введите логин'); return }
    if (!password.trim()) { setError('Введите пароль'); return }
    setLoading(true)
    try {
      const data = await login({ email, password })
      localStorage.setItem('access_token', data.access_token)
      window.location.href = '/leads'
    } catch (err) {
      setError(friendlyError(err, 'Неверный логин или пароль'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">🔧</div>
        <h1 className="login-title">AutoCRM</h1>
        <p className="login-subtitle">Вход в систему</p>

        {error && <div className="login-error">{error}</div>}

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="field-label">Логин или email
            <input
              className="field-input"
              type="text"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="username"
              autoFocus
              placeholder="ivanov"
            />
          </label>
          <label className="field-label">Пароль
            <input
              className="field-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              placeholder="••••••••"
            />
          </label>
          <button
            className="btn btn-primary login-btn"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Вхожу...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  )
}
