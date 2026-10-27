import { useState, useEffect, useCallback } from 'react'
import { api, Session, SessionDetail, CreateSessionRequest } from '../api/client'

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSessions = useCallback(async () => {
    try {
      setError(null)
      const data = await api.listSessions()
      setSessions(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  const createSession = useCallback(async (request: CreateSessionRequest): Promise<Session> => {
    const session = await api.createSession(request)
    setSessions((prev) => [session, ...prev])
    return session
  }, [])

  const deleteSession = useCallback(async (id: string) => {
    await api.deleteSession(id)
    setSessions((prev) => prev.filter((s) => s.id !== id))
  }, [])

  const stopSession = useCallback(async (id: string) => {
    await api.stopSession(id)
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, status: 'stopped' as const } : s)))
  }, [])

  const refresh = useCallback(() => {
    setLoading(true)
    fetchSessions()
  }, [fetchSessions])

  return {
    sessions,
    loading,
    error,
    createSession,
    deleteSession,
    stopSession,
    refresh,
  }
}

export function useSessionDetail(sessionId: string | null) {
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return

    let mounted = true
    setLoading(true)
    setError(null)

    api.getSession(sessionId)
      .then((data) => {
        if (mounted) setSession(data)
      })
      .catch((e) => {
        if (mounted) setError(e instanceof Error ? e.message : 'Failed to load session')
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [sessionId])

  return { session, loading, error }
}
