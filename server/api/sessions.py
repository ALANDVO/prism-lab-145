"""REST API endpoints for session management."""
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from server.models.session import Session, SessionCreate, SessionStatus, MessageRole
from server.core.session_manager import SessionManager

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Global session manager instance (set by main.py)
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    if _session_manager is None:
        raise RuntimeError("Session manager not initialized")
    return _session_manager


def set_session_manager(manager: SessionManager) -> None:
    global _session_manager
    _session_manager = manager


class SessionResponse(BaseModel):
    """Session response for API."""
    id: UUID
    provider: str
    working_directory: str
    status: SessionStatus
    created_at: str
    updated_at: str
    message_count: int
    pid: int | None
    error: str | None

    @classmethod
    def from_session(cls, session: Session) -> "SessionResponse":
        return cls(
            id=session.id,
            provider=session.provider,
            working_directory=session.working_directory,
            status=session.status,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=len(session.messages),
            pid=session.pid,
            error=session.error,
        )


class SessionDetailResponse(SessionResponse):
    """Detailed session response with messages."""
    messages: list[dict]

    @classmethod
    def from_session(cls, session: Session) -> "SessionDetailResponse":
        return cls(
            id=session.id,
            provider=session.provider,
            working_directory=session.working_directory,
            status=session.status,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=len(session.messages),
            pid=session.pid,
            error=session.error,
            messages=[
                {
                    "id": str(msg.id),
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in session.messages
            ],
        )


class CreateSessionRequest(BaseModel):
    """Request to create a session."""
    provider: str = "mock"
    working_directory: str | None = None
    initial_prompt: str | None = None


class SendInputRequest(BaseModel):
    """Request to send input to a session."""
    input: str


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionResponse:
    """Create a new agent session."""
    session_create = SessionCreate(
        provider=request.provider,
        working_directory=request.working_directory,
        initial_prompt=request.initial_prompt,
    )
    session = await manager.create_session(session_create)
    await manager.start_session(session.id)
    return SessionResponse.from_session(session)


@router.get("", response_model=list[SessionResponse])
async def list_sessions(manager: SessionManager = Depends(get_session_manager)) -> list[SessionResponse]:
    """List all sessions."""
    sessions = manager.list_sessions()
    return [SessionResponse.from_session(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionDetailResponse:
    """Get session details including message history."""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetailResponse.from_session(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    manager: SessionManager = Depends(get_session_manager),
) -> None:
    """Delete a session."""
    success = await manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/input", status_code=status.HTTP_204_NO_CONTENT)
async def send_input(
    session_id: UUID,
    request: SendInputRequest,
    manager: SessionManager = Depends(get_session_manager),
) -> None:
    """Send input to a running session."""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    success = await manager.send_input(session_id, request.input)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to send input (session not running)")


@router.post("/{session_id}/stop", status_code=status.HTTP_204_NO_CONTENT)
async def stop_session(
    session_id: UUID,
    manager: SessionManager = Depends(get_session_manager),
) -> None:
    """Stop a running session."""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await manager.stop_session(session_id)
