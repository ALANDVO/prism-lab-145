import { useState } from 'react'
import { useSessions } from './hooks/useSessions'
import { useWebSocket } from './hooks/useWebSocket'
import { SessionList } from './components/SessionList'
import { Terminal } from './components/Terminal'

function App() {
  const { sessions, createSession } = useSessions()
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [showWelcome, setShowWelcome] = useState(true)

  const handleCreateSession = async (provider: string, initialPrompt?: string) => {
    const session = await createSession({ provider, initial_prompt: initialPrompt })
    setActiveSessionId(session.id)
    setShowWelcome(false)
  }

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id)
    setShowWelcome(false)
  }

  const activeSession = sessions.find((s) => s.id === activeSessionId)

  const {
    connected,
    messages,
    sessionState,
    sendInput,
  } = useWebSocket(activeSessionId)

  return (
    <div className="app">
      <header className="app-header">
        <h1>Prism Lab 145</h1>
        <p className="subtitle">Agent Harness Control Surface</p>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <SessionList
            activeSessionId={activeSessionId}
            onSelectSession={handleSelectSession}
          />
        </aside>

        <main className="main-content">
          {showWelcome && !activeSessionId && (
            <div className="welcome-screen">
              <h2>Welcome to Prism Lab 145</h2>
              <p>Control AI coding agents from your browser.</p>
              <div className="providers-info">
                <h3>Available Providers</h3>
                <ul>
                  <li><strong>Mock</strong> - Echo agent for testing (always available)</li>
                  <li><strong>Claude Code</strong> - Requires <code>claude</code> CLI installed</li>
                  <li><strong>Codex</strong> - Requires <code>codex</code> CLI installed</li>
                </ul>
              </div>
              <button className="btn btn-primary" onClick={() => handleCreateSession('mock')}>
                Create Mock Session
              </button>
            </div>
          )}

          {activeSessionId && (
            <>
              {activeSession && (
                <div className="session-toolbar">
                  <span className="session-badge">{activeSession.provider}</span>
                  <span className="session-badge">{activeSession.status}</span>
                </div>
              )}
              <Terminal
                messages={messages}
                sessionState={sessionState}
                onSendInput={sendInput}
                connected={connected}
              />
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
