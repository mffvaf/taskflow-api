from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task
from app.schemas import TaskCreate, TaskRead, TaskStatus, TaskUpdate


router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


def find_task(task_id: int, db: Session) -> Task:
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена",
        )

    return task


def save_changes(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Конфликт данных: проверьте существование "
                "проекта, исполнителя и метки"
            ),
        )


@router.get("", response_model=list[TaskRead])
def list_tasks(
    project_id: int | None = Query(default=None, gt=0),
    status: TaskStatus | None = None,
    db: Session = Depends(get_db),
):
    query = select(Task).order_by(Task.id)

    if project_id is not None:
        query = query.where(Task.project_id == project_id)

    if status is not None:
        query = query.where(Task.status == status)

    return db.scalars(query).all()


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    return find_task(task_id, db)


@router.post("", response_model=TaskRead, status_code=201)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
):
    task = Task(**payload.model_dump())

    db.add(task)
    save_changes(db)
    db.refresh(task)

    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
):
    task = find_task(task_id, db)

    for field, value in payload.model_dump(
        exclude_unset=True
    ).items():
        setattr(task, field, value)

    save_changes(db)
    db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = find_task(task_id, db)

    db.delete(task)
    save_changes(db)

    return Response(status_code=204)