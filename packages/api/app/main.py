from fastapi import FastAPI

from app.config import get_settings
from app.logging import set_logging
from app.routers import drugs, health


def create_app():
    settings = get_settings()
    set_logging(settings.log_level)
    
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    app.include_router(drugs.router)
    return app


app = create_app()
