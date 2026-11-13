from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import literal, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from app.routers.users import router as users_router
from app.routers.projects import router as projects_router
from app.routers.labels import router as labels_router
from app.routers.tasks import router as tasks_router
from app.routers.comments import router as comments_router

from app.config import settings
from app.database import engine, get_db
from app.logs import configure_logging, logger

configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as connection:
            connection.execute(select(literal(1)))
    except OperationalError:
        logger.critical("API startup failed: PostgreSQL is unavailable")
        raise
    logger.info("TaskFlow API started")
    try:
        yield
    finally:
        logger.info("TaskFlow API stopped")


app = FastAPI(title="TaskFlow API", lifespan=lifespan)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(labels_router)
app.include_router(tasks_router)
app.include_router(comments_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error("Unhandled request error: %s", type(exc).__name__)
        raise

    route = request.scope.get("route")
    route_path = getattr(route, "path", "<unmatched>")
    logger.debug("%s %s -> %d", request.method, route_path, response.status_code)
    return response


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(literal(1)))
    except OperationalError:
        logger.error("Health check failed: PostgreSQL is unavailable")
        raise HTTPException(
            status_code=503,
            detail="База данных недоступна",
        )

    return {"status": "ok"}
