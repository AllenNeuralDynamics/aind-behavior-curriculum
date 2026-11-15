"""
Init package

Modules in this file are public facing.
"""

from importlib.metadata import version as _version

__version__ = _version("aind-behavior-curriculum")

from .curriculum import (
    Curriculum,
    Globals,
    Metrics,
    MetricsProvider,
    Policy,
    PolicyTransition,
    Stage,
    StageEntryRule,
    StageGraph,
    StageTransition,
    create_curriculum,
    make_task_discriminator,
)
from .curriculum_utils import GRADUATED, Graduated, export_diagram, export_json
from .task import Task, TaskParameters, create_task
from .trainer import Trainer, TrainerServer, TrainerState

__all__ = [
    "Curriculum",
    "Globals",
    "Metrics",
    "MetricsProvider",
    "Policy",
    "PolicyTransition",
    "Stage",
    "StageEntryRule",
    "StageGraph",
    "StageTransition",
    "create_curriculum",
    "make_task_discriminator",
    "GRADUATED",
    "Graduated",
    "Task",
    "TaskParameters",
    "create_task",
    "Trainer",
    "TrainerServer",
    "TrainerState",
    "export_diagram",
    "export_json",
]
