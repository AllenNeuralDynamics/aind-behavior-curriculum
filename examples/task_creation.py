from pydantic import (
    Field, 
    field_validator,
    ValidationInfo
)

import aind_behavior_curriculum as abc


class ExampleTask(abc.Task):
    # Required: Define type annotations for strict type checks.
    # Optional: Make fields immutable with the 'frozen=True'.
    field_1: int = Field(0)
    field_2: int = Field(0)
    field_3: float = Field(0.5)
    field_4: float = Field(0.5)
    field_5: str = Field("Immutable Field", frozen=True)

    # Optional: Add additional validation to fields.
    @field_validator('field_1', 'field_2')
    @classmethod
    def check_nonnegative(cls, v: int, info: ValidationInfo):
        if v < 0: 
            raise ValueError(f'{info.field_name} must be nonnegative. {info.field_name}: {v} ')
        return v

    @field_validator('field_3', 'field_4')
    @classmethod
    def check_normalized(cls, v: float, info: ValidationInfo):
        if v < 0 or v > 1: 
            raise ValueError(f'{info.field_name} must be normalized. {info.field_name}: {v}')
        return v


if __name__ == '__main__':
    # Create task, optionally add parameters
    ex = ExampleTask(name='Task', field_2=100, field_4=0.6)
    print(ex)

    # Update Task parameters individually
    ex.field_1 = 100
    ex.field_2 = 200
    print(ex)

    # Or use Task.update_parameters(...)
    ex.update_parameters(description='new description',
                         field_1=123, 
                         field_2=456,
                         field_3=0.8,
                         field_4=0.9)
    print(ex)