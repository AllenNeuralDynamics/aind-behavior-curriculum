"""
Typing and deserialization robustness tests
"""

import unittest
from typing import Literal

import example_project as ex
from pydantic import Field

from aind_behavior_curriculum import (
    Curriculum,
    Metrics,
    Policy,
    Stage,
    StageGraph,
    StageTransition,
    Task,
    Trainer,
    create_curriculum,
    make_task_discriminator,
)
from aind_behavior_curriculum.curriculum import is_non_deserializable_callable

from . import future_annotations_rules as far


class SignatureValidationTests(unittest.TestCase):
    def test_postponed_annotations_are_resolved(self):
        Policy(far.policy_rule)
        StageTransition(far.optional_transition)

    def test_any_annotation_is_accepted(self):
        StageTransition(far.any_transition)

    def test_incompatible_postponed_annotation_is_rejected(self):
        with self.assertRaises(TypeError):
            StageTransition(far.wrong_transition)


class RuleDeserializationTests(unittest.TestCase):
    def test_nested_qualname_round_trip(self):
        rule = StageTransition(far.RuleHolder.transition)
        reference = StageTransition.serialize_rule(rule)
        self.assertEqual(reference, "tests.future_annotations_rules.RuleHolder.transition")
        recovered = StageTransition._deserialize_rule(reference)
        self.assertIs(recovered.callable, far.RuleHolder.transition)
        self.assertEqual(rule, recovered)

    def test_unresolvable_references(self):
        for reference in [
            "not_a_module",
            "not_a_package.module.function",
            "tests.future_annotations_rules.does_not_exist",
            "tests.future_annotations_rules.RuleHolder.does_not_exist",
        ]:
            with self.subTest(reference=reference):
                rule = StageTransition._deserialize_rule(reference)
                self.assertTrue(is_non_deserializable_callable(rule.callable))
                # The original reference is preserved on re-serialization
                self.assertEqual(StageTransition.serialize_rule(rule), reference)


class DeterminismTests(unittest.TestCase):
    def test_task_discriminator_preserves_order(self):
        for tasks in [(ex.TaskA, ex.TaskB), (ex.TaskB, ex.TaskA), (ex.TaskA, ex.TaskB, ex.TaskA)]:
            with self.subTest(tasks=tasks):
                discriminator = make_task_discriminator(tasks)
                curriculum_type = create_curriculum("Curr", "0.0.1", tasks)
                expected = list(dict.fromkeys(tasks))
                self.assertEqual(curriculum_type(name="Curr")._known_tasks, expected)
                self.assertIsNotNone(discriminator)

    def test_unique_policies_preserve_order(self):
        policies = [ex.stageA_policyB, ex.stageA_policyA, ex.stageA_policyB, ex.INIT_STAGE]
        self.assertEqual(
            Trainer._get_unique_policies(policies),
            [ex.stageA_policyB, ex.stageA_policyA, ex.INIT_STAGE],
        )


class IterableInputTests(unittest.TestCase):
    def test_create_curriculum_accepts_generator(self):
        curriculum_type = create_curriculum("Curr", "0.0.1", (t for t in (ex.TaskA, ex.TaskB)))
        self.assertEqual(curriculum_type(name="Curr")._known_tasks, [ex.TaskA, ex.TaskB])

    def test_set_start_policies_accepts_generator(self):
        stage = Stage(name="StageA", task=ex.TaskA(task_parameters=ex.TaskAParameters()))
        stage.set_start_policies(p for p in (ex.stageA_policyA, ex.stageA_policyB))
        self.assertEqual(stage.start_policies, [ex.stageA_policyA, ex.stageA_policyB])


class KnownTasksTests(unittest.TestCase):
    def test_plain_task_graph_annotation(self):
        class SingleTaskCurriculum(Curriculum):
            version: Literal["0.0.1"] = "0.0.1"
            graph: StageGraph[Metrics, ex.TaskA] = Field(default_factory=StageGraph[Metrics, ex.TaskA])  # type: ignore[valid-type]

        self.assertEqual(SingleTaskCurriculum()._known_tasks, [ex.TaskA])

    def test_union_task_graph_annotation(self):
        class UnionCurriculum(Curriculum):
            version: Literal["0.0.1"] = "0.0.1"
            graph: StageGraph[Metrics, ex.TaskA | ex.TaskB] = Field(
                default_factory=StageGraph[Metrics, ex.TaskA | ex.TaskB]  # type: ignore[valid-type]
            )

        self.assertEqual(UnionCurriculum()._known_tasks, [ex.TaskA, ex.TaskB])

    def test_unparameterized_curriculum(self):
        self.assertEqual(Curriculum(version="0.0.1")._known_tasks, [Task])


if __name__ == "__main__":
    unittest.main()
