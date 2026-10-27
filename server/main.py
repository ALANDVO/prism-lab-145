"""Main FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from server.api.sessions import router as sessions_router, set_session_manager
from server.api.websocket import router as websocket_router
from server.core.session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global session manager
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
        set_session_manager(_session_manager)
    return _session_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _session_manager
    logger.info("Starting Prism Lab 145 server...")
    _session_manager = SessionManager()
    set_session_manager(_session_manager)
    yield
    logger.info("Shutting down...")
    await _session_manager.shutdown()


app = FastAPI(
    title="Prism Lab 145",
    description="Agent harness control surface - control AI coding agents from a web UI",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(sessions_router)
app.include_router(websocket_router)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "prism-lab-145"}


# Serve React frontend in production
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str, request: Request) -> HTMLResponse:
        """Serve the React frontend for all non-API routes."""
        # Don't serve frontend for API routes
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")

        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            return HTMLResponse(
                content="""
                <html>
                    <body>
                        <h1>Prism Lab 145</h1>
                        <p>Frontend not built. Run <code>npm run build</code> in frontend directory.</p>
                    </body>
                </html>
                """,
                status_code=200,
            )
else:
    @app.get("/")
    async def root() -> dict:
        return {
            "message": "Prism Lab 145 API",
            "docs": "/docs",
            "frontend": "Not built - run 'npm run build' in frontend directory",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
