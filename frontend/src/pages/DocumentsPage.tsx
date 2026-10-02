import { FileText } from 'lucide-react'
import { formatRelative, formatDate } from '@/utils'
import { useQuery } from '@tanstack/react-query'
import { documentsApi } from '@/services/api'
import type { ComplianceDocument } from '@/types'

export default function DocumentsPage() {
  const { data, isLoading } = useQuery({ queryKey: ['documents'], queryFn: () => documentsApi.list() })
  const docs: ComplianceDocument[] = Array.isArray(data) ? data : []

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-foreground">Compliance Documents</h1>
        <p className="text-sm text-muted-foreground">{docs.length} documents</p>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr><th>Title</th><th>Type</th><th>Reference</th><th>Compliance</th><th>Expiry</th><th>OCR</th><th>Uploaded</th></tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>{Array.from({ length: 7 }).map((_, j) => <td key={j}><div className="skeleton h-4 w-full" /></td>)}</tr>
                ))
              ) : docs.map((d) => (
                <tr key={d.id}>
                  <td className="flex items-center gap-2"><FileText className="w-4 h-4 text-primary shrink-0" />{d.title}</td>
                  <td className="capitalize text-sm">{d.document_type?.replace('_', ' ') ?? '—'}</td>
                  <td className="font-mono text-xs">{d.reference_number ?? '—'}</td>
                  <td>
                    <span className={`badge-${d.compliance_status === 'compliant' ? 'low' : d.compliance_status === 'expired' ? 'critical' : 'medium'}`}>
                      {d.compliance_status ?? '—'}
                    </span>
                  </td>
                  <td className="text-xs">{formatDate(d.expiry_date)}</td>
                  <td><span className={`text-xs font-medium ${d.ocr_status === 'complete' ? 'text-green-400' : 'text-yellow-400'}`}>{d.ocr_status}</span></td>
                  <td className="text-xs text-muted-foreground">{formatRelative(d.created_at)}</td>
                </tr>
              ))}
              {!isLoading && !docs.length && (
                <tr><td colSpan={7} className="text-center py-8 text-muted-foreground">No documents</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
