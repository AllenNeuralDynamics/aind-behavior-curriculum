"""
Base Behavior Models
"""
from __future__ import annotations

import aind_behavior_curriculum

from typing import Any, Callable
from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import core_schema
from semver import Version


class SemVerAnnotation(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> Version:
            Version.parse(value)
            return value

        return core_schema.no_info_after_validator_function(
            validate_from_str, _handler(str)
        )


class AindBehaviorModel(BaseModel):
    """
    Defines Pydantic configurations applied to all behavior models.
    BaseModel: Validate arguments on initialization.
    Configurations:
        - extra='forbid':
            Do not allow a model to be initalized with undocumented parameters.
        - validate_assignment=True:
            Revalidate fields against schema on any change to model instance.
        - validate_defaults=True:
            Validate default fields on subclasses.
        - strict=True:
            Enforce strict typing.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_defaults=True,
        strict=True,
    )

class TaskParameters(AindBehaviorModel):
    pass

class Task(AindBehaviorModel):
    """
    Set of parameters associated with a mouse task.
    Task parameters may be updated and are revalidated on assignment.
    """

    name: str = Field(..., description="Name of the task.", frozen=True)
    description: str = Field("", description="Description of the task.")
    version: str = aind_behavior_curriculum.__version__
    task_parameters: TaskParameters = Field(..., description="Task parameters.", )

    def update_parameters(self, **kwargs) -> None:
         """
         Convenience utility for updating multiple task parameters at once.
         Works across all subclass levels.
         kwargs: dictionary of keyword args
         """
         for key, value in kwargs.items():
             try:
                 self.task_parameters.__setattr__(key, value)
             except Exception as e:
                 raise e
