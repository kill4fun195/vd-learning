from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.models.user import User  # noqa: F401 — register model with metadata


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    from app.services.cpu_service import cpu_loader
    cpu_loader.stop()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Simple FastAPI service with User CRUD (AWS RDS), JWT authentication, "
        "and avatar upload to AWS S3. Use **/docs** to try the APIs."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
