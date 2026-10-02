import { FileBarChart2 } from 'lucide-react'
import { useState } from 'react'
import { reportsApi } from '@/services/api'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'

export default function ReportsPage() {
  const mineId = useAuthStore((s) => s.selectedMineId)
  const [loading, setLoading] = useState(false)
  const [reportUrl, setReportUrl] = useState<string | null>(null)

  const generate = async (type: string) => {
    setLoading(true)
    setReportUrl(null)
    try {
      const res = await reportsApi.generate({ mine_id: mineId, report_type: type, format: 'pdf' })
      if (res.status === 'complete' && res.file_path) {
        setReportUrl(res.file_path)
        toast.success('Report generated')
      } else {
        toast.error(res.error_message || 'Report generation failed')
      }
    } catch {
      toast.error('Report generation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-foreground">Reports</h1>
        <p className="text-sm text-muted-foreground">Generate compliance and analytics reports</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { type: 'compliance', title: 'Compliance Report', desc: 'Full compliance status with violation summary and task status' },
          { type: 'incident', title: 'Incident Report', desc: 'Critical incidents and escalation history' },
          { type: 'trend', title: 'Trend Analysis', desc: 'Violation trends and recurring risk patterns' },
        ].map((r) => (
          <div key={r.type} className="card card-body space-y-3">
            <FileBarChart2 className="w-8 h-8 text-primary" />
            <h3 className="font-semibold text-foreground">{r.title}</h3>
            <p className="text-xs text-muted-foreground">{r.desc}</p>
            <button className="btn-primary w-full justify-center" onClick={() => generate(r.type)} disabled={loading}>
              {loading ? 'Generating…' : 'Generate'}
            </button>
          </div>
        ))}
      </div>

      {reportUrl && (
        <div className="card card-body">
          <p className="text-sm text-foreground">Report ready:</p>
          <a href={reportUrl} target="_blank" rel="noopener" className="text-sm text-primary hover:underline">{reportUrl}</a>
        </div>
      )}
    </div>
  )
}
