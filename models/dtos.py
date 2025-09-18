from datetime import datetime
from pydantic import StringConstraints, BaseModel, EmailStr, computed_field
from typing import Optional, List, Annotated, Dict, Any

from .enums import PlanLevel, PlanType, WorkoutType, WorkoutStepType


class MessageRead(BaseModel):
    id: int
    sender_id: int
    conversation_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=6)]
    is_coach: Optional[bool]
    name: Optional[str] = None
    avatar: Optional[str] = None


class LoginData(BaseModel):
    email: EmailStr
    password: str


class UpdateData(BaseModel):
    name: str
    username: str


class CoachUpdateData(BaseModel):
    description: str
    settings: Optional[Dict[str, Any]] = {}


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    roles: Optional[List[str]] = []

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        from utils.images import get_presigned_url

        if self.avatar:
            return get_presigned_url(self.avatar)
        return None

    class Config:
        from_attributes = True


# --- WorkoutStep ---
class WorkoutStepCreate(BaseModel):
    value: int
    type: WorkoutStepType
    repetitions: Optional[int] = None
    name: str
    description: Optional[str]
    order: int

    class Config:
        from_attributes = True


class WorkoutStepRead(WorkoutStepCreate):
    id: int
    value: int
    type: WorkoutStepType
    name: str
    description: Optional[str] = None
    order: int
    repetitions: Optional[int] = None


# --- Workout ---
class WorkoutCreate(BaseModel):
    title: Annotated[str, StringConstraints(min_length=3, max_length=100)]
    description: Optional[str] = None
    type: WorkoutType
    steps: Optional[List[WorkoutStepCreate]] = []
    order: int

    class Config:
        from_attributes = True


class WorkoutRead(WorkoutCreate):
    id: int
    steps: List[WorkoutStepRead] = []

    class Config:
        from_attributes = True


# --- Day ---
class DayCreate(BaseModel):
    day_of_week: int
    workouts: Optional[List[WorkoutCreate]] = []
    order: int

    class Config:
        from_attributes = True


class DayRead(DayCreate):
    id: int
    workouts: List[WorkoutRead] = []

    class Config:
        from_attributes = True


# --- Week ---
class WeekCreate(BaseModel):
    days: Optional[List[DayCreate]] = []
    order: int

    class Config:
        from_attributes = True


class WeekRead(WeekCreate):
    id: int

    class Config:
        from_attributes = True


# --- Plan ---
class PlanCreate(BaseModel):
    id: Optional[int] = None
    title: Annotated[str, StringConstraints(min_length=5, max_length=100)]
    description: Annotated[str, StringConstraints(min_length=10)]
    level: PlanLevel
    type: PlanType
    features: Optional[List[str]] = []
    price: Optional[int] = 0
    weeks: Optional[List[WeekCreate]] = []

    class Config:
        from_attributes = True


class PlanUpdate(BaseModel):
    title: Optional[Annotated[str, StringConstraints(min_length=5, max_length=100)]] = (
        None
    )
    description: Optional[Annotated[str, StringConstraints(min_length=10)]] = None
    level: Optional[PlanLevel] = None
    weeks: Optional[List[WeekCreate]] = None

    class Config:
        from_attributes = True


class CoachRead(BaseModel):
    id: int
    description: Optional[str] = None
    settings: Dict[str, Any]
    user: UserRead

    class Config:
        from_attributes = True


class PlanRead(BaseModel):
    id: int
    title: str
    description: str
    level: PlanLevel
    type: PlanType
    coach: CoachRead
    weeks: List[WeekRead] = []

    @computed_field
    def weeks_count(self) -> int:
        return len(self.weeks)

    class Config:
        from_attributes = True


class PlanPreviewRead(BaseModel):
    id: int
    title: str
    description: str
    level: PlanLevel
    type: PlanType
    price: int
    features: Optional[List[str]] = []
    coach: CoachRead
    first_week: Optional[WeekRead] = None
    weeks_count: int

    class Config:
        from_attributes = True


class AthletePlanRead(BaseModel):
    id: int
    started_at: datetime
    plan: PlanRead

    class Config:
        from_attributes = True


class CurrentUserRead(UserRead):
    plans: List[AthletePlanRead] = []


class ConversationRead(BaseModel):
    id: int
    user_id: int
    recipient_id: int
    created_at: datetime
    user: UserRead
    recipient: UserRead
    messages: List[MessageRead] = []

    class Config:
        from_attributes = True


class ForgotPasswordData(BaseModel):
    email: str


class ResetPasswordData(BaseModel):
    token: Optional[str]
    password: str


class UpdatePasswordData(BaseModel):
    password: str
    old_password: str


class VerifyEmailData(BaseModel):
    token: str
