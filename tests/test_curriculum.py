"""
Curriculum Test Suite
"""

import unittest

import example_project as ex
import example_project_2 as ex2

from aind_behavior_curriculum import INIT_STAGE, Curriculum, Stage
from aind_behavior_curriculum.curriculum_utils import create_empty_stage


class CurriculumTests(unittest.TestCase):
    """Unit tests for Stage/Curriculum De/Serialization"""

    def test_round_trip_empty_stage(self):
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = Stage(name="StageA", task=taskA)

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Child
        recovered = Stage.model_validate_json(instance_json)
        self.assertTrue(stageA == recovered)

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Parent
        instance_parent = Stage.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = Stage.model_validate_json(parent_json)
        self.assertTrue(stageA == instance_prime)

    def test_round_trip_stage(self):
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = Stage(name="StageA", task=taskA)

        stageA.add_policy_transition(INIT_STAGE, ex.stageA_policyB, ex.t1_10)
        stageA.add_policy_transition(INIT_STAGE, ex.stageA_policyA, ex.t1_5)
        stageA.add_policy_transition(
            ex.stageA_policyA, ex.stageA_policyB, ex.t1_10
        )

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Child
        recovered = Stage.model_validate_json(instance_json)
        self.assertTrue(stageA == recovered)

        # Serialize from Child
        instance_json = stageA.model_dump_json()
        # Deserialize from Parent
        instance_parent = Stage.model_validate_json(instance_json)
        # Serialize from Parent
        parent_json = instance_parent.model_dump_json()
        # Deserialize from Child
        instance_prime = Stage.model_validate_json(parent_json)
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

        stageA.add_policy_transition(
            ex2.policy_1, ex2.policy_2, ex2.m1_policy_transition
        )
        stageA.add_policy_transition(
            ex2.policy_1, ex2.policy_3, ex2.m1_policy_transition
        )

        stageA.add_policy_transition(
            ex2.policy_2, ex2.policy_4, ex2.m1_policy_transition
        )
        stageA.add_policy_transition(
            ex2.policy_3, ex2.policy_4, ex2.m1_policy_transition
        )

        self.assertTrue(
            stageA.see_policies()
            == [ex2.policy_1, ex2.policy_2, ex2.policy_3, ex2.policy_4]
        )
        self.assertTrue(
            stageA.see_policy_transitions(ex2.policy_1)
            == [
                (ex2.m1_policy_transition, ex2.policy_2),
                (ex2.m1_policy_transition, ex2.policy_3),
            ]
        )
        self.assertTrue(
            stageA.see_policy_transitions(ex2.policy_2)
            == [(ex2.m1_policy_transition, ex2.policy_4)]
        )
        self.assertTrue(
            stageA.see_policy_transitions(ex2.policy_3)
            == [(ex2.m1_policy_transition, ex2.policy_4)]
        )
        self.assertTrue(stageA.see_policy_transitions(ex2.policy_4) == [])

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
        stageA = create_empty_stage(Stage(name="Stage A", task=dummy_task))
        stageB = create_empty_stage(Stage(name="Stage B", task=dummy_task))
        stageC = create_empty_stage(Stage(name="Stage C", task=dummy_task))
        stageD = create_empty_stage(Stage(name="Stage D", task=dummy_task))

        ex_curr = ex2.Curriculum()
        ex_curr.add_stage(stageA)
        ex_curr.add_stage_transition(stageA, stageB, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageA, stageC, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageB, stageD, ex2.m1_stage_transition)
        ex_curr.add_stage_transition(stageC, stageD, ex2.m1_stage_transition)

        self.assertTrue(
            ex_curr.see_stages() == [stageA, stageB, stageC, stageD]
        )
        self.assertTrue(
            ex_curr.see_stage_transitions(stageA)
            == [
                (ex2.m1_stage_transition, stageB),
                (ex2.m1_stage_transition, stageC),
            ]
        )
        self.assertTrue(
            ex_curr.see_stage_transitions(stageB)
            == [(ex2.m1_stage_transition, stageD)]
        )
        self.assertTrue(
            ex_curr.see_stage_transitions(stageC)
            == [(ex2.m1_stage_transition, stageD)]
        )
        self.assertTrue(ex_curr.see_stage_transitions(stageD) == [])

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

        stageA.add_policy_transition(
            ex2.policy_1, ex2.policy_2, ex2.m1_policy_transition
        )
        stageA.add_policy_transition(
            ex2.policy_1, ex2.policy_3, ex2.m1_policy_transition
        )

        stageA.add_policy_transition(
            ex2.policy_2, ex2.policy_4, ex2.m1_policy_transition
        )
        stageA.add_policy_transition(
            ex2.policy_3, ex2.policy_4, ex2.m1_policy_transition
        )

        new_priority = [
            (ex2.m1_policy_transition, ex2.policy_3),
            (ex2.m1_policy_transition, ex2.policy_2),
        ]
        stageA.set_policy_transition_priority(ex2.policy_1, new_priority)

        self.assertTrue(
            stageA.see_policy_transitions(ex2.policy_1) == new_priority
        )

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

        stageA.add_policy_transition(
            ex2.policy_1, ex2.policy_2, ex2.m1_policy_transition
        )
        stageA.add_policy_transition(
            ex2.policy_1, ex2.policy_3, ex2.m1_policy_transition
        )

        stageA.add_policy_transition(
            ex2.policy_2, ex2.policy_4, ex2.m1_policy_transition
        )
        stageA.add_policy_transition(
            ex2.policy_3, ex2.policy_4, ex2.m1_policy_transition
        )

        stageA1 = stageA.model_copy(deep=True)
        stageA2 = stageA.model_copy(deep=True)
        stageA3 = stageA.model_copy(deep=True)
        stageA4 = stageA.model_copy(deep=True)

        stageA1.remove_policy(ex2.policy_1)
        self.assertTrue(
            stageA1.see_policies()
            == [ex2.policy_2, ex2.policy_3, ex2.policy_4]
        )

        stageA2.remove_policy(ex2.policy_4)
        self.assertTrue(stageA2.see_policy_transitions(ex2.policy_2) == [])
        self.assertTrue(stageA2.see_policy_transitions(ex2.policy_3) == [])

        stageA3.remove_policy(ex2.policy_2)
        self.assertTrue(
            stageA3.see_policy_transitions(ex2.policy_1)
            == [(ex2.m1_policy_transition, ex2.policy_3)]
        )

        stageA4.remove_policy_transition(
            ex2.policy_1, ex2.policy_2, ex2.m1_policy_transition
        )
        stageA4.remove_policy_transition(
            ex2.policy_1, ex2.policy_3, ex2.m1_policy_transition
        )
        stageA4.remove_policy_transition(
            ex2.policy_2, ex2.policy_4, ex2.m1_policy_transition
        )
        stageA4.remove_policy_transition(
            ex2.policy_3, ex2.policy_4, ex2.m1_policy_transition
        )
        self.assertTrue(stageA4.see_policy_transitions(ex2.policy_1) == [])
        self.assertTrue(stageA4.see_policy_transitions(ex2.policy_2) == [])
        self.assertTrue(stageA4.see_policy_transitions(ex2.policy_3) == [])
        self.assertTrue(stageA4.see_policy_transitions(ex2.policy_4) == [])

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
        stageA = create_empty_stage(Stage(name="Stage A", task=dummy_task))
        stageB = create_empty_stage(Stage(name="Stage B", task=dummy_task))
        stageC = create_empty_stage(Stage(name="Stage C", task=dummy_task))
        stageD = create_empty_stage(Stage(name="Stage D", task=dummy_task))

        ex_curr = ex2.Curriculum()
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
        self.assertTrue(ex_curr1.see_stages() == [stageB, stageC, stageD])

        ex_curr2.remove_stage(stageD)
        self.assertTrue(ex_curr2.see_stage_transitions(stageB) == [])
        self.assertTrue(ex_curr2.see_stage_transitions(stageC) == [])

        ex_curr3.remove_stage(stageB)
        self.assertTrue(
            ex_curr3.see_stage_transitions(stageA)
            == [(ex2.m1_stage_transition, stageC)]
        )

        ex_curr4.remove_stage_transition(
            stageA, stageB, ex2.m1_stage_transition
        )
        ex_curr4.remove_stage_transition(
            stageA, stageC, ex2.m1_stage_transition
        )
        ex_curr4.remove_stage_transition(
            stageB, stageD, ex2.m1_stage_transition
        )
        ex_curr4.remove_stage_transition(
            stageC, stageD, ex2.m1_stage_transition
        )
        self.assertTrue(ex_curr4.see_stage_transitions(stageA) == [])
        self.assertTrue(ex_curr4.see_stage_transitions(stageB) == [])
        self.assertTrue(ex_curr4.see_stage_transitions(stageC) == [])
        self.assertTrue(ex_curr4.see_stage_transitions(stageD) == [])

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
        stageA = create_empty_stage(Stage(name="Stage A", task=dummy_task))
        stageB = create_empty_stage(Stage(name="Stage B", task=dummy_task))
        stageC = create_empty_stage(Stage(name="Stage C", task=dummy_task))
        stageD = create_empty_stage(Stage(name="Stage D", task=dummy_task))

        ex_curr = ex2.Curriculum()
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

        self.assertTrue(ex_curr.see_stage_transitions(stageA) == new_priority)


if __name__ == "__main__":
    unittest.main()
