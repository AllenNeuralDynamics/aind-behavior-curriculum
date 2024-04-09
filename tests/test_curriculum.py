"""
Curriculum Test Suite
"""

import unittest

import example_project as ex

from aind_behavior_curriculum import INIT_STAGE, Curriculum, Stage


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
        instance_parent = Stage.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.StageA.model_validate_json(parent_json)
        self.assertTrue(stageA == instance_prime)

    def test_round_trip_stage(self):
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = ex.StageA(task=taskA)
        stageA.add_policy_transition(INIT_STAGE, ex.stageA_policyB, ex.t1_10)
        stageA.add_policy_transition(INIT_STAGE, ex.stageA_policyA, ex.t1_5)
        stageA.add_policy_transition(
            ex.stageA_policyA, ex.stageA_policyB, ex.t1_10
        )

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Child
        recovered = ex.StageA.model_validate_json(instance_json)
        self.assertTrue(stageA == recovered)

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Parent
        instance_parent = Stage.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.StageA.model_validate_json(parent_json)
        self.assertTrue(stageA == instance_prime)

    def test_round_trip_empty_curriculum(self):
        ex_curr = ex.MyCurriculum(name="My Curriculum")

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Child
        recovered = ex.MyCurriculum.model_validate_json(instance_json)
        self.assertTrue(ex_curr == recovered)

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Parent
        instance_parent = Curriculum.model_validate_json(instance_json)
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
        instance_parent = Curriculum.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.MyCurriculum.model_validate_json(parent_json)
        self.assertTrue(ex_curr == instance_prime)

    def test_round_trip_edit_task_parameters(self):
        ex_curr = ex.construct_curriculum()

        stage_0 = ex_curr.see_stages()[0]
        params = stage_0.get_task_parameters()
        params.field_a = 8
        stage_0.set_task_parameters(params)

        # Serialize from child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from child
        recovered = ex.MyCurriculum.model_validate_json(instance_json)
        self.assertTrue(ex_curr == recovered)

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Parent
        instance_parent = Curriculum.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.MyCurriculum.model_validate_json(parent_json)
        self.assertTrue(ex_curr == instance_prime)
        self.assertTrue(stage_0 == instance_prime.see_stages()[0])


if __name__ == "__main__":
    unittest.main()
