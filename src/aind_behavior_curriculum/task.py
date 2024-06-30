"""
Base Behavior Models
"""

from __future__ import annotations

from typing import Optional, TypeVar

from pydantic import Field

from aind_behavior_curriculum.base import (
    AindBehaviorModel,
    AindBehaviorModelExtra,
)

SEMVER_REGEX = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"  # noqa: E501


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
    version: Optional[str] = Field(
        default=None,
        pattern=SEMVER_REGEX,
        description="task schema version",
        frozen=True,
    )
    stage_name: Optional[str] = Field(
        default=None,
        description="Optional stage name the `Task` object instance represents.",
    )
