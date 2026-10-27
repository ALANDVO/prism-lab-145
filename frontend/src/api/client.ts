const API_BASE = '/api'

export interface Session {
  id: string
  provider: string
  working_directory: string
  status: 'created' | 'starting' | 'running' | 'stopped' | 'error'
  created_at: string
  updated_at: string
  message_count: number
  pid: number | null
  error: string | null
}

export interface SessionDetail extends Session {
  messages: Message[]
}

export interface Message {
  id: string
  role: 'user' | 'agent' | 'system' | 'error'
  content: string
  timestamp: string
}

export interface CreateSessionRequest {
  provider: string
  working_directory?: string
  initial_prompt?: string
}

export interface SendInputRequest {
  input: string
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export const api = {
  async listSessions(): Promise<Session[]> {
    return fetchJson(`${API_BASE}/sessions`)
  },

  async createSession(request: CreateSessionRequest): Promise<Session> {
    return fetchJson(`${API_BASE}/sessions`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  async getSession(id: string): Promise<SessionDetail> {
    return fetchJson(`${API_BASE}/sessions/${id}`)
  },

  async deleteSession(id: string): Promise<void> {
    await fetch(`${API_BASE}/sessions/${id}`, { method: 'DELETE' })
  },

  async sendInput(id: string, input: string): Promise<void> {
    await fetchJson(`${API_BASE}/sessions/${id}/input`, {
      method: 'POST',
      body: JSON.stringify({ input }),
    })
  },

  async stopSession(id: string): Promise<void> {
    await fetchJson(`${API_BASE}/sessions/${id}/stop`, { method: 'POST' })
  },
}
