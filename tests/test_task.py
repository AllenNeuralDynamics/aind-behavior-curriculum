"""
Task Test Suite
"""

import unittest

import example_project as ex

from aind_behavior_curriculum import Task


class TaskTests(unittest.TestCase):
    """Unit tests for valid and invalid Task usage"""

    # Valid Usage
    def test_valid_construction(self):
        ex_parameters = ex.ExampleTaskParameters(field_2=50, field_4=0.8)
        ex_task = ex.ExampleTask(task_parameters=ex_parameters)
        self.assertTrue(
            ex_task.task_parameters.field_2 == 50
            and ex_task.task_parameters.field_4 == 0.8
        )

    def test_valid_parameter_change(self):
        ex_parameters = ex.ExampleTaskParameters()
        ex_task = ex.ExampleTask(task_parameters=ex_parameters)
        ex_task.task_parameters.field_1 = 50
        self.assertTrue(ex_task.task_parameters.field_1 == 50)

    # Invalid Usage
    def test_invalid_construction(self):
        def invalid_type():
            ex_parameters = ex.ExampleTaskParameters(field_1="20")
            ex_task = ex.ExampleTask(  # noqa: F841
                task_parameters=ex_parameters
            )  # noqa: F841

        def invalid_field():
            ex_parameters = ex.ExampleTaskParameters(field_4=5)
            ex_task = ex.ExampleTask(  # noqa: F841
                task_parameters=ex_parameters
            )  # noqa: F841

        self.assertRaises(Exception, invalid_type)
        self.assertRaises(Exception, invalid_field)

    def test_invalid_parameter_change(self):
        def invalid_type():
            ex_parameters = ex.ExampleTaskParameters()
            ex_task = ex.ExampleTask(task_parameters=ex_parameters)
            ex_task.update_parameters(field_1="20")

        def invalid_field():
            ex_parameters = ex.ExampleTaskParameters()
            ex_task = ex.ExampleTask(task_parameters=ex_parameters)
            ex_task.update_parameters(field_4=5)

        self.assertRaises(Exception, invalid_type)
        self.assertRaises(Exception, invalid_field)

    def test_round_trip(self):
        ex_parameters = ex.ExampleTaskParameters()
        ex_task = ex.ExampleTask(task_parameters=ex_parameters)

        # Serialize from Child
        instance_json = ex_task.model_dump_json()
        # Deserialize from Child
        recovered = ex.ExampleTask.model_validate_json(instance_json)
        self.assertTrue(ex_task == recovered)

        # Serialize from Child
        instance_json = ex_task.model_dump_json()
        # Deserialize from Parent
        instance_parent = Task.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.ExampleTask.model_validate_json(parent_json)
        self.assertTrue(ex_task == instance_prime)


if __name__ == "__main__":
    unittest.main()
