// src/types/index.ts  — FULL REPLACEMENT (Phase 2).
// Добавлены: LeadPriority, priority/rejection_reason в Lead,
// PaginatedLeads, Comment, AuditLogEntry, priority в LeadFilters.
// Всё остальное сохранено.

export type LeadStatus = 'new' | 'in_progress' | 'selection' | 'invoice' | 'won' | 'lost'
export type LeadSource = 'telegram' | 'manual' | 'site'
export type LeadPriority = 'low' | 'normal' | 'high' | 'urgent'  // NEW

export interface User {
  id: number
  email: string
  role: string
}

export interface LeadItem {
  id: number
  lead_id: number
  name: string
  oem: string | null
  brand: string | null
  price: number | null
  purchase_price: number | null
  qty: number
  is_analog: boolean
  line_total: number
  line_margin: number | null
}

export interface LeadItemsSummary {
  items: LeadItem[]
  original_items: LeadItem[]
  analog_items: LeadItem[]
  original_total: number
  analog_total: number
  total_amount: number
  total_margin: number | null
}

export interface Lead {
  id: number
  name: string
  phone: string | null
  source: LeadSource
  vin: string | null
  car_info: string | null
  manager_id: number | null
  status: LeadStatus
  priority: LeadPriority        // NEW
  rejection_reason: string | null  // NEW
  items: LeadItem[]
  original_total: number
  analog_total: number
  total_amount: number
  total_margin: number | null
  created_at: string
  updated_at: string
  history?: StatusHistoryEntry[]
}

export interface StatusHistoryEntry {  // NEW
  id: number
  lead_id: number
  from_status: string | null
  to_status: string
  changed_by: number | null
  changed_at: string | null
}

export interface PaginatedLeads {  // NEW
  items: Lead[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface Comment {  // NEW
  id: number
  lead_id: number
  author_id: number | null
  text: string
  created_at: string
  updated_at: string | null
}

export interface AuditLogEntry {  // NEW
  id: number
  lead_id: number | null
  actor_id: number | null
  action: string
  field: string | null
  old_value: string | null
  new_value: string | null
  meta: string | null
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

// ---- Dashboard: nested structure as returned by GET /analytics/dashboard ----

export interface DashboardPeriod {
  date_from: string
  date_to: string
}

export interface DashboardOverview {
  period: DashboardPeriod
  total_leads: number
  sales: number
  conversion_percent: number
  revenue: number
  average_check: number
}

export interface DashboardSourceItem {
  source: LeadSource
  leads: number
  share_percent: number
}

export interface DashboardSources {
  period: DashboardPeriod
  items: DashboardSourceItem[]
  labels: string[]
  values: number[]
}

export interface DashboardManagerItem {
  manager_id: number
  email: string
  sales: number
  revenue: number
}

export interface DashboardManagers {
  period: DashboardPeriod
  items: DashboardManagerItem[]
  labels: string[]
  sales_values: number[]
  revenue_values: number[]
}

export interface DashboardStageTimeItem {
  stage: LeadStatus
  sample_count: number
  average_seconds: number
  median_seconds: number
  average_hours: number
}

export interface DashboardStageTimes {
  period: DashboardPeriod
  items: DashboardStageTimeItem[]
  labels: string[]
  values_hours: number[]
}

export interface DashboardStats {
  overview: DashboardOverview
  sources: DashboardSources
  managers: DashboardManagers
  stage_times: DashboardStageTimes
}

// Lead list filters (frontend-only)
export interface LeadFilters {
  status?: LeadStatus | ''
  source?: LeadSource | ''
  manager_id?: number | ''
  priority?: LeadPriority | ''   // NEW
  search?: string                 // NEW
  page?: number                   // NEW
  limit?: number                  // NEW
  include_completed?: boolean
  sort?: 'created_at' | 'updated_at' | 'priority' | 'status' | 'name' | 'total_amount'
  order?: 'asc' | 'desc'
}


export interface RuntimeSettings {
  auto_priority_enabled: boolean
  normal_after_minutes: number
  high_after_minutes: number
  urgent_after_minutes: number
}

export interface UserSummary extends User {
  username: string
  full_name: string
  total_leads: number
  active_leads: number
}

export interface ManagerAccountPayload {
  full_name: string
  username: string
  password?: string
}
