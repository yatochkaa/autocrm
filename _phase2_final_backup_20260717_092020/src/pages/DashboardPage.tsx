import { useState, useEffect, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { getDashboardStats, defaultDateRange } from '../api/dashboard'
import type { DashboardStats, LeadSource, LeadStatus } from '../types'
import { STATUS_LABELS, SOURCE_LABELS } from '../utils/constants'
import { formatRub, formatPercent, toISO, startOfMonth, endOfMonth, startOfQuarter } from '../utils/format'
import { buildDashboardCsv, downloadCsv } from '../utils/csv'
import { useToast } from '../hooks/useToast'
import { ToastContainer } from '../components/Toast'
import './DashboardPage.css'

const PIE_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']

function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: string }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={accent ? { color: accent } : {}}>{value}</div>
    </div>
  )
}

const PRESETS = [
  { label: '7 days', days: 7 },
  { label: '30 days', days: 30 },
  { label: 'This month', days: 0, mode: 'month' as const },
  { label: 'This quarter', days: 0, mode: 'quarter' as const },
]

function getPresetRange(p: typeof PRESETS[number]): { date_from: string; date_to: string } {
  const today = new Date()
  if (p.mode === 'month') return { date_from: toISO(startOfMonth(today)), date_to: toISO(endOfMonth(today)) }
  if (p.mode === 'quarter') return { date_from: toISO(startOfQuarter(today)), date_to: toISO(today) }
  const from = new Date(today)
  from.setDate(from.getDate() - p.days)
  return { date_from: toISO(from), date_to: toISO(today) }
}

