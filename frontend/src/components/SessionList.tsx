import { useState, FormEvent } from 'react'
import { Session } from '../api/client'
import { useSessions } from '../hooks/useSessions'

interface SessionListProps {
  activeSessionId: string | null
  onSelectSession: (id: string) => void
}

export function SessionList({ activeSessionId, onSelectSession }: SessionListProps) {
  const { sessions, loading, createSession, deleteSession, stopSession } = useSessions()
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newSessionProvider, setNewSessionProvider] = useState('mock')
  const [newSessionPrompt, setNewSessionPrompt] = useState('')

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    await createSession({
      provider: newSessionProvider,
      initial_prompt: newSessionPrompt || undefined,
    })
    setShowCreateDialog(false)
    setNewSessionPrompt('')
  }

  const getStatusColor = (status: Session['status']) => {
    switch (status) {
      case 'running': return 'var(--success)'
      case 'starting': return 'var(--warning)'
      case 'stopped': return 'var(--fg-muted)'
      case 'error': return 'var(--error)'
      default: return 'var(--fg-secondary)'
    }
  }

  return (
    <div className="session-list">
      <div className="session-list-header">
        <h2>Sessions</h2>
        <button className="btn btn-primary" onClick={() => setShowCreateDialog(true)}>
          + New Session
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : sessions.length === 0 ? (
        <div className="empty-state">
          <p>No sessions yet</p>
          <button className="btn btn-secondary" onClick={() => setShowCreateDialog(true)}>
            Create your first session
          </button>
        </div>
      ) : (
        <ul className="session-list-items">
          {sessions.map((session) => (
            <li
              key={session.id}
              className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
              onClick={() => onSelectSession(session.id)}
            >
              <div className="session-info">
                <div className="session-header">
                  <span className="session-provider">{session.provider}</span>
                  <span
                    className="session-status"
                    style={{ color: getStatusColor(session.status) }}
                  >
                    {session.status}
                  </span>
                </div>
                <div className="session-meta">
                  <span>{session.message_count} messages</span>
                  {session.pid && <span>PID: {session.pid}</span>}
                </div>
                {session.error && <div className="session-error">{session.error}</div>}
              </div>
              <div className="session-actions">
                {session.status === 'running' && (
                  <button
                    className="btn btn-small btn-danger"
                    onClick={(e) => { e.stopPropagation(); stopSession(session.id); }}
                    title="Stop session"
                  >
                    Stop
                  </button>
                )}
                <button
                  className="btn btn-small btn-secondary"
                  onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                  title="Delete session"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {showCreateDialog && (
        <div className="modal-overlay" onClick={() => setShowCreateDialog(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Create New Session</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label htmlFor="provider">Provider</label>
                <select
                  id="provider"
                  value={newSessionProvider}
                  onChange={(e) => setNewSessionProvider(e.target.value)}
                >
                  <option value="mock">Mock (testing)</option>
                  <option value="claude">Claude Code</option>
                  <option value="codex">Codex</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="initialPrompt">Initial Prompt (optional)</label>
                <textarea
                  id="initialPrompt"
                  value={newSessionPrompt}
                  onChange={(e) => setNewSessionPrompt(e.target.value)}
                  rows={3}
                  placeholder="Enter initial prompt for the agent..."
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
