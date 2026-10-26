from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.api.routes import records, validate, findings, dashboard


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gracenote Metadata Quality Validator",
        description="Validation engine for Gracenote metadata records",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(records.router, prefix="/api", tags=["records"])
    app.include_router(validate.router, prefix="/api", tags=["validate"])
    app.include_router(findings.router, prefix="/api", tags=["findings"])
    app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
