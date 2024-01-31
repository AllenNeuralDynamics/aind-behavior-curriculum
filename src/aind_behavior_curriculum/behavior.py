"""
Base Behavior Models
"""

from pydantic import BaseModel, ConfigDict, Field


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


class Task(AindBehaviorModel):
    """
    Set of parameters associated with a mouse task.
    Task parameters may be updated and are revalidated on assignment.
    """

    name: str = Field(..., description="Name of the task.", frozen=True)
    description: str = Field("", description="Description of the task.")

    def update_parameters(self, **kwargs) -> None:
        """
        Convenience utility for updating multiple task parameters at once.
        Works across all subclass levels.
        kwargs: dictionary of keyword args
        """
        for key, value in kwargs.items():
            try:
                setattr(self, key, value)
            except Exception as e:
                raise e
