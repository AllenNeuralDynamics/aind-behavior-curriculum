"""
Example of Task creation
"""

from typing import Literal

from pydantic import Field, ValidationInfo, field_validator

import aind_behavior_curriculum as abc


class ExampleTask(abc.Task):
    """
    Example Task
    """

    # Required: Define type annotations for strict type checks.
    # Make fields immutable with Literal type.
    field_1: int = Field(default=0, ge=0.0)
    field_2: int = Field(default=0, ge=0.0)
    field_3: float = Field(default=0.5, ge=0.0, le=1.0)
    field_4: float = Field(default=0.5, ge=0.0, le=1.0)
    field_5: Literal["Immutable Field"] = "Immutable Field"

    # Optional: Add additional validation to fields.
    @field_validator("field_1", "field_2")
    @classmethod
    def check_something(cls, v: int, info: ValidationInfo):
        """Your validation code here"""
        return v


if __name__ == "__main__":
    # Create task, optionally add parameters
    ex = ExampleTask(name="Task", field_2=100, field_4=0.6)
    print(ex)

    # Update Task parameters individually
    ex.field_1 = 100
    ex.field_2 = 200
    print(ex)

    # Or use Task.update_parameters(...)
    ex.update_parameters(
        description="new description",
        field_1=123,
        field_2=456,
        field_3=0.8,
        field_4=0.9,
    )
    print(ex)
