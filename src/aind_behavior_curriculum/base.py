"""
Base behavior pydantic object
"""

from pydantic import BaseModel, ConfigDict


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
        extra="forbid",  # Potentially change to 'ignore'
        validate_assignment=True,
        validate_defaults=True,
        strict=True,
        str_strip_whitespace=True,
    )


class AindBehaviorModelExtra(BaseModel):
    """
    Same as AindBehaviorModel w/ extra = "allow".
    Helpful for deserialization of nested subclasses.
    """

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        validate_defaults=True,
        strict=True,
        str_strip_whitespace=True,
    )
