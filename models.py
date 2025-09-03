import enum
from datetime import datetime, timezone
from pydantic import constr, BaseModel, EmailStr
from typing import Optional, List
from sqlalchemy import ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from database import Base


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
    name: Mapped[Optional[str]]
    avatar: Mapped[Optional[str]]


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

    plans = Relationship("Plan", back_populates="coach")


class PlanLevel(enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class PlanTemplate(Base):
    __tablename__ = "plan_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    coach_id: Mapped[int] = mapped_column(ForeignKey("coaches.id"))
    title: Mapped[str]
    description: Mapped[str]
    level: Mapped[PlanLevel] = mapped_column(Enum(PlanLevel, name="level"))
    features: Mapped[Optional[str]]
    price: Mapped[Optional[float]]

    coach = Relationship("Coach", back_populates="plan_templates")
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

    coach = Relationship("Coach", back_populates="plans")
    weeks = Relationship("Week", back_populates="plan")
    template = Relationship("Template", back_populates="template")

    athlete_plans: Mapped[list["AthletePlan"]] = Relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class Week(Base):
    __tablename__ = "weeks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("plan_templates.id"))

    plan = Relationship("Plan", back_populates="weeks")
    template = Relationship("PlanTemplate", back_populates="weeks")
    days = Relationship("Day", back_populates="week")


class Day(Base):
    __tablename__ = "days"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id"))
    day_of_week: Mapped[int]

    week = Relationship("Week", back_populates="days")
    workouts = Relationship("Workout", back_populates="day")


class WorkoutType(enum.Enum):
    REST = "REST"
    STRENGTH = "STRENGTH"
    RUN = "RUN"


class WorkoutSetMeasureType(enum.Enum):
    DISTANCE = "DISTANCE"
    TIME = "TIME"
    REPS = "REPS"


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    day_id: Mapped[int] = mapped_column(ForeignKey("days.id"))
    title: Mapped[str]
    description: Mapped[Optional[str]]
    type: Mapped[WorkoutType] = mapped_column(Enum(WorkoutType, name="type"))

    day = Relationship("Day", back_populates="workouts")
    sets = Relationship("WorkoutSet", back_populates="workout")


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"))
    active_value: Mapped[int]
    active_measure_type: Mapped[WorkoutSetMeasureType] = mapped_column(
        Enum(WorkoutSetMeasureType, name="workout_set_measure_type")
    )
    recovery_value: Mapped[int] = mapped_column(nullable=True)
    recovery_measure_type: Mapped[WorkoutSetMeasureType] = mapped_column(
        Enum(WorkoutSetMeasureType, name="workout_set_measure_type", nullable=True)
    )

    workout = Relationship("Workout", back_populates="sets")


class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=6)
    is_coach: Optional[bool]
    name: Optional[str] = None
    avatar: Optional[str] = None


class LoginData(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    name: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


# --- WorkoutSet ---
class WorkoutSetCreate(BaseModel):
    active_value: int
    active_measure_type: WorkoutSetMeasureType
    recovery_value: Optional[int] = None
    recovery_measure_type: Optional[WorkoutSetMeasureType] = None

    class Config:
        from_attributes = True


class WorkoutSetRead(WorkoutSetCreate):
    id: int


# --- Workout ---
class WorkoutCreate(BaseModel):
    title: constr(min_length=3, max_length=100)
    description: Optional[str] = None
    type: WorkoutType
    sets: Optional[List[WorkoutSetCreate]] = []

    class Config:
        from_attributes = True


class WorkoutRead(BaseModel):
    id: int
    sets: List[WorkoutSetRead] = []

    class Config:
        from_attributes = True


# --- Day ---
class DayCreate(BaseModel):
    day_of_week: int
    workouts: Optional[List[WorkoutCreate]] = []

    class Config:
        from_attributes = True


class DayRead(BaseModel):
    id: int
    workouts: List[WorkoutRead] = []

    class Config:
        from_attributes = True


# --- Week ---
class WeekCreate(BaseModel):
    days: Optional[List[DayCreate]] = []

    class Config:
        from_attributes = True


class WeekRead(BaseModel):
    id: int
    days: List[DayRead] = []

    class Config:
        from_attributes = True


# --- Plan ---
class PlanCreate(BaseModel):
    title: constr(min_length=5, max_length=100)
    description: constr(min_length=10)
    level: PlanLevel
    weeks: Optional[List[WeekCreate]] = []

    class Config:
        from_attributes = True


class PlanUpdate(BaseModel):
    title: Optional[constr(min_length=5, max_length=100)] = None
    description: Optional[constr(min_length=10)] = None
    level: Optional[PlanLevel] = None
    weeks: Optional[List[WeekCreate]] = None

    class Config:
        from_attributes = True


class CoachRead(BaseModel):
    description: Optional[str] = None


class PlanRead(BaseModel):
    id: int
    title: str
    description: str
    level: PlanLevel
    coach: CoachRead
    weeks: List[WeekRead] = []

    class Config:
        from_attributes = True
