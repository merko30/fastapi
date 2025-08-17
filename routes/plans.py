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
    Coach,
    WorkoutType,
    WorkoutSetMeasureType,
)
from utils.middleware import require_user_id
from dto import ErrorDTO

router = APIRouter(prefix="/plans")


@router.get("/", response_model=List[PlanRead])
def get_plans(db: Session = Depends(get_db)):
    return db.query(Plan).options(selectinload(Plan.coach)).all()


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

    # create plan
    plan_dict = data.model_dump(exclude={"weeks"})
    plan = Plan(**plan_dict, coach_id=coach.id)
    db.add(plan)
    db.flush()  # flush to get plan.id

    # create nested weeks, days, workouts, sets
    for week_data in getattr(data, "weeks", []):
        week = Week(plan_id=plan.id)
        db.add(week)
        db.flush()

        for day_data in getattr(week_data, "days", []):
            day = Day(week_id=week.id, day_of_week=day_data.day_of_week)
            db.add(day)
            db.flush()

            for workout_data in getattr(day_data, "workouts", []):
                workout_fields = workout_data.model_dump(exclude={"sets"})
                workout_fields["type"] = WorkoutType(workout_fields["type"].value).value
                workout = Workout(day_id=day.id, **workout_fields)
                db.add(workout)
                db.flush()

                for set_data in getattr(workout_data, "sets", []):
                    set_data["active_measure_type"] = WorkoutSetMeasureType(
                        str(set_data["active_measure_type"].value).upper()
                    )
                    set_data["recovery_measure_type"] = WorkoutSetMeasureType(
                        str(set_data["recovery_measure_type"].value).upper()
                    )
                    workout_set = WorkoutSet(
                        workout_id=workout.id, **set_data.model_dump()
                    )
                    db.add(workout_set)

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
