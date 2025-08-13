"""
Base Behavior Models
"""

from string import capwords
from typing import Annotated, Generic, Literal, Optional, Type, TypeVar

from pydantic import Field, SerializeAsAny, create_model

from aind_behavior_curriculum.base import (
    AindBehaviorModel,
    AindBehaviorModelExtra,
)

SEMVER_REGEX = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


TTaskParameters = TypeVar("TTaskParameters", bound=AindBehaviorModelExtra)

TaskParameters = AindBehaviorModelExtra


class Task(AindBehaviorModel, Generic[TTaskParameters]):
    """
    Base class for all Tasks. A new Task can be created by:
        - Subclassing: class NewTask(TaskParameters)
        - Using the factory method: create_task(...)
        - Passing a type to the generic base: NewTask = Task[MyParameters]
    Holds Task metadata and parameters.
    """

    name: str = Field(..., description="Name of the task.", frozen=True)
    description: str = Field(default="", description="Description of the task.")
    task_parameters: SerializeAsAny[TTaskParameters]
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


TTask = TypeVar("TTask", bound="Task")


def create_task(
    *,
    name: str,
    task_parameters: Type[TTaskParameters],
    version: Optional[str] = None,
    description: str = "",
) -> Type[Task[TTaskParameters]]:
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

    return create_model(
        _snake_to_pascal(name),
        __base__=Task[task_parameters],
        name=Annotated[
            Literal[name],
            Field(default=name, frozen=True, validate_default=True),
        ],
        version=Annotated[
            Literal[version] if version else Optional[str],
            Field(
                default=version,
                frozen=True,
                pattern=SEMVER_REGEX,
                validate_default=True,
            ),
        ],
        description=Annotated[
            str,
            Field(default=description, frozen=True, validate_default=True),
        ],
    )
