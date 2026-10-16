from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    func,
    ForeignKey,
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('operator', 'admin')",
            name="ck_users_role",
        ),
    )

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    role = Column(
        String(32),
        nullable=False,
        server_default="operator",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Label(Base):
    __tablename__ = "labels"

    __table_args__ = (
        CheckConstraint(
            "color ~ '^#[0-9A-Fa-f]{6}$'",
            name="ck_labels_color",
        ),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False, unique=True)
    color = Column(
        String(7),
        nullable=False,
        server_default="#6b7280",
    )


class Task(Base):
    __tablename__ = "tasks"

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'done')",
            name="ck_tasks_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name="ck_tasks_priority",
        ),
    )

    id = Column(Integer, primary_key=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    assignee_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    label_id = Column(
        Integer,
        ForeignKey("labels.id", ondelete="SET NULL"),
        nullable=True,
    )

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(32),
        nullable=False,
        server_default="open",
    )
    priority = Column(
        String(16),
        nullable=False,
        server_default="medium",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Comment(Base):
    __tablename__ = "comments"

    __table_args__ = (
        CheckConstraint(
            "length(trim(body)) > 0",
            name="ck_comments_body",
        ),
    )

    id = Column(Integer, primary_key=True)
    task_id = Column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    body = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )