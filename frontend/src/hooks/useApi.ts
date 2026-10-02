import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dashboardApi, violationsApi, tasksApi, inspectionsApi, notificationsApi, minesApi, usersApi, auditApi } from '@/services/api'
import { useAuthStore } from '@/store/authStore'

// ─── Dashboard ────────────────────────────────────────
export function useDashboard() {
  const mineId = useAuthStore((s) => s.selectedMineId)
  return useQuery({
    queryKey: ['dashboard', mineId],
    queryFn: () => dashboardApi.get(mineId ?? undefined),
    refetchInterval: 30_000,
    staleTime: 15_000,
  })
}

// ─── Mines ────────────────────────────────────────────
export function useMines() {
  return useQuery({
    queryKey: ['mines'],
    queryFn: minesApi.list,
    staleTime: 60_000,
  })
}

// ─── Violations ───────────────────────────────────────
export function useViolations(params?: Record<string, unknown>) {
  const mineId = useAuthStore((s) => s.selectedMineId)
  return useQuery({
    queryKey: ['violations', mineId, params],
    queryFn: () => violationsApi.list({ mine_id: mineId, ...params }),
  })
}

export function useRecurringRisks() {
  const mineId = useAuthStore((s) => s.selectedMineId)
  return useQuery({
    queryKey: ['recurring-risks', mineId],
    queryFn: () => violationsApi.recurring(mineId ?? undefined),
    refetchInterval: 60_000,
  })
}

// ─── Tasks ────────────────────────────────────────────
export function useTasks(params?: Record<string, unknown>) {
  const mineId = useAuthStore((s) => s.selectedMineId)
  return useQuery({
    queryKey: ['tasks', mineId, params],
    queryFn: () => tasksApi.list({ mine_id: mineId, ...params }),
  })
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ['task', id],
    queryFn: () => tasksApi.get(id),
    enabled: !!id,
  })
}

export function useAssignTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, assigneeId }: { id: string; assigneeId: string }) =>
      tasksApi.assign(id, assigneeId),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['task', id] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useEscalateTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, escalateToId, note }: { id: string; escalateToId: string; note: string }) =>
      tasksApi.escalate(id, escalateToId, note),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['task', id] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useResolveTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) =>
      tasksApi.resolve(id, note),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['task', id] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useVerifyTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, note, approved }: { id: string; note: string; approved: boolean }) =>
      tasksApi.verify(id, note, approved),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['task', id] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

// ─── Inspections ──────────────────────────────────────
export function useInspections(params?: Record<string, unknown>) {
  const mineId = useAuthStore((s) => s.selectedMineId)
  return useQuery({
    queryKey: ['inspections', mineId, params],
    queryFn: () => inspectionsApi.list({ mine_id: mineId, ...params }),
  })
}

export function useInspection(id: string) {
  return useQuery({
    queryKey: ['inspection', id],
    queryFn: () => inspectionsApi.get(id),
    enabled: !!id,
  })
}

// ─── Notifications ────────────────────────────────────
export function useNotifications() {
  return useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list(),
    refetchInterval: 15_000,
  })
}

export function useMarkNotificationRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })
}

// ─── Users ────────────────────────────────────────────
export function useUsers(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ['users', params],
    queryFn: () => usersApi.list(params),
  })
}

// ─── Audit ────────────────────────────────────────────
export function useAuditTrail(entityType: string, entityId: string) {
  return useQuery({
    queryKey: ['audit', entityType, entityId],
    queryFn: () => auditApi.get(entityType, entityId),
    enabled: !!entityId,
  })
}
