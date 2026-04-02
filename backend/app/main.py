from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, graduates, students, universities
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(universities.router)
    app.include_router(graduates.router)
    app.include_router(students.router)
    app.include_router(admin.router)

    return app


app = create_app()
