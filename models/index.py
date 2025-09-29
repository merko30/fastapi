from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import ForeignKey, Enum, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from database import Base


from .enums import PlanLevel, PlanType, WorkoutType, WorkoutStepType


class AthletePlan(Base):
    __tablename__ = "athlete_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )

    # relationships
    athlete = Relationship("Athlete", back_populates="athlete_plans")
    plan = Relationship("Plan", back_populates="athlete_plans")


# an example mapping using the base
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    password_reset_token: Mapped[Optional[str]]
    verified_at: Mapped[Optional[datetime]]
    verify_token: Mapped[Optional[str]]
    name: Mapped[Optional[str]]
    avatar: Mapped[Optional[str]]
    roles: Mapped[List[str]] = mapped_column(JSONB, nullable=False, server_default="[]")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())

    user = Relationship("User", foreign_keys=[user_id])
    recipient = Relationship("User", foreign_keys=[recipient_id])
    messages = Relationship(
        "Message", back_populates="conversation", order_by="Message.created_at.asc()"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())

    conversation = Relationship("Conversation", back_populates="messages")
    sender = Relationship("User")


class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    description: Mapped[Optional[str]]

    user = Relationship("User")
    athlete_plans: Mapped[list["AthletePlan"]] = Relationship(
        back_populates="athlete", cascade="all, delete-orphan"
    )


class Coach(Base):
    __tablename__ = "coaches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    description: Mapped[Optional[str]]
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    plans = Relationship("Plan", back_populates="coach")
    plan_templates = Relationship("PlanTemplate", back_populates="coach")
    user = Relationship("User")


class PlanTemplate(Base):
    __tablename__ = "plan_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    coach_id: Mapped[int] = mapped_column(ForeignKey("coaches.id"))
    title: Mapped[str]
    description: Mapped[str]
    level: Mapped[PlanLevel] = mapped_column(Enum(PlanLevel, name="level"))
    features: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    price: Mapped[Optional[float]]
    type: Mapped[PlanType] = mapped_column(Enum(PlanType, name="type"))

    coach = Relationship("Coach", back_populates="plan_templates")
    plans = Relationship("Plan", back_populates="template")
    weeks = Relationship("Week", back_populates="template")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    coach_id: Mapped[int] = mapped_column(ForeignKey("coaches.id"))
    template_id: Mapped[int] = mapped_column(ForeignKey("plan_templates.id"))
    title: Mapped[str]
    description: Mapped[str]
    level: Mapped[PlanLevel] = mapped_column(
        Enum(PlanLevel, name="plan_level", create_type=False)
    )
    type: Mapped[PlanType] = mapped_column(Enum(PlanType, name="type"))

    coach = Relationship("Coach", back_populates="plans")
    weeks = Relationship("Week", back_populates="plan")
    template = Relationship("PlanTemplate", back_populates="plans")

    athlete_plans: Mapped[list["AthletePlan"]] = Relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class Week(Base):
    __tablename__ = "weeks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("plan_templates.id"), nullable=True
    )
    order: Mapped[int]

    plan = Relationship("Plan", back_populates="weeks")
    template = Relationship("PlanTemplate", back_populates="weeks")
    days = Relationship("Day", back_populates="week")


class Day(Base):
    __tablename__ = "days"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id"))
    day_of_week: Mapped[int]
    # maybe redundant? - use day of the week for order
    order: Mapped[int]

    week = Relationship("Week", back_populates="days")
    workouts = Relationship("Workout", back_populates="day")


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    day_id: Mapped[int] = mapped_column(ForeignKey("days.id"))
    title: Mapped[str]
    description: Mapped[Optional[str]]
    order: Mapped[int]
    type: Mapped[WorkoutType] = mapped_column(Enum(WorkoutType, name="type"))

    day = Relationship("Day", back_populates="workouts")
    steps = Relationship("WorkoutStep", back_populates="workout")


class WorkoutStep(Base):
    __tablename__ = "workout_steps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"))
    name: Mapped[str]
    description: Mapped[Optional[str]]
    order: Mapped[int]
    value: Mapped[int]
    type: Mapped[WorkoutStepType] = mapped_column(
        Enum(WorkoutStepType, name="workout_step_type")
    )
    step_id = mapped_column(ForeignKey("workout_steps.id"), nullable=True)
    repetitions: Mapped[Optional[int]] = mapped_column(nullable=True, default=1)

    parent: Mapped[Optional["WorkoutStep"]] = Relationship(
        "WorkoutStep",
        remote_side=[id],  # points to the "other side"
        back_populates="steps",
    )
    # if repetitive
    steps: Mapped[List["WorkoutStep"]] = Relationship(
        "WorkoutStep", back_populates="parent", cascade="all, delete-orphan"
    )
    workout = Relationship("Workout", back_populates="steps")
