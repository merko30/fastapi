from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, event, Connection, text
from datetime import datetime
import json

from database import get_db
from models import (
    Plan,
    PlanTemplate,
    PlanCreate,
    PlanUpdate,
    PlanRead,
    AthletePlan,
    Week,
    Workout,
    WorkoutSet,
    Day,
    Coach,
    Athlete,
    PlanPreviewRead,
    CoachRead,
    Conversation,
    Message,
)
from utils.middleware import require_user_id
from dto import ErrorDTO

router = APIRouter(prefix="/plans")


def generate_plan(
    db: Session, data: PlanCreate, coach_id: int, model_class=PlanTemplate
) -> Plan:
    is_template = model_class == PlanTemplate
    fields_to_exclude = (
        {"id", "coach", "features", "price", "weeks"} if not is_template else {"weeks"}
    )
    plan_dict = data.model_dump(exclude=fields_to_exclude)
    plan_dict["level"] = plan_dict["level"].value
    plan_dict["type"] = plan_dict["type"].value
    plan_dict["template_id"] = None if is_template else data.id
    plan = model_class(**plan_dict, coach_id=coach_id)
    db.add(plan)
    db.flush()  # Ensure plan.id is available

    for week_data in getattr(data, "weeks", []):
        week = Week(
            template_id=(plan.id if model_class == PlanTemplate else None),
            plan_id=plan.id if model_class == Plan else None,
            **week_data.model_dump(exclude={"days"})
        )
        db.add(week)
        db.flush()

        for day_data in getattr(week_data, "days", []):
            day = Day(week_id=week.id, **day_data.model_dump(exclude={"workouts"}))
            db.add(day)
            db.flush()

            for workout_data in getattr(day_data, "workouts", []):
                workout = Workout(
                    **workout_data.model_dump(exclude={"sets"}), day_id=day.id
                )
                db.add(workout)
                db.flush()

                for set_data in getattr(workout_data, "sets", []):
                    workout_set = WorkoutSet(
                        **set_data.model_dump(), workout_id=workout.id
                    )
                    db.add(workout_set)

    db.commit()
    db.refresh(plan)
    return plan


@router.get("/", response_model=List[PlanRead])
def get_plans(db: Session = Depends(get_db)):
    return (
        db.query(PlanTemplate)
        .options(selectinload(PlanTemplate.coach).selectinload(Coach.user))
        .all()
    )


# coach generating a plan template
@router.post("/", response_model=PlanRead)
def create_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
    user_id=Depends(require_user_id),
):
    coach = db.query(Coach).filter(Coach.user_id == user_id).first()
    if not coach:
        raise HTTPException(
            400, detail=ErrorDTO(code=400, message="You are not a coach").model_dump()
        )

    plan = generate_plan(db, data, coach.id, model_class=PlanTemplate)
    return plan


@router.get("/{id}", response_model=PlanPreviewRead)
def get_plan_preview(id: int, db: Session = Depends(get_db)):
    # fetch plan
    plan = db.query(PlanTemplate).get(id)

    # count weeks separately
    weeks_count = db.query(func.count(Week.id)).filter(Week.template_id == id).scalar()

    # fetch first week
    first_week = (
        db.query(Week).filter(Week.template_id == id).order_by(Week.order.asc()).first()
    )

    return PlanPreviewRead.model_validate(
        {
            "id": plan.id,
            "title": plan.title,
            "description": plan.description,
            "level": plan.level,
            "type": plan.type,
            "price": plan.price,
            "features": plan.features,
            "coach": CoachRead.model_validate(plan.coach),
            "first_week": first_week,
            "weeks_count": weeks_count,
        }
    )


@router.put("/{id}", response_model=PlanRead)
def update_plan(
    id: int,
    plan: PlanUpdate,
    db: Session = Depends(get_db),
    user_id=Depends(require_user_id),
):
    plan_in_db = db.query(PlanTemplate).filter(PlanTemplate.id == id).first()

    if not plan_in_db:
        raise HTTPException(
            404, detail=ErrorDTO(code=404, message="Plan not found").model_dump()
        )

    update_data = plan.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan_in_db, key, value)
    db.commit()
    db.refresh(plan_in_db)

    return plan_in_db


@router.post("/{plan_template_id}/order")
def assign_plan_to_athlete(
    plan_template_id: int,
    user_id: int = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    # fetch original plan
    plan_template = (
        db.query(PlanTemplate).where(PlanTemplate.id == plan_template_id).first()
    )
    if not plan_template:
        raise HTTPException(404, "Plan not found")

    athlete = db.query(Athlete).where(Athlete.user_id == user_id).first()

    if not athlete:
        raise HTTPException(400, "You are not an athlete")

    new_plan = generate_plan(
        db,
        PlanCreate.model_validate(plan_template),
        plan_template.coach_id,
        model_class=Plan,
    )

    athlete_plan = AthletePlan(
        athlete_id=athlete.id,
        plan_id=new_plan.id,
        started_at=datetime.utcnow(),
    )

    db.add(athlete_plan)
    db.commit()
    db.refresh(athlete_plan)
    return {"message": "Plan ordered successfully"}


@event.listens_for(AthletePlan, "after_insert")
def receive_after_insert(mapper, connection: Connection, target):
    sql = text(
        """
        SELECT
            ap.id AS athlete_plan_id,
            ap.athlete_id,
            ap.plan_id,
            ap.started_at,
            
            p.id AS plan_id,
            p.title AS plan_title,
            
            c.id AS coach_id,
            c.settings AS settings,
            
            u.id AS user_id,
            u.username AS username,
            u.email AS email,
            u.name AS name,

            u2.id AS athlete_user_id,
            u2.name AS athlete_name,
            u2.username AS athlete_username

        FROM athlete_plans ap
        JOIN plans p ON ap.plan_id = p.id
        JOIN coaches c ON p.coach_id = c.id
        JOIN athletes a ON ap.athlete_id = a.id
        JOIN users u2 ON a.user_id = u2.id
        JOIN users u ON c.user_id = u.id
        WHERE ap.id = :id
        """
    )

    ap = connection.execute(sql, {"id": target.id})

    row = ap.first()
    dict = row._asdict()

    settings = dict["settings"]

    if settings and settings["send_welcome_message"] and settings["welcome_message"]:
        athlete_user_id = dict["athlete_user_id"]
        athlete_name = dict["athlete_name"]
        athlete_username = dict["athlete_username"]
        coach_user_id = dict["user_id"]

        message = settings["welcome_message"].replace(
            "{athlete_name}", athlete_name if athlete_name else athlete_username
        )

        conversation_insert_result = connection.execute(
            text(
                """
                    INSERT INTO conversations (user_id, recipient_id, created_at) VALUES (:user_id, :recipient_id, :created_at) RETURNING id
                """
            ),
            {
                "user_id": coach_user_id,
                "recipient_id": athlete_user_id,
                "created_at": datetime.utcnow(),
            },
        )

        conversation_id = conversation_insert_result.scalar_one()

        connection.execute(
            text(
                """
                INSERT INTO messages (conversation_id, sender_id, content, created_at)
                VALUES (:conversation_id, :sender_id, :content, :created_at)
            """
            ),
            {
                "conversation_id": conversation_id,
                "sender_id": coach_user_id,
                "content": message,
                "created_at": datetime.utcnow(),
            },
        )
