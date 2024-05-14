"""
Init package

Modules in this file are public facing.
"""

__version__ = "0.0.16"

from .task import (
    Task,
    TaskParameters
) # noqa: F401, F403

from .curriculum import (
    Metrics,
    Rule,
    Policy,
    PolicyTransition,
    Stage,
    StageGraph,
    StageTransition,
    Curriculum
)  # noqa: F401, F403

from .curriculum_utils import *  # noqa: F401, F403

from .trainer import (
    SubjectHistory,
    Trainer
)  # noqa: F401, F403
