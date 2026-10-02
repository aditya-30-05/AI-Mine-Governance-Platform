// ─── API Types ─────────────────────────────────────────
export type UserRole = 'admin' | 'field_officer' | 'compliance_officer' | 'mine_manager' | 'corporate_manager'
export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type TaskStatus = 'open' | 'assigned' | 'in_progress' | 'overdue' | 'escalated' | 'resolved' | 'verified' | 'closed'
export type TaskPriority = 'critical' | 'high' | 'medium' | 'low'
export type ViolationCategory =
  | 'PPE' | 'Fire Safety' | 'Electrical Safety' | 'Ventilation'
  | 'Environmental' | 'Equipment' | 'Labour/Worker Safety'
  | 'Documentation' | 'Emergency Preparedness'
export type SyncStatus = 'pending' | 'syncing' | 'synced' | 'failed' | 'conflict'
export type InspectionStatus = 'draft' | 'in_progress' | 'submitted' | 'under_review' | 'completed' | 'synced'

// ─── Auth ───────────────────────────────────────────────
export interface AuthUser {
  user_id: string
  email: string
  full_name: string
  role: UserRole
  mine_id: string | null
  access_token: string
  expires_in: number
}

// ─── Mine ───────────────────────────────────────────────
export interface Mine {
  id: string
  name: string
  code: string
  subsidiary_id: string
  location_name: string | null
  state: string | null
  district: string | null
  latitude: number | null
  longitude: number | null
  mine_type: string | null
  capacity_mtpa: number | null
  is_active: boolean
}

// ─── Dashboard ──────────────────────────────────────────
export interface DashboardKPIs {
  compliance_pct: number
  critical_risks: number
  high_risks: number
  medium_risks: number
  low_risks: number
  overdue_actions: number
  recurring_violations: number
  pending_actions: number
  total_violations: number
  total_inspections: number
}

export interface DashboardData {
  mine_id: string
  generated_at: string
  period_days: number
  kpis: DashboardKPIs
  violations_by_category: Array<{ category: string; count: number }>
  violation_trend: Array<{ date: string; violations: number }>
  task_status_breakdown: Record<string, number>
  recent_inspections: RecentInspection[]
  critical_alerts: CriticalAlert[]
}

export interface RecentInspection {
  id: string
  reference_number: string
  inspection_type: string
  status: InspectionStatus
  created_at: string
  compliance_score: number | null
}

export interface CriticalAlert {
  id: string
  title: string
  status: TaskStatus
  priority: TaskPriority
  due_date: string | null
}

// ─── Inspection ─────────────────────────────────────────
export interface Inspection {
  id: string
  reference_number: string
  mine_id: string
  inspector_id: string
  inspection_type: string
  status: InspectionStatus
  shift: string | null
  start_latitude: number | null
  start_longitude: number | null
  started_at: string | null
  completed_at: string | null
  overall_compliance_score: number | null
  sync_status: SyncStatus | null
  created_at: string
}

// ─── Observation ────────────────────────────────────────
export interface Observation {
  id: string
  inspection_id: string
  description: string
  latitude: number | null
  longitude: number | null
  category: ViolationCategory | null
  photo_urls: string[]
  captured_at: string
  created_at: string
}

// ─── Violation ──────────────────────────────────────────
export interface Violation {
  id: string
  reference_number: string
  mine_id: string
  category: ViolationCategory | null
  severity: SeverityLevel | null
  description: string
  compliance_status: string | null
  is_recurring: boolean
  latitude: number | null
  longitude: number | null
  resolved_at: string | null
  created_at: string
}

// ─── Recurring Risk ─────────────────────────────────────
export interface RecurringRisk {
  id: string
  mine_id: string
  category: ViolationCategory | null
  occurrence_count: number
  first_occurrence: string | null
  last_occurrence: string | null
  time_window_days: number
  severity: SeverityLevel | null
  status: string
  recommended_action: string | null
  trend: string
}

// ─── Task ───────────────────────────────────────────────
export interface Task {
  id: string
  reference_number: string
  mine_id: string
  violation_id: string | null
  title: string
  description: string | null
  category: ViolationCategory | null
  priority: TaskPriority | null
  status: TaskStatus | null
  assignee_id: string | null
  due_date: string | null
  is_overdue: boolean
  escalation_count: number
  resolved_at: string | null
  created_at: string
  history?: TaskHistoryEntry[]
}

export interface TaskHistoryEntry {
  action: string
  old_status: TaskStatus | null
  new_status: TaskStatus | null
  note: string | null
  changed_by_id: string | null
  timestamp: string
}

// ─── AI Analysis ────────────────────────────────────────
export interface AIAnalysisResult {
  category: string
  severity: SeverityLevel
  risk_score: number
  confidence: number
  explanation: string
  recommended_action: string
  is_demo_fallback: boolean
  model_used: string
}

// ─── Notification ────────────────────────────────────────
export interface Notification {
  id: string
  type: string
  title: string
  message: string
  severity: SeverityLevel | null
  entity_type: string | null
  entity_id: string | null
  is_read: boolean
  action_url: string | null
  created_at: string
}

// ─── Offline Queue ───────────────────────────────────────
export interface OfflineInspection {
  clientId: string
  mineId: string
  inspectionType: string
  notes?: string
  shift?: string
  latitude?: number
  longitude?: number
  startedAt: string
  deviceId: string
  syncStatus: SyncStatus
  observations: OfflineObservation[]
  createdAt: string
}

export interface OfflineObservation {
  clientId: string
  description: string
  latitude?: number
  longitude?: number
  category?: string
  photoUrls: string[]
  capturedAt: string
}

// ─── Document ────────────────────────────────────────────
export interface ComplianceDocument {
  id: string
  title: string
  document_type: string | null
  mine_id: string | null
  reference_number: string | null
  compliance_status: string | null
  expiry_date: string | null
  ocr_status: string
  created_at: string
}

// ─── Audit ───────────────────────────────────────────────
export interface AuditEntry {
  id: string
  timestamp: string
  user_id: string | null
  action: string
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown> | null
  record_hash: string
  previous_hash: string | null
}

export interface AuditTrail {
  entity_type: string
  entity_id: string
  integrity: { verified: boolean; chain_length: number; message: string }
  total: number
  entries: AuditEntry[]
}

// ─── Paginated Response ──────────────────────────────────
export interface PaginatedResponse<T> {
  total: number
  items: T[]
}
