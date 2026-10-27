import { useEffect, useRef, useState } from 'react'
import { WSMessage } from '../hooks/useWebSocket'

interface TerminalProps {
  messages: WSMessage[]
  sessionState: WSMessage | null
  onSendInput: (content: string) => void
  connected: boolean
}

export function Terminal({ messages, sessionState, onSendInput, connected }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [input, setInput] = useState('')
  const [history, setHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && connected) {
      onSendInput(input)
      setHistory((prev) => [...prev, input])
      setHistoryIndex(-1)
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (history.length > 0 && historyIndex < history.length - 1) {
        const newIndex = historyIndex + 1
        setHistoryIndex(newIndex)
        setInput(history[history.length - 1 - newIndex])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setInput(history[history.length - 1 - newIndex])
      } else if (historyIndex === 0) {
        setHistoryIndex(-1)
        setInput('')
      }
    }
  }

  return (
    <div className="terminal">
      <div className="terminal-header">
        <div className="terminal-title">
          {sessionState?.provider || 'Session'} @ {sessionState?.working_directory || 'unknown'}
        </div>
        <div className="terminal-status">
          <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`} />
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
      <div className="terminal-output" ref={terminalRef}>
        {messages.map((msg, index) => (
          <div key={index} className={`terminal-line ${msg.type}`}>
            {msg.type === 'session_state' && (
              <span className="system-message">
                Session {msg.status} - {msg.provider}
              </span>
            )}
            {msg.type === 'message' && msg.message && (
              <div className={`message ${msg.message.role}`}>
                <span className="message-role">{msg.message.role}:</span>
                <span className="message-content">{msg.message.content}</span>
              </div>
            )}
            {msg.type === 'output' && msg.content && (
              <div className="agent-output">{msg.content}</div>
            )}
            {msg.type === 'error' && (
              <div className="error-message">{msg.content || 'Error'}</div>
            )}
          </div>
        ))}
      </div>
      <form className="terminal-input-form" onSubmit={handleSubmit}>
        <span className="prompt">$</span>
        <textarea
          ref={inputRef}
          className="terminal-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={connected ? 'Type a message...' : 'Not connected'}
          disabled={!connected}
          rows={1}
          spellCheck={false}
        />
      </form>
    </div>
  )
}
