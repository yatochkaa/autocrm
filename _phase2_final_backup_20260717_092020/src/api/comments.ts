// src/api/comments.ts  — NEW FILE (Phase 2).
import api from './client'
import type { Comment } from '../types'

export async function getComments(leadId: number): Promise<Comment[]> {
  const res = await api.get<Comment[]>(`/leads/${leadId}/comments`)
  return res.data
}

export async function addComment(leadId: number, text: string): Promise<Comment> {
  const res = await api.post<Comment>(`/leads/${leadId}/comments`, { text })
  return res.data
}

export async function editComment(leadId: number, commentId: number, text: string): Promise<Comment> {
  const res = await api.patch<Comment>(`/leads/${leadId}/comments/${commentId}`, { text })
  return res.data
}

export async function deleteComment(leadId: number, commentId: number): Promise<void> {
  await api.delete(`/leads/${leadId}/comments/${commentId}`)
}
