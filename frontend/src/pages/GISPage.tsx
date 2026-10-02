import { Map as MapIcon } from 'lucide-react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { useViolations } from '@/hooks/useApi'
import { getSeverityColor } from '@/utils'
import type { Violation } from '@/types'

export default function GISPage() {
  const { data } = useViolations({ limit: 100 })
  const violations: Violation[] = data?.items ?? []
  const geoViolations = violations.filter((v) => v.latitude && v.longitude)

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-foreground">GIS Violation Map</h1>
        <p className="text-sm text-muted-foreground">{geoViolations.length} geo-tagged violations</p>
      </div>

      {/* Map display */}
      <div className="card overflow-hidden">
        <div className="relative h-[500px] bg-[hsl(222,47%,8%)] flex items-center justify-center">
          {geoViolations.length > 0 ? (
            <GISMapInner violations={geoViolations} />
          ) : (
            <div className="text-center text-muted-foreground">
              <MapIcon className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <p>No geo-tagged violations to display</p>
              <p className="text-xs mt-1">Violations with GPS coordinates will appear here</p>
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs">
        {['critical', 'high', 'medium', 'low'].map((sev) => (
          <div key={sev} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: getSeverityColor(sev as any) }} />
            <span className="text-muted-foreground capitalize">{sev}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function GISMapInner({ violations }: { violations: Violation[] }) {
  const center = violations.length > 0
    ? [violations[0].latitude!, violations[0].longitude!] as [number, number]
    : [23.6250, 85.5140] as [number, number]

  return (
    <MapContainer center={center} zoom={14} style={{ height: '100%', width: '100%' }} scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {violations.map((v) => (
        <CircleMarker
          key={v.id}
          center={[v.latitude!, v.longitude!]}
          radius={v.severity === 'critical' ? 10 : v.severity === 'high' ? 8 : 6}
          pathOptions={{
            color: getSeverityColor(v.severity),
            fillColor: getSeverityColor(v.severity),
            fillOpacity: 0.7,
          }}
        >
          <Popup>
            <div className="text-xs">
              <p className="font-bold">{v.reference_number}</p>
              <p className="capitalize">{v.severity} · {v.category}</p>
              <p className="mt-1">{v.description?.slice(0, 100)}</p>
              {v.is_recurring && <p className="text-red-500 font-semibold mt-1">⚠ RECURRING</p>}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
