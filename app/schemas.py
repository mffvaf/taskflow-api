from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


DisplayName = Annotated[
    str,
    Field(min_length=1, max_length=255),
]

UserRole = Literal["operator", "admin"]


class InputSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class UserCreate(InputSchema):
    email: Annotated[EmailStr, Field(max_length=255)]
    display_name: DisplayName
    role: UserRole = "operator"


class UserUpdate(InputSchema):
    email: Annotated[EmailStr, Field(max_length=255)] = None
    display_name: DisplayName = None
    role: UserRole = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    role: UserRole
    created_at: datetime


ProjectName = Annotated[
    str,
    Field(min_length=1, max_length=200),
]


class ProjectCreate(InputSchema):
    name: ProjectName
    description: str | None = None


class ProjectUpdate(InputSchema):
    name: ProjectName = None
    description: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime

LabelName = Annotated[
    str,
    Field(min_length=1, max_length=64),
]

LabelColor = Annotated[
    str,
    Field(pattern=r"^#[0-9A-Fa-f]{6}$"),
]


class LabelCreate(InputSchema):
    name: LabelName
    color: LabelColor = "#6b7280"


class LabelUpdate(InputSchema):
    name: LabelName = None
    color: LabelColor = None


class LabelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str

PositiveId = Annotated[int, Field(gt=0)]

TaskTitle = Annotated[
    str,
    Field(min_length=1, max_length=200),
]

TaskStatus = Literal["open", "in_progress", "done"]
TaskPriority = Literal["low", "medium", "high"]


class TaskCreate(InputSchema):
    project_id: PositiveId
    assignee_id: PositiveId | None = None
    label_id: PositiveId | None = None
    title: TaskTitle
    description: str | None = None
    status: TaskStatus = "open"
    priority: TaskPriority = "medium"


class TaskUpdate(InputSchema):
    project_id: PositiveId = None
    assignee_id: PositiveId | None = None
    label_id: PositiveId | None = None
    title: TaskTitle = None
    description: str | None = None
    status: TaskStatus = None
    priority: TaskPriority = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    assignee_id: int | None
    label_id: int | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime

CommentBody = Annotated[
    str,
    Field(min_length=1),
]


class CommentCreate(InputSchema):
    task_id: PositiveId
    author_id: PositiveId
    body: CommentBody


class CommentUpdate(InputSchema):
    task_id: PositiveId = None
    author_id: PositiveId = None
    body: CommentBody = None


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    body: str
    created_at: datetime