"""Tests for session management."""
import pytest
from uuid import uuid4
from server.models.session import Session, SessionCreate, SessionStatus, MessageRole
from server.core.providers import MockProvider, get_provider, list_providers
from server.core.session_manager import SessionManager


def test_session_models():
    """Test session model creation and methods."""
    session = Session(provider="mock", working_directory="/tmp")
    assert session.id is not None
    assert session.provider == "mock"
    assert session.status == SessionStatus.CREATED

    msg = session.add_message(MessageRole.USER, "Hello")
    assert msg.role == MessageRole.USER
    assert msg.content == "Hello"
    assert len(session.messages) == 1

    session.set_status(SessionStatus.RUNNING)
    assert session.status == SessionStatus.RUNNING


def test_session_create_model():
    """Test SessionCreate model."""
    create = SessionCreate(provider="claude", working_directory="/home", initial_prompt="Hi")
    assert create.provider == "claude"
    assert create.working_directory == "/home"
    assert create.initial_prompt == "Hi"


def test_mock_provider():
    """Test mock provider availability and command."""
    provider = MockProvider()
    assert provider.is_available() is True
    cmd = provider.get_command("/tmp")
    assert "python" in cmd[0]


def test_provider_registry():
    """Test provider registry functions."""
    providers = list_providers()
    assert len(providers) >= 3  # mock, claude, codex

    mock = get_provider("mock")
    assert mock is not None
    assert mock.name == "mock"

    claude = get_provider("claude")
    assert claude is not None
    assert claude.name == "claude"

    assert get_provider("nonexistent") is None


@pytest.mark.asyncio
async def test_session_manager_create():
    """Test session manager creates sessions."""
    manager = SessionManager()
    session = await manager.create_session(SessionCreate(provider="mock"))
    assert session.provider == "mock"
    assert session.status == SessionStatus.CREATED

    # Test start
    success = await manager.start_session(session.id)
    assert success is True
    assert session.status == SessionStatus.RUNNING
    assert session.pid is not None

    # Test send input
    await manager.send_input(session.id, "test input")

    # Wait a bit for output
    import asyncio
    await asyncio.sleep(0.5)

    # Test stop
    await manager.stop_session(session.id)
    assert session.status == SessionStatus.STOPPED


@pytest.mark.asyncio
async def test_session_manager_list():
    """Test listing sessions."""
    manager = SessionManager()
    s1 = await manager.create_session(SessionCreate(provider="mock"))
    s2 = await manager.create_session(SessionCreate(provider="mock"))

    sessions = manager.list_sessions()
    assert len(sessions) == 2
    ids = {s.id for s in sessions}
    assert s1.id in ids
    assert s2.id in ids


@pytest.mark.asyncio
async def test_session_manager_delete():
    """Test deleting sessions."""
    manager = SessionManager()
    session = await manager.create_session(SessionCreate(provider="mock"))
    await manager.start_session(session.id)

    success = await manager.delete_session(session.id)
    assert success is True
    assert manager.get_session(session.id) is None
    assert len(manager.list_sessions()) == 0
