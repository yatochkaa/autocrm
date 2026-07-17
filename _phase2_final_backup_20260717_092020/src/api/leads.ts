// src/api/leads.ts  — FULL REPLACEMENT (Phase 2).
// axios-паттерн сохранён. getLeads возвращает PaginatedLeads.
// changeLeadStatus(rejection_reason), getLeadHistory, getLeadAudit — новые.
import api from './client'
import type {
  Lead, LeadFilters, LeadStatus, LeadItem, LeadItemsSummary,
  PaginatedLeads, StatusHistoryEntry, AuditLogEntry,
} from '../types'

// ── Leads ──
export async function getLeads(filters: LeadFilters = {}): Promise<PaginatedLeads> {
  const params: Record<string, string | number | boolean> = {}
  if (filters.status)     params.status     = filters.status
  if (filters.source)     params.source     = filters.source
  if (filters.manager_id) params.manager_id = filters.manager_id
  if (filters.priority)   params.priority   = filters.priority
  if (filters.search)     params.search     = filters.search
  if (filters.page)       params.page       = filters.page
  if (filters.limit)      params.limit      = filters.limit
  if (filters.include_completed !== undefined) params.include_completed = filters.include_completed
  if (filters.sort)       params.sort       = filters.sort
  if (filters.order)      params.order      = filters.order
  const res = await api.get<PaginatedLeads>('/leads', { params })
  return res.data
}

export async function getLead(id: number): Promise<Lead> {
  const res = await api.get<Lead>(`/leads/${id}`)
  return res.data
}

export async function createLead(data: Partial<Lead>): Promise<Lead> {
  const res = await api.post<Lead>('/leads', data)
  return res.data
}

export async function updateLead(id: number, data: Partial<Lead>): Promise<Lead> {
  const res = await api.patch<Lead>(`/leads/${id}`, data)
  return res.data
}

export async function changeLeadStatus(
  id: number,
  status: LeadStatus,
  rejection_reason?: string,
): Promise<Lead> {
  const res = await api.patch<Lead>(`/leads/${id}/status`, { status, rejection_reason })
  return res.data
}

/** @deprecated используй changeLeadStatus */
export async function updateLeadStatus(id: number, status: LeadStatus): Promise<Lead> {
  return changeLeadStatus(id, status)
}

export async function deleteLead(id: number): Promise<void> {
  await api.delete(`/leads/${id}`)
}

export async function getLeadHistory(id: number): Promise<StatusHistoryEntry[]> {
  const res = await api.get<StatusHistoryEntry[]>(`/leads/${id}/history`)
  return res.data
}

export async function getLeadAudit(id: number): Promise<AuditLogEntry[]> {
  const res = await api.get<AuditLogEntry[]>(`/leads/${id}/audit`)
  return res.data
}

// ── Items (остаются в order_items.py) ──
export async function getLeadItems(leadId: number): Promise<LeadItem[]> {
  const res = await api.get<LeadItemsSummary>(`/leads/${leadId}/items`)
  return res.data.items
}

export async function createLeadItem(leadId: number, data: Partial<LeadItem>): Promise<LeadItem> {
  const res = await api.post<LeadItem>(`/leads/${leadId}/items`, data)
  return res.data
}

export async function updateLeadItem(leadId: number, itemId: number, data: Partial<LeadItem>): Promise<LeadItem> {
  const res = await api.patch<LeadItem>(`/leads/${leadId}/items/${itemId}`, data)
  return res.data
}

export async function deleteLeadItem(leadId: number, itemId: number): Promise<void> {
  await api.delete(`/leads/${leadId}/items/${itemId}`)
}