export default function DashboardPage() {
  const { toasts, toast, removeToast } = useToast()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  const def = defaultDateRange()
  const [dateFrom, setDateFrom] = useState(def.date_from)
  const [dateTo, setDateTo]     = useState(def.date_to)

  const load = useCallback((from: string, to: string) => {
    setLoading(true)
    getDashboardStats(from, to, 10)
      .then(setStats)
      .catch(() => toast.error('Ne udalos zagruzit analitiku'))
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => { load(dateFrom, dateTo) }, [])

  const applyRange = () => load(dateFrom, dateTo)

  const applyPreset = (p: typeof PRESETS[number]) => {
    const r = getPresetRange(p)
    setDateFrom(r.date_from)
    setDateTo(r.date_to)
    load(r.date_from, r.date_to)
  }

  const handleCsv = () => {
    if (!stats) return
    const csv = buildDashboardCsv(stats, dateFrom, dateTo)
    downloadCsv(`dashboard_${dateFrom}_${dateTo}.csv`, csv)
  }

  const handlePrint = () => window.print()

  const toggleTheme = () => {
    const el = document.documentElement
    el.dataset.theme = el.dataset.theme === 'dark' ? '' : 'dark'
    localStorage.setItem('theme', el.dataset.theme)
  }

  if (!stats && loading) return <div className="dash-loading">Zagruzka...</div>

  const ov = stats?.overview
  const srcItems = stats?.sources.items ?? []
  const mgrItems = stats?.managers.items ?? []
  const stgItems = stats?.stage_times.items ?? []

  const sourceChartData = srcItems.map((s: { source: LeadSource; leads: number; share_percent: number }) => ({
    name: SOURCE_LABELS[s.source] ?? s.source,
    value: s.leads,
    share: s.share_percent,
  }))

  const managerChartData = mgrItems.map((m: { email: string; sales: number; revenue: number }) => ({
    name: m.email.split('@')[0],
    sales: m.sales,
    revenue: m.revenue,
  }))

  const stageChartData = stgItems.map((s: { stage: LeadStatus; average_hours: number; sample_count: number }) => ({
    name: STATUS_LABELS[s.stage] ?? s.stage,
    hours: parseFloat(s.average_hours.toFixed(2)),
    count: s.sample_count,
  }))

  return (
    <div className="dash-page">
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <div className="dash-toolbar">
          <button className="btn" onClick={handleCsv} disabled={!stats}>CSV</button>
          <button className="btn" onClick={handlePrint}>Print</button>
          <button className="btn" onClick={toggleTheme}>Theme</button>
        </div>
      </div>

      {/* Period picker */}
      <div className="card dash-period">
        <div className="dash-presets">
          {PRESETS.map(p => (
            <button key={p.label} className="btn btn-sm" onClick={() => applyPreset(p)}>{p.label}</button>
          ))}
        </div>
        <div className="dash-range">
          <input type="date" className="field-input" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
          <span>-</span>
          <input type="date" className="field-input" value={dateTo} onChange={e => setDateTo(e.target.value)} />
          <button className="btn btn-primary" onClick={applyRange} disabled={loading}>Apply</button>
        </div>
      </div>

      {loading && <div className="dash-loading">Zagruzka...</div>}

      {ov && (
        <>
          {/* Overview cards */}
          <div className="stat-grid">
            <StatCard label="Vsego zayavok"  value={ov.total_leads} />
            <StatCard label="Prodazhi"        value={ov.sales}       accent="#10b981" />
            <StatCard label="Konversiya"      value={formatPercent(ov.conversion_percent)} accent="#3b82f6" />
            <StatCard label="Vyruchka"        value={formatRub(ov.revenue)}        accent="#3b82f6" />
            <StatCard label="Sredniy chek"    value={formatRub(ov.average_check)}  accent="#8b5cf6" />
          </div>

          {/* Sources pie */}
          {sourceChartData.length > 0 && (
            <div className="card">
              <h2 className="section-title">Istochniki zayavok</h2>
              <div className="chart-row">
                <ResponsiveContainer width="50%" height={240}>
                  <PieChart>
                    <Pie data={sourceChartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, share }: { name: string; share: number }) => `${name}: ${share.toFixed(1)}%`}>
                      {sourceChartData.map((_: unknown, i: number) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                    </Pie>
                    <Legend />
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <table className="data-table" style={{ flex: 1 }}>
                  <thead><tr><th>Istochnik</th><th>Zayavok</th><th>Dolya, %</th></tr></thead>
                  <tbody>
                    {srcItems.map((s: { source: LeadSource; leads: number; share_percent: number }) => (
                      <tr key={s.source}>
                        <td>{SOURCE_LABELS[s.source] ?? s.source}</td>
                        <td>{s.leads}</td>
                        <td>{s.share_percent.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Managers bar */}
          {managerChartData.length > 0 && (
            <div className="card">
              <h2 className="section-title">Menedzhery</h2>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={managerChartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="sales" name="Prodazhi" fill="#3b82f6" />
                  <Bar dataKey="revenue" name="Vyruchka" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
              <table className="data-table" style={{ marginTop: 12 }}>
                <thead><tr><th>Email</th><th>Prodazhi</th><th>Vyruchka</th></tr></thead>
                <tbody>
                  {mgrItems.map((m: { manager_id: number; email: string; sales: number; revenue: number }) => (
                    <tr key={m.manager_id}>
                      <td>{m.email}</td>
                      <td>{m.sales}</td>
                      <td>{formatRub(m.revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Stage times */}
          {stageChartData.length > 0 && (
            <div className="card">
              <h2 className="section-title">Srednee vremya po etapam</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={stageChartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <XAxis dataKey="name" />
                  <YAxis unit=" ch" />
                  <Tooltip formatter={(v: number) => [`${v} ch`, 'Srednee']} />
                  <Bar dataKey="hours" name="Chasov" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
              <table className="data-table" style={{ marginTop: 12 }}>
                <thead><tr><th>Etap</th><th>Vyborka</th><th>Sred. chasov</th></tr></thead>
                <tbody>
                  {stgItems.map((s: { stage: LeadStatus; sample_count: number; average_hours: number }) => (
                    <tr key={s.stage}>
                      <td>{STATUS_LABELS[s.stage] ?? s.stage}</td>
                      <td>{s.sample_count}</td>
                      <td>{s.average_hours.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
