"""
Base Behavior Models
"""

from __future__ import annotations

from string import capwords
from typing import Annotated, Literal, Optional, Type, TypeVar

from pydantic import Field, create_model

from aind_behavior_curriculum.base import (
    AindBehaviorModel,
    AindBehaviorModelExtra,
)

SEMVER_REGEX = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


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
    description: str = Field(default="", description="Description of the task.")
    task_parameters: TaskParameters = Field(..., description=TaskParameters.__doc__.strip(), validate_default=True)
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


def create_task(
    *,
    name: str,
    task_parameters: Type[TaskParameters],
    version: Optional[str] = None,
    description: str = "",
) -> Type[Task]:
    """
    Factory method for creating a Task object.

    Args:
        name: Name of the task.
        task_parameters: Task parameters.
        version: Task schema version.
        description: Task description.
        stage_name: Optional stage name the `Task` object instance represents.

    Returns:
        Task: Task object instance.
    """

    def _snake_to_pascal(v: str) -> str:
        """Converts a string from snake_case to PascalCase"""
        return "".join(map(capwords, v.split("_")))

    _props = {
        "name": Annotated[
            Literal[name],
            Field(default=name, frozen=True, validate_default=True),
        ],
        "task_parameters": Annotated[
            task_parameters,
            Field(
                description=(task_parameters.__doc__.strip() if task_parameters.__doc__ else ""),
            ),
        ],
        "version": Annotated[
            Literal[version] if version else Optional[str],
            Field(
                default=version,
                frozen=True,
                pattern=SEMVER_REGEX,
                validate_default=True,
            ),
        ],
        "description": Annotated[
            str,
            Field(default=description, frozen=True, validate_default=True),
        ],
    }

    return create_model(_snake_to_pascal(name), __base__=Task, **_props)  # type: ignore
