from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import literal, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from app.routers.users import router as users_router
from app.routers.projects import router as projects_router
from app.routers.labels import router as labels_router
from app.routers.tasks import router as tasks_router
from app.routers.comments import router as comments_router

from app.database import get_db

app = FastAPI(title="TaskFlow API")
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(labels_router)
app.include_router(tasks_router)
app.include_router(comments_router)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(literal(1)))
    except OperationalError:
        raise HTTPException(
            status_code=503,
            detail="База данных недоступна",
        )

    return {"status": "ok"}