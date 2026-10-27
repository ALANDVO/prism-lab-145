"""WebSocket endpoint for real-time session output."""
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState

from server.core.session_manager import SessionManager
from server.api.sessions import get_session_manager

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/sessions/{session_id}")
async def session_websocket(
    websocket: WebSocket,
    session_id: UUID,
    manager: SessionManager = Depends(get_session_manager),
) -> None:
    """WebSocket endpoint for streaming session output."""
    session = manager.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()

    # Send initial session state
    await websocket.send_json({
        "type": "session_state",
        "session_id": str(session_id),
        "status": session.status.value,
        "provider": session.provider,
        "working_directory": session.working_directory,
    })

    # Send existing messages
    for msg in session.messages:
        await websocket.send_json({
            "type": "message",
            "message": {
                "id": str(msg.id),
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
        })

    # Register output callback
    async def output_callback(text: str) -> None:
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json({
                    "type": "output",
                    "content": text,
                })
            except Exception:
                pass  # Connection closed

    manager.register_output_callback(session_id, output_callback)

    try:
        while True:
            # Wait for messages from client (input)
            data = await websocket.receive_json()

            if data.get("type") == "input":
                input_text = data.get("content", "")
                if input_text:
                    await manager.send_input(session_id, input_text)

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.unregister_output_callback(session_id, output_callback)
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
