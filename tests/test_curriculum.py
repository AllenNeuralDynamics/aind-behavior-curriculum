"""
Curriculum Test Suite
"""

import unittest

import example_project as ex

import aind_behavior_curriculum as abc


class CurriculumTests(unittest.TestCase):
    """Unit tests for Stage/Curriculum De/Serialization"""

    def test_round_trip_empty_stage(self):
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = ex.StageA(task=taskA)

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Child
        recovered = ex.StageA.model_validate_json(instance_json)
        self.assertTrue(stageA == recovered)

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Parent
        instance_parent = abc.Stage.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.StageA.model_validate_json(parent_json)
        self.assertTrue(stageA == instance_prime)

    def test_round_trip_stage(self):
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = ex.StageA(task=taskA)
        stageA.add_policy_transition(
            abc.INIT_STAGE, ex.StageA_PolicyB(), ex.T1_10()
        )
        stageA.add_policy_transition(
            abc.INIT_STAGE, ex.StageA_PolicyA(), ex.T1_5()
        )
        stageA.add_policy_transition(
            ex.StageA_PolicyA(), ex.StageA_PolicyB(), ex.T1_10()
        )

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Child
        recovered = ex.StageA.model_validate_json(instance_json)
        self.assertTrue(stageA == recovered)

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Parent
        instance_parent = abc.Stage.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.StageA.model_validate_json(parent_json)
        self.assertTrue(stageA == instance_prime)

    def test_round_trip_empty_curriculum(self):
        ex_curr = ex.MyCurriculum(
            name="My Curriculum", metrics=ex.ExampleMetrics()
        )

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Child
        recovered = ex.MyCurriculum.model_validate_json(instance_json)
        self.assertTrue(ex_curr == recovered)

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Parent
        instance_parent = abc.Curriculum.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.MyCurriculum.model_validate_json(parent_json)
        self.assertTrue(ex_curr == instance_prime)

    def test_round_trip_curriculum(self):
        ex_curr = ex.construct_curriculum()

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Child
        recovered = ex.MyCurriculum.model_validate_json(instance_json)
        self.assertTrue(ex_curr == recovered)

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Parent
        instance_parent = abc.Curriculum.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.MyCurriculum.model_validate_json(parent_json)
        self.assertTrue(ex_curr == instance_prime)

    def test_round_trip_edit_task_parameters(self):
        ex_curr = ex.construct_curriculum()

        params = ex_curr.stages[0].get_task_parameters()
        params.field_a = 8
        ex_curr.stages[0].set_task_parameters(params)

        # Serialize from child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from child
        recovered = ex.MyCurriculum.model_validate_json(instance_json)
        self.assertTrue(ex_curr == recovered)

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Parent
        instance_parent = abc.Curriculum.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.MyCurriculum.model_validate_json(parent_json)
        self.assertTrue(ex_curr == instance_prime)

        self.assertTrue(ex_curr.stages[0] == instance_prime.stages[0])


if __name__ == "__main__":
    unittest.main()
