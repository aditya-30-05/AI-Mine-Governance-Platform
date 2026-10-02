import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Filter, RefreshCw, RotateCcw } from 'lucide-react'
import { useViolations, useRecurringRisks } from '@/hooks/useApi'
import { getSeverityClass, formatRelative, formatDate, truncate } from '@/utils'
import type { Violation, RecurringRisk } from '@/types'

type Tab = 'violations' | 'recurring'

export default function ViolationsPage() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('violations')
  const [severity, setSeverity] = useState('')
  const [category, setCategory] = useState('')

  const { data: violData, isLoading: vLoading, refetch: vRefetch } = useViolations({
    severity: severity || undefined,
    category: category || undefined,
    limit: 50,
  })
  const { data: recurData, isLoading: rLoading } = useRecurringRisks()

  const violations: Violation[] = violData?.items ?? []
  const recurring: RecurringRisk[] = recurData?.items ?? []

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Violations</h1>
          <p className="text-sm text-muted-foreground">
            {violData?.total ?? 0} total · {recurring.length} recurring patterns
          </p>
        </div>
        <button className="btn-secondary" onClick={() => vRefetch()}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {(['violations', 'recurring'] as Tab[]).map((t) => (
          <button
            key={t}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors border-b-2 ${
              tab === t
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
            onClick={() => setTab(t)}
          >
            {t === 'violations' ? `Violations (${violData?.total ?? 0})` : `Recurring Risks (${recurring.length})`}
          </button>
        ))}
      </div>

      {tab === 'violations' && (
        <>
          {/* Filters */}
          <div className="flex flex-wrap gap-2 items-center">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <select className="form-input w-auto text-xs py-1" value={severity} onChange={(e) => setSeverity(e.target.value)}>
              <option value="">All Severities</option>
              {['critical', 'high', 'medium', 'low'].map((s) => (
                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
            <select className="form-input w-auto text-xs py-1" value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">All Categories</option>
              {['PPE', 'Fire Safety', 'Electrical Safety', 'Ventilation', 'Environmental', 'Equipment', 'Documentation'].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            {(severity || category) && (
              <button className="text-xs text-muted-foreground hover:text-foreground" onClick={() => { setSeverity(''); setCategory('') }}>
                Clear filters
              </button>
            )}
          </div>

          {/* Table */}
          <div className="card">
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Reference</th>
                    <th>Category</th>
                    <th>Severity</th>
                    <th>Description</th>
                    <th>Recurring</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {vLoading ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i}>
                        {Array.from({ length: 7 }).map((_, j) => (
                          <td key={j}><div className="skeleton h-4 w-full" /></td>
                        ))}
                      </tr>
                    ))
                  ) : violations.map((v) => (
                    <tr key={v.id} className="cursor-pointer" onClick={() => navigate(`/violations/${v.id}`)}>
                      <td className="font-mono text-xs text-primary">{v.reference_number}</td>
                      <td className="text-sm">{v.category ?? '—'}</td>
                      <td><span className={getSeverityClass(v.severity)}>{v.severity ?? '—'}</span></td>
                      <td className="text-sm text-muted-foreground max-w-xs">{truncate(v.description, 60)}</td>
                      <td>
                        {v.is_recurring && (
                          <span className="inline-flex items-center gap-1 badge-critical">
                            <RotateCcw className="w-3 h-3" /> Recurring
                          </span>
                        )}
                      </td>
                      <td>
                        <span className={`badge-${v.compliance_status === 'compliant' ? 'low' : 'high'}`}>
                          {v.compliance_status ?? '—'}
                        </span>
                      </td>
                      <td className="text-xs text-muted-foreground">{formatRelative(v.created_at)}</td>
                    </tr>
                  ))}
                  {!vLoading && !violations.length && (
                    <tr><td colSpan={7} className="text-center py-8 text-muted-foreground">No violations found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {tab === 'recurring' && (
        <div className="grid grid-cols-1 gap-4">
          {rLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="card card-body"><div className="skeleton h-20 w-full" /></div>
            ))
          ) : recurring.length === 0 ? (
            <div className="card card-body text-center text-muted-foreground py-8">No recurring risks detected</div>
          ) : recurring.map((r) => (
            <div key={r.id} className="card">
              <div className="card-body">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <RotateCcw className="w-5 h-5 text-red-400" />
                      <h3 className="font-semibold text-foreground">{r.category}</h3>
                      <span className={getSeverityClass(r.severity)}>{r.severity}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{r.recommended_action}</p>
                    <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                      <span><strong className="text-foreground">{r.occurrence_count}</strong> occurrences in {r.time_window_days} days</span>
                      <span>First: {formatDate(r.first_occurrence)}</span>
                      <span>Last: {formatDate(r.last_occurrence)}</span>
                      <span className="capitalize">Trend: <strong className={r.trend === 'increasing' ? 'text-red-400' : 'text-yellow-400'}>{r.trend}</strong></span>
                    </div>
                  </div>
                  <div className="shrink-0">
                    <span className={`text-xs px-2 py-1 rounded-full font-semibold border ${
                      r.status === 'active' ? 'bg-red-950 text-red-400 border-red-800' : 'bg-green-950 text-green-400 border-green-800'
                    }`}>
                      {r.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
