import type { Toast, ToastType } from '../hooks/useToast'
import './Toast.css'

const ICONS: Record<ToastType, string> = {
  success: '✔️',
  error:   '❌',
  info:    'ℹ️',
  warning: '⚠️',
}

export function ToastContainer({ toasts, onRemove }: {
  toasts: Toast[]
  onRemove: (id: number) => void
}) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span className="toast-icon">{ICONS[t.type]}</span>
          <span className="toast-msg">{t.message}</span>
          <button className="toast-close" onClick={() => onRemove(t.id)}>×</button>
        </div>
      ))}
    </div>
  )
}
