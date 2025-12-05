"""
Base behavior pydantic object
"""

import warnings
from typing import Literal, get_args, get_origin

from pydantic import BaseModel, ConfigDict
from semver import Version


class AindBehaviorModel(BaseModel):
    """
    Defines Pydantic configurations applied to all behavior models.
    BaseModel: Validate arguments on initialization.
    Configurations:

    - **extra**: 'forbid'
        Do not allow a model to be initialized with undocumented parameters.
    - **validate_assignment**: True
        Revalidate fields against schema on any change to model instance.
    - **validate_default**: True
        Validate default fields on subclasses.
    - **strict**: True
        Enforce strict typing.
    """

    model_config = ConfigDict(
        extra="forbid",  # Potentially change to 'ignore'
        validate_assignment=True,
        validate_default=True,
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
        validate_default=True,
        strict=True,
        str_strip_whitespace=True,
    )


def coerce_schema_version(cls: type[BaseModel], v: str, version_string: str = "version") -> str:
    """Try to coerce a versioned field to the default schema version defined in the model.

    This function is meant to be used as a pydantic validator for versioned fields.
    """

    try:  # Get the default schema version from the model literal field
        field = cls.model_fields[version_string]
        annotation = field.annotation
        if get_origin(annotation) is Literal:
            _default_schema_version = Version.parse(get_args(cls.model_fields[version_string].annotation)[0])
        else:
            _default_schema_version = Version.parse(cls.model_fields[version_string].default)
    except Exception as e:  # If anything fails, raise a warning and return the original value for the user to handle
        warnings.warn(f"Failed to parse default schema version for {cls.__name__}: {e}")
        return v

    semver = Version.parse(v)
    if semver != _default_schema_version:
        warnings.warn(
            f"Deserialized versioned field {semver}, expected {_default_schema_version}. \n"
            f"Will attempt to coerce. This will be considered a best-effort operation and may lead to a loss of information."
        )
    return str(_default_schema_version)
