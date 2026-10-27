"""Provider abstraction for AI coding agents."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List
from pathlib import Path
import asyncio
import shlex
import os
import signal
import sys

from server.models.session import Session, SessionStatus, MessageRole


class Provider(ABC):
    """Abstract base class for AI coding agent providers."""

    name: str
    description: str

    @abstractmethod
    async def spawn(
        self,
        session: Session,
        working_dir: Path,
        initial_prompt: Optional[str] = None,
    ) -> asyncio.subprocess.Process:
        """Spawn the agent process. Returns the process handle."""
        pass

    @abstractmethod
    def get_command(self, working_dir: Path, initial_prompt: Optional[str] = None) -> List[str]:
        """Get the command to run the agent. Used for display/logging."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available on the system."""
        pass

    async def send_input(self, process: asyncio.subprocess.Process, input_text: str) -> None:
        """Send input to the agent process. Default writes to stdin."""
        if process.stdin and not process.stdin.is_closing():
            process.stdin.write((input_text + "\n").encode())
            await process.stdin.drain()

    async def terminate(self, process: asyncio.subprocess.Process) -> None:
        """Gracefully terminate the agent process."""
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()


class MockProvider(Provider):
    """Mock provider for testing - simulates an AI agent that echoes input."""

    name = "mock"
    description = "Mock provider for testing (echoes input)"

    def is_available(self) -> bool:
        return True

    def get_command(self, working_dir: Path, initial_prompt: Optional[str] = None) -> List[str]:
        return [sys.executable, "-c", "import sys; [print(f'Echo: {line.strip()}') for line in sys.stdin]"]

    async def spawn(
        self,
        session: Session,
        working_dir: Path,
        initial_prompt: Optional[str] = None,
    ) -> asyncio.subprocess.Process:
        # Simple echo process for testing
        script = (
            "import sys, asyncio\n"
            "async def main():\n"
            "    print('Mock agent started. Type something...')\n"
            "    sys.stdout.flush()\n"
            "    loop = asyncio.get_event_loop()\n"
            "    reader = asyncio.StreamReader()\n"
            "    protocol = asyncio.StreamReaderProtocol(reader)\n"
            "    await loop.connect_read_pipe(lambda: protocol, sys.stdin)\n"
            "    while True:\n"
            "        line = await reader.readline()\n"
            "        if not line:\n"
            "            break\n"
            "        text = line.decode().rstrip()\n"
            "        if text.lower() in ('exit', 'quit'):\n"
            "            print('Goodbye!')\n"
            "            break\n"
            "        print(f'[Agent] You said: {text}')\n"
            "        sys.stdout.flush()\n"
            "asyncio.run(main())"
        )
        cmd = [sys.executable, "-u", "-c", script]
        return await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
        )


class ClaudeCodeProvider(Provider):
    """Claude Code CLI provider."""

    name = "claude"
    description = "Anthropic Claude Code"

    def is_available(self) -> bool:
        # Check if claude command exists
        return any(
            Path(p).joinpath("claude").exists()
            for p in os.environ.get("PATH", "").split(os.pathsep)
        )

    def get_command(self, working_dir: Path, initial_prompt: Optional[str] = None) -> List[str]:
        cmd = ["claude", "--dangerously-skip-permissions"]
        if initial_prompt:
            cmd.extend(["-p", initial_prompt])
        return cmd

    async def spawn(
        self,
        session: Session,
        working_dir: Path,
        initial_prompt: Optional[str] = None,
    ) -> asyncio.subprocess.Process:
        cmd = self.get_command(working_dir, initial_prompt)
        return await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ, "TERM": "dumb"},
        )


class CodexProvider(Provider):
    """OpenAI Codex CLI provider."""

    name = "codex"
    description = "OpenAI Codex"

    def is_available(self) -> bool:
        return any(
            Path(p).joinpath("codex").exists()
            for p in os.environ.get("PATH", "").split(os.pathsep)
        )

    def get_command(self, working_dir: Path, initial_prompt: Optional[str] = None) -> List[str]:
        cmd = ["codex", "exec"]
        if initial_prompt:
            cmd.extend(["-p", initial_prompt])
        return cmd

    async def spawn(
        self,
        session: Session,
        working_dir: Path,
        initial_prompt: Optional[str] = None,
    ) -> asyncio.subprocess.Process:
        cmd = self.get_command(working_dir, initial_prompt)
        return await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ, "TERM": "dumb"},
        )


# Provider registry
_PROVIDERS: dict[str, Provider] = {
    "mock": MockProvider(),
    "claude": ClaudeCodeProvider(),
    "codex": CodexProvider(),
}


def get_provider(name: str) -> Optional[Provider]:
    """Get a provider by name."""
    return _PROVIDERS.get(name.lower())


def list_providers() -> List[Provider]:
    """List all registered providers."""
    return list(_PROVIDERS.values())


def register_provider(provider: Provider) -> None:
    """Register a new provider."""
    _PROVIDERS[provider.name.lower()] = provider
