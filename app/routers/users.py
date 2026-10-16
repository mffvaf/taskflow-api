from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserRead, UserUpdate


router = APIRouter(prefix="/v1/users", tags=["users"])


def find_user(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден",
        )

    return user


def save_changes(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Конфликт данных: email уже занят "
                "или пользователь связан с комментариями"
            ),
        )


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(
        select(User).order_by(User.id)
    ).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return find_user(user_id, db)


@router.post("", response_model=UserRead, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    user = User(**payload.model_dump())

    db.add(user)
    save_changes(db)
    db.refresh(user)

    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
):
    user = find_user(user_id, db)

    for field, value in payload.model_dump(
        exclude_unset=True
    ).items():
        setattr(user, field, value)

    save_changes(db)
    db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = find_user(user_id, db)

    db.delete(user)
    save_changes(db)

    return Response(status_code=204)