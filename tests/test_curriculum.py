"""
Curriculum Test Suite
"""

import unittest

import example_project as ex
import example_project_2 as ex2
from pydantic import BaseModel, Field, PydanticUserError

from aind_behavior_curriculum import (
    Curriculum,
    Metrics,
    Policy,
    Stage,
    StageGraph,
    TaskParameters,
    create_curriculum,
)
from aind_behavior_curriculum.curriculum import make_task_discriminator


def init_stage_rule(metrics: Metrics, task_params: TaskParameters) -> TaskParameters:
    """
    Trivially pass the default
    """
    return task_params


INIT_STAGE = Policy(init_stage_rule)


class CurriculumTests(unittest.TestCase):
    """Unit tests for Stage/Curriculum De/Serialization"""

    def test_round_trip_without_policies(self):
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = Stage(name="StageA", task=taskA)

        # Check if the jsons produced by cross serialization are equal
        instance_json = stageA.model_dump_json()
        # Use the generic deserializer
        recovered = Stage.model_validate_json(instance_json)
        recovered_json = recovered.model_dump_json()
        # Compare the two jsons
        self.assertEqual(instance_json, recovered_json)
        self.assertEqual(stageA, recovered)

    def test_round_trip_with_policies(self):
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = Stage(name="StageA", task=taskA)

        stageA.add_policy_transition(INIT_STAGE, ex.stageA_policyB, ex.t1_10)
        stageA.add_policy_transition(INIT_STAGE, ex.stageA_policyA, ex.t1_5)
        stageA.add_policy_transition(ex.stageA_policyA, ex.stageA_policyB, ex.t1_10)

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Child
        recovered = Stage.model_validate_json(instance_json)
        recovered_json = recovered.model_dump_json()
        self.assertEqual(instance_json, recovered_json)
        self.assertEqual(stageA.see_policies(), recovered.see_policies())
        self.assertEqual(stageA, recovered)

    def test_round_trip_empty_curriculum(self):
        ex_curr = ex.MyCurriculum(name="My Curriculum")

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Child
        recovered = ex.MyCurriculum.model_validate_json(instance_json)
        self.assertEqual(ex_curr, recovered)

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Parent
        instance_parent = Curriculum.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.MyCurriculum.model_validate_json(parent_json)
        self.assertEqual(ex_curr, instance_prime)

    def test_round_trip_curriculum(self):
        ex_curr = ex.construct_curriculum()

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Child
        recovered = ex.MyCurriculum.model_validate_json(instance_json)

        self.assertEqual(ex_curr, recovered)

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Parent
        instance_parent = Curriculum.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.MyCurriculum.model_validate_json(parent_json)
        self.assertEqual(ex_curr, instance_prime)

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
        self.assertEqual(ex_curr, recovered)

        # Serialize from Child
        instance_json = ex_curr.model_dump_json()
        # Deserialize from Parent
        instance_parent = Curriculum.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = ex.MyCurriculum.model_validate_json(parent_json)
        self.assertEqual(ex_curr, instance_prime)
        self.assertEqual(instance_prime.see_stages()[0], stage_0)

    def test_add_policies_and_policy_transitions(self):
        """
        Constructing a diamond graph and checking if
        stored polices and policy transitions are correct.

        For diamond graph:
        A -> B -> D
        A -> C -> D

        Testing:
        Stage contains [A, B, C, D]
        A's transitions are [B, C]
        B's transitions are [D]
        C's transitions are [D]
        D's transitions are [].
        """

        dummy_task = ex2.DummyTask(task_parameters=ex2.DummyParameters())
        stageA = Stage(name="Stage A", task=dummy_task)

        stageA.add_policy(ex2.policy_1)
        stageA.set_start_policies(ex2.policy_1)

        stageA.add_policy_transition(ex2.policy_1, ex2.policy_2, ex2.m1_policy_transition)
        stageA.add_policy_transition(ex2.policy_1, ex2.policy_3, ex2.m1_policy_transition)

        stageA.add_policy_transition(ex2.policy_2, ex2.policy_4, ex2.m1_policy_transition)
        stageA.add_policy_transition(ex2.policy_3, ex2.policy_4, ex2.m1_policy_transition)

        self.assertEqual(
            stageA.see_policies(),
            [ex2.policy_1, ex2.policy_2, ex2.policy_3, ex2.policy_4],
        )
        self.assertEqual(
            stageA.see_policy_transitions(ex2.policy_1),
            [
                (ex2.m1_policy_transition, ex2.policy_2),
                (ex2.m1_policy_transition, ex2.policy_3),
            ],
        )
        self.assertEqual(
            stageA.see_policy_transitions(ex2.policy_2),
            [(ex2.m1_policy_transition, ex2.policy_4)],
        )
        self.assertEqual(
            stageA.see_policy_transitions(ex2.policy_3),
            [(ex2.m1_policy_transition, ex2.policy_4)],
        )
        self.assertEqual(stageA.see_policy_transitions(ex2.policy_4), [])

    def test_add_stage_and_stage_transitions(self):
        """
        Constructing a diamond graph and checking if
        stored stages and stage transitions are correct.

        For diamond graph:
        A -> B -> D
        A -> C -> D

        Testing:
        Curr contains [A, B, C, D]
        A's transitions are [B, C]
        B's transitions are [D]
        C's transitions are [D]
        D's transitions are [].
        """

        dummy_task = ex2.DummyTask(task_parameters=ex2.DummyParameters())
        stageA = Stage(name="Stage A", task=dummy_task)
        stageB = Stage(name="Stage B", task=dummy_task)
        stageC = Stage(name="Stage C", task=dummy_task)
        stageD = Stage(name="Stage D", task=dummy_task)

        ex_curr = ex2.MyCurriculum()
        ex_curr.add_stage(stageA)
        ex_curr.add_stage_transition(stageA, stageB, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageA, stageC, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageB, stageD, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageC, stageD, ex2.m1_stage_transition)

        self.assertEqual(ex_curr.see_stages(), [stageA, stageB, stageC, stageD])
        self.assertEqual(
            ex_curr.see_stage_transitions(stageA),
            [
                (ex2.m1_stage_transition, stageB),
                (ex2.m1_stage_transition, stageC),
            ],
        )
        self.assertEqual(
            ex_curr.see_stage_transitions(stageB),
            [(ex2.m1_stage_transition, stageD)],
        )
        self.assertEqual(
            ex_curr.see_stage_transitions(stageC),
            [(ex2.m1_stage_transition, stageD)],
        )
        self.assertEqual(ex_curr.see_stage_transitions(stageD), [])

    def test_reorder_policy_transitions(self):
        """
        Constructing a diamond graph and reordering
        priority of two branches.

        For diamond graph:
        A -> B -> D
        A -> C -> D
        and swapping priority of B and C.

        Testing:
        A's transitions are reordered
        from [B, C] to [C, B].
        """
        dummy_task = ex2.DummyTask(task_parameters=ex2.DummyParameters())
        stageA = Stage(name="Stage A", task=dummy_task)

        stageA.add_policy(ex2.policy_1)
        stageA.set_start_policies(ex2.policy_1)

        stageA.add_policy_transition(ex2.policy_1, ex2.policy_2, ex2.m1_policy_transition)
        stageA.add_policy_transition(ex2.policy_1, ex2.policy_3, ex2.m1_policy_transition)

        stageA.add_policy_transition(ex2.policy_2, ex2.policy_4, ex2.m1_policy_transition)
        stageA.add_policy_transition(ex2.policy_3, ex2.policy_4, ex2.m1_policy_transition)

        new_priority = [
            (ex2.m1_policy_transition, ex2.policy_3),
            (ex2.m1_policy_transition, ex2.policy_2),
        ]
        stageA.set_policy_transition_priority(ex2.policy_1, new_priority)

        self.assertEqual(stageA.see_policy_transitions(ex2.policy_1), new_priority)

    def test_remove_policies_and_policy_transitions(self):
        """
        Tests if policies can be removed in all
        the ways offered.

        For diamond graph:
        A -> B -> D
        A -> C -> D
        Testing:
        - Removing A
        - Removing D
        - Removing B
        - Removing all edges and creating floating policies.
        """

        dummy_task = ex2.DummyTask(task_parameters=ex2.DummyParameters())
        stageA = Stage(name="Stage A", task=dummy_task)

        stageA.add_policy(ex2.policy_1)
        stageA.set_start_policies(ex2.policy_1)

        stageA.add_policy_transition(ex2.policy_1, ex2.policy_2, ex2.m1_policy_transition)
        stageA.add_policy_transition(ex2.policy_1, ex2.policy_3, ex2.m1_policy_transition)

        stageA.add_policy_transition(ex2.policy_2, ex2.policy_4, ex2.m1_policy_transition)
        stageA.add_policy_transition(ex2.policy_3, ex2.policy_4, ex2.m1_policy_transition)

        stageA1 = stageA.model_copy(deep=True)
        stageA2 = stageA.model_copy(deep=True)
        stageA3 = stageA.model_copy(deep=True)
        stageA4 = stageA.model_copy(deep=True)

        stageA1.remove_policy(ex2.policy_1)
        self.assertEqual(stageA1.see_policies(), [ex2.policy_2, ex2.policy_3, ex2.policy_4])

        stageA2.remove_policy(ex2.policy_4)
        self.assertEqual(stageA2.see_policy_transitions(ex2.policy_2), [])
        self.assertEqual(stageA2.see_policy_transitions(ex2.policy_3), [])

        stageA3.remove_policy(ex2.policy_2)
        self.assertEqual(
            stageA3.see_policy_transitions(ex2.policy_1),
            [(ex2.m1_policy_transition, ex2.policy_3)],
        )

        stageA4.remove_policy_transition(ex2.policy_1, ex2.policy_2, ex2.m1_policy_transition)
        stageA4.remove_policy_transition(ex2.policy_1, ex2.policy_3, ex2.m1_policy_transition)
        stageA4.remove_policy_transition(ex2.policy_2, ex2.policy_4, ex2.m1_policy_transition)
        stageA4.remove_policy_transition(ex2.policy_3, ex2.policy_4, ex2.m1_policy_transition)
        self.assertEqual(stageA4.see_policy_transitions(ex2.policy_1), [])
        self.assertEqual(stageA4.see_policy_transitions(ex2.policy_2), [])
        self.assertEqual(stageA4.see_policy_transitions(ex2.policy_3), [])
        self.assertEqual(stageA4.see_policy_transitions(ex2.policy_4), [])

    def test_remove_stages_and_stage_transitions(self):
        """
        Tests if stages can be removed in all
        the ways offered.

        For diamond graph:
        A -> B -> D
        A -> C -> D
        Testing:
        - Removing A
        - Removing D
        - Removing B
        - Removing all edges and creating floating stages.
        """

        dummy_task = ex2.DummyTask(task_parameters=ex2.DummyParameters())
        stageA = Stage(name="Stage A", task=dummy_task)
        stageB = Stage(name="Stage B", task=dummy_task)
        stageC = Stage(name="Stage C", task=dummy_task)
        stageD = Stage(name="Stage D", task=dummy_task)

        ex_curr = ex2.MyCurriculum()
        ex_curr.add_stage(stageA)
        ex_curr.add_stage_transition(stageA, stageB, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageA, stageC, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageB, stageD, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageC, stageD, ex2.m1_stage_transition)

        ex_curr1 = ex_curr.model_copy(deep=True)
        ex_curr2 = ex_curr.model_copy(deep=True)
        ex_curr3 = ex_curr.model_copy(deep=True)
        ex_curr4 = ex_curr.model_copy(deep=True)

        ex_curr1.remove_stage(stageA)
        self.assertEqual(ex_curr1.see_stages(), [stageB, stageC, stageD])

        ex_curr2.remove_stage(stageD)
        self.assertEqual(ex_curr2.see_stage_transitions(stageB), [])
        self.assertEqual(ex_curr2.see_stage_transitions(stageC), [])

        ex_curr3.remove_stage(stageB)
        self.assertEqual(
            ex_curr3.see_stage_transitions(stageA),
            [(ex2.m1_stage_transition, stageC)],
        )

        ex_curr4.remove_stage_transition(stageA, stageB, ex2.m1_stage_transition)
        ex_curr4.remove_stage_transition(stageA, stageC, ex2.m1_stage_transition)
        ex_curr4.remove_stage_transition(stageB, stageD, ex2.m1_stage_transition)
        ex_curr4.remove_stage_transition(stageC, stageD, ex2.m1_stage_transition)
        self.assertEqual(ex_curr4.see_stage_transitions(stageA), [])
        self.assertEqual(ex_curr4.see_stage_transitions(stageB), [])
        self.assertEqual(ex_curr4.see_stage_transitions(stageC), [])
        self.assertEqual(ex_curr4.see_stage_transitions(stageD), [])

    def test_reorder_stage_transitions(self):
        """
        Constructing a diamond graph and reordering
        priority of two branches.

        For diamond graph:
        A -> B -> D
        A -> C -> D
        and swapping priority of B and C.

        Testing:
        A's transitions are reordered
        from [B, C] to [C, B].
        """

        dummy_task = ex2.DummyTask(task_parameters=ex2.DummyParameters())
        stageA = Stage(name="Stage A", task=dummy_task)
        stageB = Stage(name="Stage B", task=dummy_task)
        stageC = Stage(name="Stage C", task=dummy_task)
        stageD = Stage(name="Stage D", task=dummy_task)

        ex_curr = ex2.MyCurriculum()
        ex_curr.add_stage(stageA)
        ex_curr.add_stage_transition(stageA, stageB, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageA, stageC, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageB, stageD, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageC, stageD, ex2.m1_stage_transition)

        new_priority = [
            (ex2.m1_stage_transition, stageC),
            (ex2.m1_stage_transition, stageB),
        ]
        ex_curr.set_stage_transition_priority(stageA, new_priority)

        self.assertEqual(ex_curr.see_stage_transitions(stageA), new_priority)

    def test_create_curriculum(self):
        _ = create_curriculum("test_curriculum", "1.2.3", (ex.TaskA, ex.TaskB))
        _ = create_curriculum("test_curriculum", "1.2.3", (ex.TaskA, ex.TaskB, ex.TaskB))
        _ = create_curriculum(
            "test_curriculum",
            "1.2.3",
            (ex.TaskA, ex.TaskB),
            pkg_location="example_project",
        )

    def test_create_curriculum_equivalence(self):
        class TestCurriculum(Curriculum):
            name: str = "TestCurriculum"
            version: str = "1.2.3"
            graph: StageGraph[make_task_discriminator((ex.TaskA, ex.TaskB))] = Field(default_factory=StageGraph)
            pkg_location: str = "test"

        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        taskB = ex.TaskB(task_parameters=ex.TaskBParameters())
        expected_curriculum = TestCurriculum()
        expected_curriculum.add_stage(Stage(name="Stage 0", task=taskA))
        expected_curriculum.add_stage(Stage(name="Stage 1", task=taskB))

        created_curriculum = create_curriculum(
            "TestCurriculum",
            "1.2.3",
            (ex.TaskA, ex.TaskB),
            pkg_location="test",
        )()
        created_curriculum.add_stage(Stage(name="Stage 0", task=taskA))
        created_curriculum.add_stage(Stage(name="Stage 1", task=taskB))

        self.assertEqual(expected_curriculum.model_dump(), created_curriculum.model_dump())
        self.assertEqual(
            expected_curriculum.model_dump_json(),
            created_curriculum.model_dump_json(),
        )
        self.assertEqual(
            expected_curriculum.model_validate_json(expected_curriculum.model_dump_json()),
            expected_curriculum.model_validate_json(expected_curriculum.model_dump_json()),
        )

    def test_create_curriculum_with_invalid_tagged_union(self):
        class NotATask(BaseModel):
            not_name: str = "Not a Task"

        with self.assertRaises(PydanticUserError) as _:
            _ = create_curriculum("test_curriculum", "1.2.3", (ex.TaskA, ex.TaskB, NotATask))


if __name__ == "__main__":
    unittest.main()
