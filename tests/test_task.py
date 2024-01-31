"""
Task Test Suite
"""

import unittest
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


class TaskTests(unittest.TestCase):
    """Unit tests for valid and invalid Task usage"""

    # Valid Usage
    def test_valid_construction(self):
        ex = ExampleTask(name="test", field_2=50, field_4=0.8)
        self.assertTrue(ex.field_2 == 50 and ex.field_4 == 0.8)

    def test_valid_parameter_change(self):
        ex = ExampleTask(name="test")
        ex.field_1 = 50
        self.assertTrue(ex.field_1 == 50)

    def test_valid_group_parameter_change(self):
        ex = ExampleTask(name="test")
        ex.update_parameters(
            field_1=123, field_2=456, field_3=0.8, field_4=0.9
        )
        self.assertTrue(
            ex.field_1 == 123
            and ex.field_2 == 456
            and ex.field_3 == 0.8
            and ex.field_4 == 0.9
        )

    # Invalid Usage
    def test_invalid_construction(self):
        def unknown_field():
            ExampleTask(name="test", field_0=0)

        def invalid_type():
            ExampleTask(name="test", field_1="20")

        def invalid_field():
            ExampleTask(name="test", field_4=5)

        self.assertRaises(Exception, unknown_field)
        self.assertRaises(Exception, invalid_type)
        self.assertRaises(Exception, invalid_field)

    def test_invalid_parameter_change(self):
        def unknown_field():
            ex = ExampleTask(name="test")
            ex.field_0 = 0

        def invalid_type():
            ex = ExampleTask(name="test")
            ex.field_1 = "20"

        def invalid_field():
            ex = ExampleTask(name="test")
            ex.field_4 = 5

        self.assertRaises(Exception, unknown_field)
        self.assertRaises(Exception, invalid_type)
        self.assertRaises(Exception, invalid_field)

    def test_invalid_group_parameter_change(self):
        def unknown_field():
            ex = ExampleTask(name="test")
            ex.update_parameters(field_0=0, field_1=1)

        def invalid_type():
            ex = ExampleTask(name="test")
            ex.update_parameters(field_1="20", field_2=50)

        def invalid_field():
            ex = ExampleTask(name="test")
            ex.update_parameters(field_1=-1, field_4=5)

        self.assertRaises(Exception, unknown_field)
        self.assertRaises(Exception, invalid_type)
        self.assertRaises(Exception, invalid_field)

    def test_edit_frozen_attribute(self):
        def edit_frozen():
            ex = ExampleTask(name="test")
            ex.field_5 = "change"

        self.assertRaises(Exception, edit_frozen)


if __name__ == "__main__":
    unittest.main()
