from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from datetime import datetime
from database import get_db
from models import (
    Plan,
    PlanCreate,
    PlanUpdate,
    PlanRead,
    AthletePlan,
    Week,
    Workout,
    WorkoutSet,
    Day,
)
from utils.middleware import require_user_id
from dto import ErrorDTO

router = APIRouter(prefix="/plans")


@router.get("/", response_model=List[PlanRead])
def get_plans(db: Session = Depends(get_db)):
    return db.query(Plan).options(selectinload(Plan.coach)).all()


@router.post("/")
def get_plans(
    data: PlanCreate,
    db: Session = Depends(get_db),
    user_id=Depends(require_user_id),
):

    new_plan = data.model_dump()
    new_plan["user_id"] = user_id
    plan = Plan(**new_plan)
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


@router.get("/{id}", response_model=PlanRead)
def get_plan(id: int, db: Session = Depends(get_db)):
    plan = (
        db.query(Plan).filter(Plan.id == id).options(selectinload(Plan.coach)).first()
    )

    if not plan:
        raise HTTPException(
            404, detail=ErrorDTO(code=404, message="Plan not found").model_dump()
        )

    return plan


@router.put("/{id}", response_model=PlanRead)
def update_plan(
    id: int,
    plan: PlanUpdate,
    db: Session = Depends(get_db),
    user_id=Depends(require_user_id),
):
    plan_in_db = db.query(Plan).filter(Plan.id == id).first()

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


@router.post("/{athlete_id}/{plan_id}")
def assign_plan_to_athlete(
    plan_id: int, athlete_id: int, db: Session = Depends(get_db)
):
    # fetch original plan
    original_plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not original_plan:
        raise HTTPException(404, "Plan not found")

    # create athlete plan entry
    athlete_plan = AthletePlan(
        athlete_id=athlete_id, plan_id=plan_id, started_at=datetime.utcnow()
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
