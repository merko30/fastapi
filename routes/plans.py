from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
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
    PlanPreviewRead,
    CoachRead,
)
from utils.middleware import require_user_id
from dto import ErrorDTO

router = APIRouter(prefix="/plans")


def generate_plan(
    db: Session, data: PlanCreate, coach_id: int, model_class=PlanTemplate
) -> Plan:
    plan_dict = data.model_dump(exclude={"weeks"})
    plan_dict["level"] = plan_dict["level"].value
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


@router.post("/{athlete_id}/{plan_template_id}")
def assign_plan_to_athlete(
    plan_template_id: int, athlete_id: int, db: Session = Depends(get_db)
):
    # fetch original plan
    original_plan = (
        db.query(PlanTemplate).filter(PlanTemplate.id == plan_template_id).first()
    )
    if not original_plan:
        raise HTTPException(404, "Plan not found")

    # create athlete plan entry
    athlete_plan = AthletePlan(
        athlete_id=athlete_id, plan_id=plan_template_id, started_at=datetime.utcnow()
    )
    db.add(athlete_plan)
    db.flush()

    # deep copy weeks
    for week in original_plan.weeks:
        new_week = Week(plan_id=athlete_plan.id)
        db.add(new_week)
        db.flush()

        # copy days
        for day in week.days:
            new_day = Day(week_id=new_week.id, day_of_week=day.day_of_week)
            db.add(new_day)
            db.flush()

            # copy workouts
            for workout in day.workouts:
                new_workout = Workout(
                    day_id=new_day.id,
                    title=workout.title,
                    description=workout.description,
                    type=workout.type,
                )
                db.add(new_workout)
                db.flush()

                # copy sets
                for s in workout.sets:
                    new_set = WorkoutSet(
                        workout_id=new_workout.id,
                        active_value=s.active_value,
                        active_measure_type=s.active_measure_type,
                        recovery_value=s.recovery_value,
                        recovery_measure_type=s.recovery_measure_type,
                    )
                    db.add(new_set)

    db.commit()
    return athlete_plan
