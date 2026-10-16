from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate


router = APIRouter(prefix="/v1/projects", tags=["projects"])


def find_project(project_id: int, db: Session) -> Project:
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден",
        )

    return project


def save_changes(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Конфликт ограничений базы данных",
        )


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.scalars(
        select(Project).order_by(Project.id)
    ).all()


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    return find_project(project_id, db)


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
):
    project = Project(**payload.model_dump())

    db.add(project)
    save_changes(db)
    db.refresh(project)

    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
):
    project = find_project(project_id, db)

    for field, value in payload.model_dump(
        exclude_unset=True
    ).items():
        setattr(project, field, value)

    save_changes(db)
    db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = find_project(project_id, db)

    db.delete(project)
    save_changes(db)

    return Response(status_code=204)