import enum


class PlanLevel(enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class PlanType(enum.Enum):
    RUN = "RUN"
    BIKE = "BIKE"
    STRENGTH = "STRENGTH"
    HYBRID = "HYBRID"


class WorkoutType(enum.Enum):
    STRENGTH = "STRENGTH"
    RUN = "RUN"
    HYBRID = "HYBRID"


class WorkoutStepType(enum.Enum):
    DISTANCE = "DISTANCE"
    TIME = "TIME"
    REPS = "REPS"
    REST = "REST"
    WARM_UP = "WARM UP"
    COOL_DOWN = "COOL DOWN"
