// src/pages/DashboardPage.tsx — Phase 2 HOTFIX.
// Русские подписи, KPI в адаптивной сетке (stats-grid), графики в карточках (charts-grid),
// период и быстрые кнопки как toolbar, тема через существующий механизм Layout.
// CSV аналитики — через buildDashboardCsv (UTF-8 BOM, sep=;, CRLF).
import { useState, useEffect, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { downloadDashboardExcel, getDashboardStats, defaultDateRange } from '../api/dashboard'
import type { LeadSource, DashboardStats, UserSummary } from '../types'
import { STATUS_LABELS, SOURCE_LABELS } from '../utils/constants'
import { formatRub, formatPercent, toISO, startOfMonth, startOfQuarter } from '../utils/format'
import { useToast } from '../hooks/useToast'
import { getUsers } from '../api/settings'
import { ToastContainer } from '../components/Toast'
import './DashboardPage.css'

const PIE_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']

function StatCard({ label, value, accent, hint }: { label: string; value: string; accent?: string; hint?: string }) {
  return <div className="card stat-card"><div className="stat-label">{label}</div><div className="stat-value" style={accent ? { color: accent } : undefined}>{value}</div>{hint && <div className="stat-hint">{hint}</div>}</div>
}

type Preset = { key: '7d'|'30d'|'month'|'quarter'; label: string; days?: number; mode?: 'month'|'quarter' }
const PRESETS: Preset[] = [
  { key:'7d', label:'Последние 7 дней', days:7 },
  { key:'30d', label:'Последние 30 дней', days:30 },
  { key:'month', label:'Текущий месяц', mode:'month' },
  { key:'quarter', label:'Текущий квартал', mode:'quarter' },
]

function getPresetRange(p: Preset): { from: string; to: string } {
  const today = new Date()
  if (p.mode === 'month') return { from: toISO(startOfMonth(today)), to: toISO(today) }
  if (p.mode === 'quarter') return { from: toISO(startOfQuarter(today)), to: toISO(today) }
  const from = new Date(today)
  from.setDate(today.getDate() - Math.max((p.days ?? 7) - 1, 0))
  return { from: toISO(from), to: toISO(today) }
}

function formatPeriodDate(value: string): string { return new Date(`${value}T12:00:00`).toLocaleDateString('ru-RU') }
function formatDuration(seconds: number): string {
  const minutes=Math.max(0,Math.round(seconds/60))
  if(minutes<60)return `${minutes} мин`
  const hours=Math.floor(minutes/60),rest=minutes%60
  if(hours<24)return rest ? `${hours} ч ${rest} мин` : `${hours} ч`
  const days=Math.floor(hours/24),restHours=hours%24
  return restHours ? `${days} д ${restHours} ч` : `${days} д`
}

export default function DashboardPage() {
  const { toasts, toast, removeToast } = useToast()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [users, setUsers] = useState<UserSummary[]>([])
  const def = defaultDateRange()
  const [dateFrom, setDateFrom] = useState(def.date_from)
  const [dateTo, setDateTo] = useState(def.date_to)
  const [activePreset, setActivePreset] = useState<Preset['key'] | null>('30d')

  const load = useCallback(async (from: string, to: string) => {
    setLoading(true)
    try {
      setStats(await getDashboardStats(from, to))
    } catch {
      toast.error('Не удалось загрузить аналитику')
    } finally { setLoading(false) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(dateFrom, dateTo); getUsers().then(setUsers).catch(() => undefined) }, [])

  const applyRange = () => { setActivePreset(null); load(dateFrom, dateTo) }
  const applyPreset = (p: Preset) => {
    const { from, to } = getPresetRange(p)
    setDateFrom(from); setDateTo(to); setActivePreset(p.key)
    load(from, to)
  }

  const handleExcel = async () => {
    if (!stats) return
    try { await downloadDashboardExcel(dateFrom, dateTo); toast.success('Excel-файл сформирован') }
    catch { toast.error('Не удалось сформировать Excel') }
  }
  const handlePrint = () => window.print()

  if (!stats && loading) return <div className="dash-loading">Загрузка…</div>

  const ov = stats?.overview
  const srcItems = stats?.sources.items ?? []
  const mgrItems = stats?.managers.items ?? []
  const stgItems = stats?.stage_times.items ?? []

  const sourceChartData = srcItems.map((s: { source: LeadSource; leads: number; share_percent: number }) => ({
    name: SOURCE_LABELS[s.source] ?? s.source,
    value: s.leads,
    share: s.share_percent,
  }))
  const managerName = (id: number, email: string) => users.find(user => user.id === id)?.full_name ?? email.split('@')[0]
  const managerChartData = mgrItems.map(m => ({ name: managerName(m.manager_id, m.email), sales: m.sales, revenue: m.revenue }))
  const selectedEnd = new Date(`${dateTo}T12:00:00`)
  const monthStart = toISO(startOfMonth(selectedEnd))
  const quarterStart = toISO(startOfQuarter(selectedEnd))
  const firstMonthOfQuarter = monthStart === quarterStart && (activePreset === 'month' || activePreset === 'quarter')
  const maxStageLog = Math.max(1, ...stgItems.map(item => Math.log1p(item.average_seconds)))

  return (
    <div className="dashboard">
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      <div className="page-header">
        <h1 className="page-title">Дашборд</h1>
        <div className="dash-toolbar no-print">
          <button className="btn" onClick={handleExcel} disabled={!stats}>⬇ Excel</button>
          <button className="btn" onClick={handlePrint}>🖨 Печать</button>
        </div>
      </div>

      {/* Период и быстрые кнопки — единый toolbar */}
      <div className="card dash-controls no-print">
        <div className="dash-presets">
          {PRESETS.map(p => (
            <button key={p.label} className={`btn btn-sm${activePreset === p.key ? ' active-preset' : ''}`} onClick={() => applyPreset(p)}>{p.label}</button>
          ))}
        </div>
        <div className="dash-range">
          <input type="date" className="field-input" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
          <span className="dash-range-sep">—</span>
          <input type="date" className="field-input" value={dateTo} onChange={e => setDateTo(e.target.value)} />
          <button className="btn btn-primary btn-sm" onClick={applyRange}>Применить</button>
        </div>
      </div>

      <div className="card period-explainer">
        <div><b>Период отчёта:</b> {formatPeriodDate(dateFrom)} — {formatPeriodDate(dateTo)}</div>
        <div>«Новые заявки» считаются по дате создания, а «Продажи закрыто» — по дате перехода в статус «Продажа».</div>
        {firstMonthOfQuarter && <div className="period-note">Сейчас первый месяц квартала: месяц и квартал начинаются одной датой, поэтому их показатели могут совпадать.</div>}
      </div>

      {loading && <div className="dash-loading">Загрузка…</div>}

      {ov && (
        <>
          {/* KPI в одну адаптивную сетку */}
          <div className="stats-grid">
            <StatCard label="Новые заявки" value={String(ov.total_leads)} hint="Созданы в выбранном периоде" />
            <StatCard label="Продажи закрыто" value={String(ov.sales)} accent="#10b981" hint="Переведены в «Продажа» за период" />
            <StatCard label="Продажи / новые" value={formatPercent(ov.conversion_percent)} accent="#3b82f6" hint="Отношение закрытых продаж к новым заявкам" />
            <StatCard label="Выручка" value={formatRub(ov.revenue)} accent="#3b82f6" />
            <StatCard label="Средний чек" value={formatRub(ov.average_check)} accent="#8b5cf6" />
          </div>

          {/* Графики — каждый в отдельной карточке */}
          <div className="charts-grid">
            <div className="card chart-card">
              <h2 className="chart-title">Источники заявок</h2>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={sourceChartData}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={80}
                    label={({ name, share }: { name: string; share: number }) => `${name}: ${share.toFixed(1)}%`}
                  >
                    {sourceChartData.map((_: unknown, i: number) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <table className="data-table" style={{ marginTop: 12 }}>
                <thead><tr><th>Источник</th><th>Заявок</th><th>Доля, %</th></tr></thead>
                <tbody>
                  {srcItems.map(s => (
                    <tr key={s.source}>
                      <td>{SOURCE_LABELS[s.source] ?? s.source}</td>
                      <td>{s.leads}</td>
                      <td>{s.share_percent.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card chart-card">
              <h2 className="chart-title">Менеджеры</h2>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={managerChartData}>
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis yAxisId="sales" allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis yAxisId="revenue" orientation="right" tickFormatter={(value: number) => `${Math.round(value / 1000)} тыс.`} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <Tooltip cursor={{ fill: 'rgba(96,165,250,.08)' }} contentStyle={{ background:'#111827', border:'1px solid #374151', borderRadius:8, color:'#f8fafc' }} labelStyle={{ color:'#f8fafc', fontWeight:700 }} formatter={(value: number, name: string) => [name === 'Выручка' ? formatRub(value) : value, name]} />
                  <Legend />
                  <Bar yAxisId="sales" dataKey="sales" name="Продажи" fill="#3b82f6" radius={[4,4,0,0]} />
                  <Bar yAxisId="revenue" dataKey="revenue" name="Выручка" fill="#10b981" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
              <table className="data-table" style={{ marginTop: 12 }}>
                <thead><tr><th>Менеджер</th><th>Продажи</th><th>Выручка</th><th>Средний чек</th></tr></thead>
                <tbody>
                  {mgrItems.map(m => (
                    <tr key={m.manager_id}>
                      <td>{managerName(m.manager_id, m.email)}</td>
                      <td>{m.sales}</td>
                      <td>{formatRub(m.revenue)}</td>
                      <td>{formatRub(m.sales > 0 ? m.revenue / m.sales : 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card chart-card chart-card--wide">
              <h2 className="chart-title">Время прохождения этапов</h2>
              <p className="chart-description">Среднее показывает общую картину, а медиана — типичную заявку без сильного влияния долгих зависших заявок. Учитываются переходы, завершённые в выбранном периоде.</p>
              <div className="stage-metrics">
                {stgItems.map(item => {
                  const label=(STATUS_LABELS as Record<string,string>)[item.stage] ?? item.stage
                  const width=item.sample_count ? Math.max(4,Math.log1p(item.average_seconds)/maxStageLog*100) : 0
                  return <div className="stage-metric" key={item.stage}>
                    <div className="stage-metric-head"><b>{label}</b><span>{item.sample_count} переходов</span></div>
                    <div className="stage-track"><i style={{ width:`${width}%` }}/></div>
                    <div className="stage-values"><span><small>Среднее</small><b>{formatDuration(item.average_seconds)}</b><em>{Math.round(item.average_seconds/60)} мин</em></span><span><small>Медиана</small><b>{formatDuration(item.median_seconds)}</b><em>{Math.round(item.median_seconds/60)} мин</em></span></div>
                    {item.sample_count > 1 && item.median_seconds > 0 && item.average_seconds > item.median_seconds * 3 && <div className="stage-warning">Есть долгие зависшие заявки: они увеличили среднее. Для обычной заявки ориентируйся на медиану.</div>}
                  </div>
                })}
              </div>
              <div className="stage-footnote">Логарифмическая шкала не даёт одному длинному этапу скрыть остальные. Точные значения указаны рядом.</div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
