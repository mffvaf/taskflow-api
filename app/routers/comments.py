from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment
from app.schemas import CommentCreate, CommentRead, CommentUpdate


router = APIRouter(prefix="/v1/comments", tags=["comments"])


def find_comment(comment_id: int, db: Session) -> Comment:
    comment = db.get(Comment, comment_id)

    if comment is None:
        raise HTTPException(
            status_code=404,
            detail="Комментарий не найден",
        )

    return comment


def save_changes(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Конфликт данных: проверьте существование "
                "задачи и автора комментария"
            ),
        )


@router.get("", response_model=list[CommentRead])
def list_comments(
    task_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    query = select(Comment).order_by(Comment.id)

    if task_id is not None:
        query = query.where(Comment.task_id == task_id)

    return db.scalars(query).all()


@router.get("/{comment_id}", response_model=CommentRead)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db),
):
    return find_comment(comment_id, db)


@router.post("", response_model=CommentRead, status_code=201)
def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
):
    comment = Comment(**payload.model_dump())

    db.add(comment)
    save_changes(db)
    db.refresh(comment)

    return comment


@router.patch("/{comment_id}", response_model=CommentRead)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
):
    comment = find_comment(comment_id, db)

    for field, value in payload.model_dump(
        exclude_unset=True
    ).items():
        setattr(comment, field, value)

    save_changes(db)
    db.refresh(comment)

    return comment


@router.delete("/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
):
    comment = find_comment(comment_id, db)

    db.delete(comment)
    save_changes(db)

    return Response(status_code=204)
