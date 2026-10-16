from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Label
from app.schemas import LabelCreate, LabelRead, LabelUpdate


router = APIRouter(prefix="/v1/labels", tags=["labels"])


def find_label(label_id: int, db: Session) -> Label:
    label = db.get(Label, label_id)

    if label is None:
        raise HTTPException(
            status_code=404,
            detail="Метка не найдена",
        )

    return label


def save_changes(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Конфликт данных: название метки уже существует",
        )


@router.get("", response_model=list[LabelRead])
def list_labels(db: Session = Depends(get_db)):
    return db.scalars(
        select(Label).order_by(Label.id)
    ).all()


@router.get("/{label_id}", response_model=LabelRead)
def get_label(
    label_id: int,
    db: Session = Depends(get_db),
):
    return find_label(label_id, db)


@router.post("", response_model=LabelRead, status_code=201)
def create_label(
    payload: LabelCreate,
    db: Session = Depends(get_db),
):
    label = Label(**payload.model_dump())

    db.add(label)
    save_changes(db)
    db.refresh(label)

    return label


@router.patch("/{label_id}", response_model=LabelRead)
def update_label(
    label_id: int,
    payload: LabelUpdate,
    db: Session = Depends(get_db),
):
    label = find_label(label_id, db)

    for field, value in payload.model_dump(
        exclude_unset=True
    ).items():
        setattr(label, field, value)

    save_changes(db)
    db.refresh(label)

    return label


@router.delete("/{label_id}", status_code=204)
def delete_label(
    label_id: int,
    db: Session = Depends(get_db),
):
    label = find_label(label_id, db)

    db.delete(label)
    save_changes(db)

    return Response(status_code=204)