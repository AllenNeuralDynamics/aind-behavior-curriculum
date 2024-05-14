"""
Base Behavior Models
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import Field

from aind_behavior_curriculum.base import (
    AindBehaviorModel,
    AindBehaviorModelExtra,
)

TTask = TypeVar("TTask", bound="Task")


class TaskParameters(AindBehaviorModelExtra):
    """
    Set of parameters associated with a subject task.
    Subclass with Task Parameters.
    """

    pass


class Task(AindBehaviorModel):
    """
    Base Task Primitive.
    Holds Task metadata and parameters.
    """

    name: str = Field(..., description="Name of the task.", frozen=True)
    description: str = Field(
        default="", description="Description of the task."
    )
    task_parameters: TaskParameters = Field(
        ..., description=TaskParameters.__doc__.strip(), validate_default=True
    )
