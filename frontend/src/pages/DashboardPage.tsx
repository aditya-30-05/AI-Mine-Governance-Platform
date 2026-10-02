import { useEffect, useCallback } from 'react'
import {
  AlertTriangle, CheckSquare, ShieldCheck, TrendingUp, RefreshCw,
  ArrowUpRight, Clock, RotateCcw, ClipboardList, Wifi
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts'
import { useNavigate } from 'react-router-dom'
import { useDashboard } from '@/hooks/useApi'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useQueryClient } from '@tanstack/react-query'
import { getComplianceColor, formatRelative, getSeverityClass, getTaskStatusClass, isOverdue } from '@/utils'
import toast from 'react-hot-toast'
import type { DashboardData, CriticalAlert } from '@/types'

const SEV_COLORS: Record<string, string> = {
  critical: '#dc2626', high: '#ea580c', medium: '#ca8a04', low: '#16a34a'
}

function KPICard({ value, label, color, onClick }: {
  value: number | string; label: string; color?: string; onClick?: () => void
}) {
  return (
    <div className="kpi-card" onClick={onClick}>
      <div className="kpi-value" style={{ color }}>{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  )
}

function SkeletonCard() {
  return <div className="kpi-card"><div className="skeleton h-8 w-16 mb-2" /><div className="skeleton h-3 w-24" /></div>
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { data: dash, isLoading, refetch } = useDashboard()

  // WebSocket: refresh on critical events
  const handleWsMessage = useCallback((msg: { type: string }) => {
    if (msg.type === 'critical_violation') {
      toast.error('⚠️ Critical violation detected!')
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    } else if (['task_escalated', 'task_resolved', 'task_verified'].includes(msg.type)) {
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    }
  }, [qc])

  const { connect } = useWebSocket(handleWsMessage)
  useEffect(() => { connect() }, [connect])

  const d = dash as DashboardData | undefined

  const catData = d?.violations_by_category?.map((c) => ({
    name: c.category.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2'),
    count: c.count,
  })) ?? []

  const trendData = d?.violation_trend ?? []

  const taskPie = d?.task_status_breakdown
    ? Object.entries(d.task_status_breakdown).map(([k, v]) => ({ name: k, value: v }))
    : []

  const PIE_COLORS = ['#2563eb', '#ca8a04', '#ea580c', '#dc2626', '#16a34a', '#8b5cf6', '#6b7280']

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Compliance Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {d ? `Updated ${formatRelative(d.generated_at)} · ${d.period_days}-day window` : 'Loading…'}
          </p>
        </div>
        <button className="btn-secondary" onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Demo warning */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-yellow-950 border border-yellow-800">
        <span className="text-xs text-yellow-400">
          ⚠️ SYNTHETIC DEMO DATA — Not based on real Coal India or government data
        </span>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {isLoading ? (
          Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)
        ) : d ? (
          <>
            <KPICard
              value={`${d.kpis.compliance_pct}%`}
              label="Compliance"
              color={getComplianceColor(d.kpis.compliance_pct)}
              onClick={() => navigate('/violations')}
            />
            <KPICard value={d.kpis.critical_risks} label="Critical Risks" color="#dc2626"
              onClick={() => navigate('/violations?severity=critical')} />
            <KPICard value={d.kpis.high_risks} label="High Risks" color="#ea580c"
              onClick={() => navigate('/violations?severity=high')} />
            <KPICard value={d.kpis.medium_risks} label="Medium Risks" color="#ca8a04"
              onClick={() => navigate('/violations?severity=medium')} />
            <KPICard value={d.kpis.overdue_actions} label="Overdue Actions" color="#dc2626"
              onClick={() => navigate('/tasks?overdue=true')} />
            <KPICard value={d.kpis.recurring_violations} label="Recurring" color="#8b5cf6"
              onClick={() => navigate('/violations?recurring=true')} />
            <KPICard value={d.kpis.pending_actions} label="Pending" color="#ca8a04"
              onClick={() => navigate('/tasks?status=open')} />
            <KPICard value={d.kpis.total_inspections} label="Inspections" color="#2563eb"
              onClick={() => navigate('/inspections')} />
          </>
        ) : null}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Violations by Category */}
        <div className="card lg:col-span-2">
          <div className="card-header">
            <h2 className="section-header"><AlertTriangle className="w-4 h-4 text-orange-400" />Violations by Category</h2>
          </div>
          <div className="card-body">
            {catData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={catData} margin={{ left: -10 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <Tooltip
                    contentStyle={{ background: 'hsl(222,47%,12%)', border: '1px solid hsl(222,47%,20%)', borderRadius: 6, fontSize: 12 }}
                    labelStyle={{ color: '#cbd5e1' }}
                  />
                  <Bar dataKey="count" fill="#2d72b1" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">No violations found</div>
            )}
          </div>
        </div>

        {/* Task Status Pie */}
        <div className="card">
          <div className="card-header">
            <h2 className="section-header"><CheckSquare className="w-4 h-4 text-blue-400" />Task Status</h2>
          </div>
          <div className="card-body">
            {taskPie.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={taskPie} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" paddingAngle={2}>
                    {taskPie.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'hsl(222,47%,12%)', border: '1px solid hsl(222,47%,20%)', fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">No tasks</div>
            )}
          </div>
        </div>
      </div>

      {/* Trend */}
      {trendData.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="section-header"><TrendingUp className="w-4 h-4 text-primary" />Violation Trend (30 days)</h2>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={trendData}>
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ background: 'hsl(222,47%,12%)', border: '1px solid hsl(222,47%,20%)', fontSize: 12 }} />
                <Line type="monotone" dataKey="violations" stroke="#2d72b1" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Bottom row: Recent Inspections + Critical Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent Inspections */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h2 className="section-header mb-0"><ClipboardList className="w-4 h-4 text-primary" />Recent Inspections</h2>
            <button className="text-xs text-primary hover:underline" onClick={() => navigate('/inspections')}>
              View all
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {(d?.recent_inspections ?? []).map((insp) => (
                  <tr key={insp.id} className="cursor-pointer" onClick={() => navigate(`/inspections/${insp.id}`)}>
                    <td className="font-mono text-xs text-primary">{insp.reference_number}</td>
                    <td className="capitalize text-sm">{insp.inspection_type}</td>
                    <td><span className={`badge-${insp.status?.replace('_', '-')}`}>{insp.status}</span></td>
                    <td>{insp.compliance_score != null ? `${(insp.compliance_score * 100).toFixed(0)}%` : '—'}</td>
                    <td className="text-xs text-muted-foreground">{formatRelative(insp.created_at)}</td>
                  </tr>
                ))}
                {!d?.recent_inspections?.length && (
                  <tr><td colSpan={5} className="text-center text-muted-foreground py-4 text-sm">No inspections</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Critical Alerts */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h2 className="section-header mb-0"><AlertTriangle className="w-4 h-4 text-red-400" />Critical Actions</h2>
            <button className="text-xs text-primary hover:underline" onClick={() => navigate('/tasks')}>
              View all
            </button>
          </div>
          <div className="card-body space-y-2">
            {(d?.critical_alerts ?? []).map((alert: CriticalAlert) => {
              const overdue = isOverdue(alert.due_date ?? undefined, alert.status)
              return (
                <div
                  key={alert.id}
                  className="flex items-start gap-3 p-3 rounded-md bg-secondary/50 border border-border cursor-pointer hover:border-red-800 transition-colors"
                  onClick={() => navigate(`/tasks/${alert.id}`)}
                >
                  <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground truncate">{alert.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={getTaskStatusClass(alert.status, overdue)}>
                        {overdue ? 'OVERDUE' : alert.status}
                      </span>
                      {alert.due_date && (
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {formatRelative(alert.due_date)}
                        </span>
                      )}
                    </div>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground shrink-0" />
                </div>
              )
            })}
            {!d?.critical_alerts?.length && (
              <div className="text-center text-muted-foreground py-8 text-sm">No critical actions</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
