from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import admin, auth, health, questionnaires, setores, senhas


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(setores.router, prefix="/setores", tags=["setores"])
    app.include_router(senhas.router, prefix="/senhas", tags=["senhas"])
    app.include_router(questionnaires.router, prefix="/formularios", tags=["formularios"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])

    return app


app = create_app()
