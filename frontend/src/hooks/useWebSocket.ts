import { useEffect, useRef, useState, useCallback } from 'react'

export interface WSMessage {
  type: 'session_state' | 'message' | 'output' | 'pong' | 'error'
  session_id?: string
  status?: string
  provider?: string
  working_directory?: string
  message?: {
    id: string
    role: string
    content: string
    timestamp: string
  }
  content?: string
}

export function useWebSocket(sessionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<WSMessage[]>([])
  const [sessionState, setSessionState] = useState<WSMessage | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const messageHandlersRef = useRef<Set<(msg: WSMessage) => void>>(new Set())

  const connect = useCallback(() => {
    if (!sessionId) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/sessions/${sessionId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        setMessages((prev) => [...prev, msg])

        if (msg.type === 'session_state') {
          setSessionState(msg)
        }

        messageHandlersRef.current.forEach((handler) => handler(msg))
      } catch (e) {
        console.error('Failed to parse WS message:', e)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null

      // Attempt reconnect after 2 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect()
      }, 2000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }, [sessionId])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
  }, [])

  const send = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  const sendInput = useCallback((content: string) => {
    send({ type: 'input', content })
  }, [send])

  const subscribe = useCallback((handler: (msg: WSMessage) => void) => {
    messageHandlersRef.current.add(handler)
    return () => messageHandlersRef.current.delete(handler)
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    connected,
    messages,
    sessionState,
    send,
    sendInput,
    subscribe,
    connect,
    disconnect,
  }
}
