"""
Skillhub — FastAPI backend

Run with:
    cd sales-rag
    uvicorn skillhub.backend.main:app --reload --port 8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from skillhub.backend.routers import dashboard, database, logs, security, skills

app = FastAPI(title="Skillhub", version="1.0.0", docs_url="/api/docs")

# Allow the Vite dev server (port 5173) during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dashboard.router)
app.include_router(skills.router)
app.include_router(logs.router)
app.include_router(security.router)
app.include_router(database.router)

# Serve the built React frontend in production
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        index = FRONTEND_DIST / "index.html"
        return FileResponse(index)
