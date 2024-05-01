"""
Base Behavior Models
"""

from __future__ import annotations

from functools import partial
from typing import Any, Callable, TypeVar

from pydantic import Field
from pydantic_core import core_schema
from semver import Version

from aind_behavior_curriculum import (
    AindBehaviorModel,
    AindBehaviorModelExtra,
    __version__,
)


class SemVerAnnotation(str):
    """
    Custom Semantic Version Type.
    Runs additional validation on a string using the semver library.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        """
        Custom validation, Ref:
        https://docs.pydantic.dev/latest/concepts/types/#as-a-method-on-a-custom-type
        """

        def validate_from_str(value: str) -> Version:
            """Pass string through semver library."""
            Version.parse(value)
            return value

        return core_schema.no_info_after_validator_function(
            validate_from_str, _handler(str)
        )


"""Tag fields inside of TaskParameters as Modifiable, seen in schema export"""
ModifiableAttr = partial(Field, allow_modification=True)


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
    version: str = __version__
    task_parameters: TaskParameters = Field(
        ..., description=TaskParameters.__doc__.strip(), validate_default=True
    )
