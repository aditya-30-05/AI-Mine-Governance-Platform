import { useState, useRef, useCallback } from 'react'

interface WSMessage {
  type: string
  [key: string]: unknown
}

type MessageHandler = (msg: WSMessage) => void

export function useWebSocket(onMessage?: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)

  const connect = useCallback((mineId = 'global') => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/dashboard?mine_id=${mineId}`

    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      // Auto-reconnect in 5s
      setTimeout(() => connect(mineId), 5000)
    }
    ws.onerror = () => ws.close()
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data) as WSMessage
        onMessage?.(msg)
      } catch {
        // Ignore malformed messages
      }
    }
  }, [onMessage])

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  const ping = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send('ping')
    }
  }, [])

  return { connect, disconnect, ping, connected }
}
