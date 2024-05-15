"""
Init package

Modules in this file are public facing.
"""

__version__ = "0.0.20"

from .task import Task, TaskParameters

from .curriculum import (
    Metrics,
    Rule,
    Policy,
    PolicyTransition,
    Stage,
    StageGraph,
    StageTransition,
    Curriculum,
)

from .curriculum_utils import *

from .trainer import SubjectHistory, Trainer
