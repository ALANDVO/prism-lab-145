# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Fixed
- Critical bug in `SessionDetailResponse.from_session()` and WebSocket message serialization: `msg.role` is already a string due to Pydantic v2 `use_enum_values=True`, not an enum with `.value` attribute
- FastAPI mypy errors: missing `AsyncIterator` import, incorrect `lifespan` return type, union response type not valid for response model
- 57 ruff linting issues auto-fixed (import sorting, unused imports, modern type annotations)

### Verified
- All 7 unit tests pass
- Mypy clean on entire server package
- Server starts and serves built React frontend
- REST API: create, list, get, delete, send input, stop sessions
- WebSocket: real-time output streaming, input sending, ping/pong
- Mock provider functional for end-to-end testing

## 1.0.0 — 2026-11-05

### Added
- Core server skeleton with FastAPI + React + WebSocket
- Session management REST API (create, list, get, delete, send input, stop)
- WebSocket endpoint for real-time session output streaming
- Mock provider for testing (echo agent)
- Claude Code and Codex provider stubs with auto-detection
- Session manager with process lifecycle handling
- React frontend with session list and terminal-like output
- Input history navigation (arrow up/down)
- Auto-scroll terminal output

### Tests
- 7 unit tests for session models, providers, and session manager

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
