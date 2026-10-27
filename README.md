# Prism Lab 145 — Alan Vo

> Work in progress. This checkpoint may be incomplete or fail tests. See PLAN.md and STATUS.md before use.


**Agent Harness Control Surface** - Control AI coding agents (Claude Code, Codex, etc.) from a web UI.

Inspired by [t3code](https://github.com/pingdotgg/t3code), built as an original implementation.

## Features

- 🌐 **Web-based UI** - Control agents from any browser (desktop or mobile)
- 🤖 **Multiple Providers** - Mock (testing), Claude Code, Codex support
- ⚡ **Real-time Streaming** - WebSocket-based live output from agents
- 📝 **Session Management** - Create, list, stop, and delete agent sessions
- 🔧 **FastAPI Backend** - Modern Python async API with automatic OpenAPI docs
- ⚛️ **React Frontend** - TypeScript + Vite for fast development

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend development)
- `uv` recommended for Python package management

### Installation

```bash
# Clone and enter directory
cd prism-lab-145

# Install Python dependencies
pip install -e .[dev]

# Install frontend dependencies
cd frontend && npm install

# Build frontend for production
npm run build

# Run the server (serves built frontend at http://localhost:8000)
cd .. && python -m server
```

### Development Mode

Run frontend and backend separately for hot reload:

```bash
# Terminal 1: Frontend dev server (port 5173)
cd frontend && npm run dev

# Terminal 2: Backend with auto-reload (port 8000)
python -m server
```

Visit http://localhost:5173 for the frontend (proxied to backend API).

## Usage

1. Open http://localhost:8000 (or http://localhost:5173 in dev)
2. Click "New Session" in the sidebar
3. Choose a provider:
   - **Mock** - Always available, echoes your input for testing
   - **Claude Code** - Requires `claude` CLI installed and authenticated
   - **Codex** - Requires `codex` CLI installed and authenticated
4. Optionally enter an initial prompt
5. Click "Create" - the session starts and you can interact with the agent

## Architecture

```
prism-lab-145/
├── server/                 # FastAPI backend
│   ├── api/               # REST + WebSocket endpoints
│   ├── core/              # Business logic (session manager, providers)
│   ├── models/            # Pydantic models
│   └── main.py            # App entry point
├── frontend/              # React + Vite frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── api/           # API client
│   │   └── styles/        # Global CSS
│   └── ...
└── tests/                 # Pytest tests
```

### Provider System

Providers implement the `Provider` abstract base class:

```python
class Provider(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def spawn(self, session, working_dir, initial_prompt) -> Process:
        pass
    
    @abstractmethod
    def get_command(self, working_dir, initial_prompt) -> List[str]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
```

Add new providers by implementing this interface and registering with `register_provider()`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/sessions` | Create new session |
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/{id}` | Get session details |
| DELETE | `/api/sessions/{id}` | Delete session |
| POST | `/api/sessions/{id}/input` | Send input to session |
| POST | `/api/sessions/{id}/stop` | Stop session |
| WS | `/ws/sessions/{id}` | WebSocket for real-time output |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=server

# Run specific test
pytest tests/test_sessions.py::test_session_models
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `WORKING_DIR` | `cwd` | Default working directory for sessions |

## Roadmap

- [ ] SQLite persistence for sessions
- [ ] Authentication & remote access (TLS)
- [ ] Mobile-responsive UI improvements
- [ ] More providers (Cursor, Grok, OpenCode)
- [ ] File upload/download support
- [ ] Session sharing/collaboration
- [ ] Terminal emulation (xterm.js)

## License

MIT License - see LICENSE file for details.

Maintainer: Alan Vo <alanvo@gmail.com>
