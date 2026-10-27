"""Session manager for handling agent sessions."""
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Set, Callable, Awaitable
from uuid import UUID

from server.models.session import Session, SessionCreate, SessionStatus, MessageRole
from server.core.providers import Provider, get_provider, MockProvider

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages the lifecycle of agent sessions."""

    def __init__(self, default_working_dir: Optional[Path] = None):
        self._sessions: Dict[UUID, Session] = {}
        self._processes: Dict[UUID, asyncio.subprocess.Process] = {}
        self._read_tasks: Dict[UUID, asyncio.Task] = {}
        self._output_callbacks: Dict[UUID, Set[Callable[[str], Awaitable[None]]]] = {}
        self._default_working_dir = default_working_dir or Path.cwd()

    async def create_session(self, session_create: SessionCreate) -> Session:
        """Create a new agent session."""
        provider = get_provider(session_create.provider)
        if not provider:
            # Fall back to mock provider
            provider = MockProvider()
            logger.warning(f"Provider '{session_create.provider}' not found, using mock")

        working_dir = Path(session_create.working_directory) if session_create.working_directory else self._default_working_dir
        working_dir = working_dir.resolve()

        session = Session(
            provider=provider.name,
            working_directory=str(working_dir),
            status=SessionStatus.CREATED,
        )

        if session_create.initial_prompt:
            session.add_message(MessageRole.USER, session_create.initial_prompt)

        self._sessions[session.id] = session
        self._output_callbacks[session.id] = set()

        logger.info(f"Created session {session.id} with provider {provider.name}")
        return session

    async def start_session(self, session_id: UUID) -> bool:
        """Start the agent process for a session."""
        session = self._sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return False

        if session.id in self._processes:
            logger.warning(f"Session {session_id} already has a process")
            return False

        provider = get_provider(session.provider)
        if not provider:
            session.set_status(SessionStatus.ERROR, f"Provider '{session.provider}' not available")
            return False

        try:
            session.set_status(SessionStatus.STARTING)
            initial_prompt = None
            # Find the first user message as initial prompt
            for msg in session.messages:
                if msg.role == MessageRole.USER:
                    initial_prompt = msg.content
                    break

            process = await provider.spawn(session, Path(session.working_directory), initial_prompt)
            self._processes[session.id] = process
            session.pid = process.pid
            session.set_status(SessionStatus.RUNNING)

            # Start reading output
            task = asyncio.create_task(self._read_output(session.id, process))
            self._read_tasks[session.id] = task

            logger.info(f"Started session {session_id} (pid={process.pid})")
            return True

        except Exception as e:
            logger.exception(f"Failed to start session {session_id}")
            session.set_status(SessionStatus.ERROR, str(e))
            return False

    async def _read_output(self, session_id: UUID, process: asyncio.subprocess.Process) -> None:
        """Read output from the agent process and broadcast to callbacks."""
        session = self._sessions.get(session_id)
        if not session:
            return

        try:
            assert process.stdout is not None
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                text = line.decode(errors="replace").rstrip("\n")
                if text:
                    session.add_message(MessageRole.AGENT, text)
                    await self._broadcast_output(session_id, text)

        except asyncio.CancelledError:
            logger.debug(f"Output reader cancelled for session {session_id}")
        except Exception as e:
            logger.exception(f"Error reading output for session {session_id}")
            if session:
                session.add_message(MessageRole.ERROR, f"Output error: {e}")
                await self._broadcast_output(session_id, f"[Error] {e}")
        finally:
            # Process ended
            await process.wait()
            session = self._sessions.get(session_id)
            if session and session.status == SessionStatus.RUNNING:
                session.set_status(SessionStatus.STOPPED)
                await self._broadcast_output(session_id, "[Session ended]")
            self._cleanup_session(session_id)

    async def _broadcast_output(self, session_id: UUID, text: str) -> None:
        """Broadcast output to all registered callbacks."""
        callbacks = self._output_callbacks.get(session_id, set())
        for callback in callbacks:
            try:
                await callback(text)
            except Exception:
                logger.exception(f"Error in output callback for session {session_id}")

    def register_output_callback(self, session_id: UUID, callback: Callable[[str], Awaitable[None]]) -> None:
        """Register a callback for session output."""
        if session_id not in self._output_callbacks:
            self._output_callbacks[session_id] = set()
        self._output_callbacks[session_id].add(callback)

    def unregister_output_callback(self, session_id: UUID, callback: Callable[[str], Awaitable[None]]) -> None:
        """Unregister a callback for session output."""
        if session_id in self._output_callbacks:
            self._output_callbacks[session_id].discard(callback)

    async def send_input(self, session_id: UUID, input_text: str) -> bool:
        """Send input to the agent process."""
        session = self._sessions.get(session_id)
        process = self._processes.get(session_id)

        if not session or not process:
            logger.error(f"Session {session_id} not found or not running")
            return False

        if session.status != SessionStatus.RUNNING:
            logger.warning(f"Session {session_id} not running (status: {session.status})")
            return False

        provider = get_provider(session.provider)
        if not provider:
            provider = MockProvider()

        try:
            session.add_message(MessageRole.USER, input_text)
            await provider.send_input(process, input_text)
            return True
        except Exception as e:
            logger.exception(f"Failed to send input to session {session_id}")
            session.add_message(MessageRole.ERROR, f"Input error: {e}")
            return False

    async def stop_session(self, session_id: UUID) -> bool:
        """Stop an agent session."""
        session = self._sessions.get(session_id)
        process = self._processes.get(session_id)

        if not session:
            return False

        if process:
            provider = get_provider(session.provider)
            if not provider:
                provider = MockProvider()
            await provider.terminate(process)

        self._cleanup_session(session_id)
        session.set_status(SessionStatus.STOPPED)
        logger.info(f"Stopped session {session_id}")
        return True

    def _cleanup_session(self, session_id: UUID) -> None:
        """Clean up process and task references."""
        self._processes.pop(session_id, None)
        task = self._read_tasks.pop(session_id, None)
        if task and not task.done():
            task.cancel()

    def get_session(self, session_id: UUID) -> Optional[Session]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[Session]:
        """List all sessions."""
        return list(self._sessions.values())

    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a session completely."""
        if session_id in self._processes:
            await self.stop_session(session_id)

        if session_id in self._sessions:
            del self._sessions[session_id]
            self._output_callbacks.pop(session_id, None)
            logger.info(f"Deleted session {session_id}")
            return True
        return False

    async def shutdown(self) -> None:
        """Shutdown all sessions."""
        session_ids = list(self._sessions.keys())
        for session_id in session_ids:
            await self.stop_session(session_id)
        self._sessions.clear()
        self._output_callbacks.clear()
        logger.info("Session manager shutdown complete")
