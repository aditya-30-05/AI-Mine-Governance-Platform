import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach auth token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-logout on 401 (skip for login attempts to avoid reload loops)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const isLoginRequest = err.config?.url?.includes('/auth/login')
    if (err.response?.status === 401 && !isLoginRequest) {
      useAuthStore.getState().logout()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// ─── Auth ──────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
  logout: () => api.post('/auth/logout').then((r) => r.data),
}

// ─── Dashboard ─────────────────────────────────────────
export const dashboardApi = {
  get: (mineId?: string) =>
    api.get('/dashboard', { params: { mine_id: mineId } }).then((r) => r.data),
}

// ─── Mines ─────────────────────────────────────────────
export const minesApi = {
  list: () => api.get('/mines').then((r) => r.data),
  get: (id: string) => api.get(`/mines/${id}`).then((r) => r.data),
}

// ─── Inspections ───────────────────────────────────────
export const inspectionsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/inspections', { params }).then((r) => r.data),
  get: (id: string) => api.get(`/inspections/${id}`).then((r) => r.data),
  create: (data: unknown) => api.post('/inspections', data).then((r) => r.data),
  addObservation: (inspectionId: string, data: unknown) =>
    api.post(`/inspections/${inspectionId}/observations`, data).then((r) => r.data),
  complete: (inspectionId: string) =>
    api.post(`/inspections/${inspectionId}/complete`).then((r) => r.data),
  sync: (data: unknown) => api.post('/inspections/sync', data).then((r) => r.data),
}

// ─── Violations ────────────────────────────────────────
export const violationsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/violations', { params }).then((r) => r.data),
  recurring: (mineId?: string) =>
    api.get('/violations/recurring', { params: { mine_id: mineId } }).then((r) => r.data),
}

// ─── Tasks ─────────────────────────────────────────────
export const tasksApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/tasks', { params }).then((r) => r.data),
  get: (id: string) => api.get(`/tasks/${id}`).then((r) => r.data),
  assign: (id: string, assigneeId: string) =>
    api.patch(`/tasks/${id}/assign`, { assignee_id: assigneeId }).then((r) => r.data),
  escalate: (id: string, escalateToId: string, note: string) =>
    api.post(`/tasks/${id}/escalate`, { escalate_to_id: escalateToId, note }).then((r) => r.data),
  resolve: (id: string, note: string) =>
    api.post(`/tasks/${id}/resolve`, { resolution_note: note }).then((r) => r.data),
  verify: (id: string, note: string, approved: boolean) =>
    api.post(`/tasks/${id}/verify`, { verification_note: note, approved }).then((r) => r.data),
}

// ─── AI ────────────────────────────────────────────────
export const aiApi = {
  analyze: (description: string, mineName?: string, zoneName?: string) =>
    api.post('/ai/analyze-observation', { description, mine_name: mineName, zone_name: zoneName }).then((r) => r.data),
}

// ─── Users ─────────────────────────────────────────────
export const usersApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/users', { params }).then((r) => r.data),
}

// ─── Notifications ─────────────────────────────────────
export const notificationsApi = {
  list: (unreadOnly?: boolean) =>
    api.get('/notifications', { params: { unread_only: unreadOnly } }).then((r) => r.data),
  markRead: (id: string) => api.patch(`/notifications/${id}/read`).then((r) => r.data),
  markAllRead: () => api.patch('/notifications/read-all').then((r) => r.data),
}

// ─── Audit ─────────────────────────────────────────────
export const auditApi = {
  get: (entityType: string, entityId: string) =>
    api.get(`/audit/${entityType}/${entityId}`).then((r) => r.data),
  logs: (params?: { entity_type?: string; action?: string; limit?: number; offset?: number }) =>
    api.get('/audit/logs', { params }).then((r) => r.data),
  summary: () => api.get('/audit/ledger-summary').then((r) => r.data),
}

// ─── Documents ─────────────────────────────────────────
export const documentsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/documents', { params }).then((r) => r.data),
  upload: (formData: FormData) =>
    api.post('/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then((r) => r.data),
  runOcr: (id: string) => api.post(`/documents/${id}/ocr`).then((r) => r.data),
}

// ─── Reports ───────────────────────────────────────────
export const reportsApi = {
  generate: (data: unknown) => api.post('/reports/generate', data).then((r) => r.data),
  status: (jobId: string) => api.get(`/reports/${jobId}`).then((r) => r.data),
}
