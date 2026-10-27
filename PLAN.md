# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-server-skeleton

## Roadmap

### core-server-skeleton — Core Server Skeleton (FastAPI + React + WebSocket)

Status: done

Acceptance:
- FastAPI server starts and serves React frontend
- WebSocket endpoint for real-time communication
- Basic agent process management (spawn, read output, send input)
- REST API for session management (create, list, delete sessions)
- Frontend shows session list and terminal-like output

Implementation: `server/main.py`, `server/api/sessions.py`, `server/api/websocket.py`, `server/core/session_manager.py`, `server/core/providers.py`, `server/models/session.py`, `frontend/src/App.tsx`, `frontend/src/components/SessionList.tsx`, `frontend/src/components/Terminal.tsx`, `frontend/src/hooks/useWebSocket.ts`, `frontend/src/hooks/useSessions.ts`, `frontend/src/api/client.ts`

Tests: `tests/test_sessions.py`

### provider-adapters — Provider Adapters (Claude Code, Codex, etc.)

Status: planned

Acceptance:
- Abstract provider interface
- Claude Code adapter implementation
- Codex adapter implementation
- Provider auto-detection

### session-persistence — Session Persistence (SQLite)

Status: planned

Acceptance:
- SQLite database for session storage
- Persist session history and state
- Restore sessions on server restart

### auth-remote-access — Authentication & Remote Access

Status: planned

Acceptance:
- Token-based authentication
- Remote client connection support
- HTTPS/TLS support for production

### mobile-responsive-ui — Mobile-Responsive Web UI

Status: planned

Acceptance:
- Responsive design for mobile browsers
- Touch-friendly terminal interaction
- Offline-capable service worker

