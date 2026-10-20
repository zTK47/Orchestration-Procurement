"""FastAPI app of the Order PDF Orchestration context, separate from the procurement app.

    uvicorn order_pdf_orchestration.infrastructure.main:app --reload --port 8001
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from order_pdf_orchestration.interfaces.api.order_router import router

STATIC_DIR = Path(__file__).parent.parent / "interfaces" / "static"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Order PDF Orchestration",
        description="Free-text order + supplier offer → validated OrderRequest → PDF → supplier.",
        version="0.1.0",
    )
    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def frontend() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
