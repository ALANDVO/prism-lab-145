from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Status of an agent session."""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class MessageRole(str, Enum):
    """Role of a message in the session."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    ERROR = "error"


class SessionMessage(BaseModel):
    """A single message in the session conversation."""
    id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {"use_enum_values": True}


class SessionCreate(BaseModel):
    """Request to create a new session."""
    provider: str = "mock"  # mock, claude, codex, cursor, etc.
    working_directory: str | None = None
    initial_prompt: str | None = None


class Session(BaseModel):
    """An agent session."""
    id: UUID = Field(default_factory=uuid4)
    provider: str
    working_directory: str
    status: SessionStatus = SessionStatus.CREATED
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: list[SessionMessage] = Field(default_factory=list)
    pid: int | None = None
    error: str | None = None

    model_config = {"use_enum_values": True}

    def add_message(self, role: MessageRole, content: str) -> SessionMessage:
        """Add a message to the session."""
        msg = SessionMessage(role=role, content=content)
        self.messages.append(msg)
        self.updated_at = datetime.now()
        return msg

    def set_status(self, status: SessionStatus, error: str | None = None) -> None:
        """Update session status."""
        self.status = status
        self.error = error
        self.updated_at = datetime.now()
