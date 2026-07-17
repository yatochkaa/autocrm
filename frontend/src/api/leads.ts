import api from './client'
import type { Lead, LeadFilters, LeadStatus, LeadItem, LeadItemsSummary } from '../types'

// GET /leads
export async function getLeads(filters: LeadFilters = {}): Promise<Lead[]> {
  const params: Record<string, string | number> = {}
  if (filters.status)     params.status     = filters.status
  if (filters.source)     params.source     = filters.source
  if (filters.manager_id) params.manager_id = filters.manager_id
  const { data } = await api.get<Lead[]>('/leads', { params })
  return data
}

// GET /leads/{id}
export async function getLead(id: number): Promise<Lead> {
  const { data } = await api.get<Lead>(`/leads/${id}`)
  return data
}

// POST /leads — sends only allowed fields, no computed/status fields
export async function createLead(payload: {
  name: string
  phone: string | null
  vin: string | null
  car_info: string | null
  source: string
}): Promise<Lead> {
  const { data } = await api.post<Lead>('/leads', payload)
  return data
}

// PATCH /leads/{id}
export async function updateLead(id: number, payload: Partial<Lead>): Promise<Lead> {
  const { data } = await api.patch<Lead>(`/leads/${id}`, payload)
  return data
}

// PATCH /leads/{id}/status
export async function updateLeadStatus(id: number, status: LeadStatus): Promise<Lead> {
  const { data } = await api.patch<Lead>(`/leads/${id}/status`, { status })
  return data
}

// DELETE /leads/{id}
export async function deleteLead(id: number): Promise<void> {
  await api.delete(`/leads/${id}`)
}

// ---- Items ----

// GET /leads/{leadId}/items — returns { items, original_items, ... }
export async function getLeadItems(leadId: number): Promise<LeadItem[]> {
  const { data } = await api.get<LeadItemsSummary>(`/leads/${leadId}/items`)
  return data.items
}

// POST /leads/{leadId}/items
export async function createLeadItem(
  leadId: number,
  payload: {
    name: string
    oem: string
    brand: string
    qty: number
    price: number
    purchase_price: number
    is_analog: boolean
  },
): Promise<LeadItem> {
  const { data } = await api.post<LeadItem>(`/leads/${leadId}/items`, payload)
  return data
}

// PATCH /leads/{leadId}/items/{itemId}
export async function updateLeadItem(
  leadId: number,
  itemId: number,
  payload: Partial<LeadItem>,
): Promise<LeadItem> {
  const { data } = await api.patch<LeadItem>(`/leads/${leadId}/items/${itemId}`, payload)
  return data
}

// DELETE /leads/{leadId}/items/{itemId}
export async function deleteLeadItem(leadId: number, itemId: number): Promise<void> {
  await api.delete(`/leads/${leadId}/items/${itemId}`)
}
