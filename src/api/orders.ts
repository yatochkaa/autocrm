import api from './client'
import type { Order, OrdersPage, OrderFilters, OrderStatus } from '../types'

// Получить список заявок с фильтрами и пагинацией
export async function getOrders(filters: OrderFilters): Promise<OrdersPage> {
  const params: Record<string, string | number> = {
    page: filters.page,
    size: filters.size,
  }
  if (filters.status) params.status = filters.status
  if (filters.source) params.source = filters.source
  if (filters.manager_id) params.manager_id = filters.manager_id
  const { data } = await api.get<OrdersPage>('/orders', { params })
  return data
}

// Получить одну заявку по ID
export async function getOrder(id: number): Promise<Order> {
  const { data } = await api.get<Order>(`/orders/${id}`)
  return data
}

// Создать заявку
export async function createOrder(payload: Partial<Order>): Promise<Order> {
  const { data } = await api.post<Order>('/orders', payload)
  return data
}

// Обновить заявку (любые поля)
export async function updateOrder(id: number, payload: Partial<Order>): Promise<Order> {
  const { data } = await api.patch<Order>(`/orders/${id}`, payload)
  return data
}

// Изменить статус — отдельный endpoint (PATCH /orders/{id}/status)
export async function updateOrderStatus(id: number, status: OrderStatus): Promise<Order> {
  const { data } = await api.patch<Order>(`/orders/${id}/status`, { status })
  return data
}

// Удалить заявку
export async function deleteOrder(id: number): Promise<void> {
  await api.delete(`/orders/${id}`)
}
