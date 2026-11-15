"""
Tests for curriculum-level Globals and StageEntryRule.
"""

import contextlib
import io
import json
import unittest
from typing import Literal

from pydantic import Field

from aind_behavior_curriculum import (
    Curriculum,
    Globals,
    Metrics,
    Policy,
    Stage,
    StageEntryRule,
    StageGraph,
    Task,
    TaskParameters,
    Trainer,
    TrainerServer,
    TrainerState,
    make_task_discriminator,
)


# --- TASKS ---
class ReportParameters(TaskParameters):
    is_left_circle: bool = Field(default=False)
    response_delay: float = Field(default=0.0)


class ReportTask(Task):
    name: Literal["ReportTask"] = "ReportTask"
    task_parameters: ReportParameters = Field(default_factory=ReportParameters)


class OtherParameters(TaskParameters):
    left_target: str = Field(default="square")


class OtherTask(Task):
    name: Literal["OtherTask"] = "OtherTask"
    task_parameters: OtherParameters = Field(default_factory=OtherParameters)


# --- GLOBALS / METRICS ---
class ContingencyGlobals(Globals):
    is_left_circle: bool


class ReportMetrics(Metrics):
    performance: float = Field(default=0.0)


# --- RULES ---
def apply_contingency(g: ContingencyGlobals, task: ReportTask) -> ReportTask:
    task.task_parameters.is_left_circle = g.is_left_circle
    return task


def apply_contingency_other(g: ContingencyGlobals, task: OtherTask) -> OtherTask:
    task.task_parameters.left_target = "circle" if g.is_left_circle else "square"
    return task


def increase_delay(metrics: ReportMetrics, task: ReportTask) -> ReportTask:
    task.task_parameters.response_delay += 1.0
    # Policies must not be undone by the entry rule within a stage
    task.task_parameters.is_left_circle = not task.task_parameters.is_left_circle
    return task


def perf_high(metrics: ReportMetrics) -> bool:
    return metrics.performance > 0.8


def apply_contingency_untyped(g, task):
    task.task_parameters.is_left_circle = g.is_left_circle
    return task


def returns_wrong_task(g: ContingencyGlobals, task: ReportTask) -> ReportTask:
    return OtherTask()  # type: ignore[return-value]


Tasks = make_task_discriminator([ReportTask, OtherTask])


class MyCurriculum(Curriculum):
    name: Literal["GlobalsCurriculum"] = "GlobalsCurriculum"
    version: Literal["0.1.0"] = "0.1.0"
    graph: StageGraph[Metrics, Tasks] = Field(default_factory=StageGraph[Metrics, Tasks])  # type: ignore


def make_curriculum() -> tuple[MyCurriculum, Stage, Stage]:
    stage_a = Stage(name="StageA", task=ReportTask(), on_entry=StageEntryRule(apply_contingency))
    stage_b = Stage(name="StageB", task=OtherTask(), on_entry=StageEntryRule(apply_contingency_other))
    curriculum = MyCurriculum()
    curriculum.add_stage_transition(stage_a, stage_b, perf_high)
    return curriculum, stage_a, stage_b


class InMemoryTrainerServer(TrainerServer):
    def __init__(self):
        super().__init__()
        self.curricula: dict[int, Curriculum] = {}
        self.states: dict[int, TrainerState] = {}
        self.metrics: dict[int, Metrics] = {}

    def load_data(self, subject_id):
        return self.curricula[subject_id], self.states[subject_id], self.metrics.get(subject_id, ReportMetrics())

    def write_data(self, subject_id, curriculum, trainer_state):
        self.curricula[subject_id] = curriculum
        self.states[subject_id] = trainer_state


class GlobalsTests(unittest.TestCase):
    def test_enrollment_applies_entry_rule(self):
        curriculum, stage_a, _ = make_curriculum()
        trainer = Trainer(curriculum)
        state = trainer.create_enrollment(globals=ContingencyGlobals(is_left_circle=True))

        self.assertEqual(state.globals, ContingencyGlobals(is_left_circle=True))
        self.assertTrue(state.stage.task.task_parameters.is_left_circle)
        # The curriculum's own stage must remain untouched
        self.assertFalse(stage_a.task.task_parameters.is_left_circle)
        self.assertFalse(curriculum.see_stages()[0].task.task_parameters.is_left_circle)

    def test_enrollment_without_globals_raises_when_rule_defined(self):
        curriculum, _, _ = make_curriculum()
        with self.assertRaises(ValueError):
            Trainer(curriculum).create_enrollment()

    def test_no_rule_no_globals_is_backwards_compatible(self):
        stage_a = Stage(name="StageA", task=ReportTask())
        curriculum = MyCurriculum()
        curriculum.add_stage(stage_a)
        state = Trainer(curriculum).create_enrollment()
        self.assertIsNone(state.globals)
        self.assertEqual(state.stage.task, stage_a.task)

    def test_entry_rule_not_reapplied_within_stage(self):
        curriculum, stage_a, _ = make_curriculum()
        stage_a.add_policy(Policy(increase_delay))
        stage_a.set_start_policies(Policy(increase_delay))
        trainer = Trainer(curriculum)
        state = trainer.create_enrollment(globals=ContingencyGlobals(is_left_circle=True))
        state = trainer.evaluate(state, ReportMetrics(performance=0.1))

        self.assertEqual(state.stage.name, "StageA")
        self.assertEqual(state.stage.task.task_parameters.response_delay, 1.0)
        # Policy flipped the value; the entry rule must not have run again
        self.assertFalse(state.stage.task.task_parameters.is_left_circle)
        self.assertEqual(state.globals, ContingencyGlobals(is_left_circle=True))

    def test_stage_transition_applies_entry_rule_and_keeps_globals(self):
        curriculum, _, _ = make_curriculum()
        trainer = Trainer(curriculum)
        state = trainer.create_enrollment(globals=ContingencyGlobals(is_left_circle=True))
        state = trainer.evaluate(state, ReportMetrics(performance=0.9))

        self.assertEqual(state.stage.name, "StageB")
        self.assertEqual(state.stage.task.task_parameters.left_target, "circle")
        self.assertEqual(state.globals, ContingencyGlobals(is_left_circle=True))
        self.assertEqual(curriculum.see_stages()[1].task.task_parameters.left_target, "square")

    def test_stage_without_rule_ignores_globals(self):
        stage_a = Stage(name="StageA", task=ReportTask(), on_entry=StageEntryRule(apply_contingency))
        stage_b = Stage(name="StageB", task=OtherTask())
        curriculum = MyCurriculum()
        curriculum.add_stage_transition(stage_a, stage_b, perf_high)
        trainer = Trainer(curriculum)
        state = trainer.create_enrollment(globals=ContingencyGlobals(is_left_circle=True))
        state = trainer.evaluate(state, ReportMetrics(performance=0.9))
        self.assertEqual(state.stage.name, "StageB")
        self.assertEqual(state.stage.task, stage_b.task)
        self.assertEqual(state.globals, ContingencyGlobals(is_left_circle=True))

    def test_manual_globals_edit_used_on_next_entry(self):
        curriculum, _, _ = make_curriculum()
        trainer = Trainer(curriculum)
        state = trainer.create_enrollment(globals=ContingencyGlobals(is_left_circle=True))
        state.globals = ContingencyGlobals(is_left_circle=False)
        state = trainer.evaluate(state, ReportMetrics(performance=0.9))
        self.assertEqual(state.stage.task.task_parameters.left_target, "square")

    def test_trainer_state_serialization_round_trip(self):
        curriculum, _, _ = make_curriculum()
        trainer = Trainer(curriculum)
        state = trainer.create_enrollment(globals=ContingencyGlobals(is_left_circle=True))
        json_str = state.model_dump_json()

        # The concrete Globals type is not stored: data survives as extra fields
        loaded = trainer.trainer_state_model.model_validate_json(json_str)
        self.assertIs(type(loaded.globals), Globals)
        self.assertEqual(loaded.globals.model_dump(), {"is_left_circle": True})
        self.assertEqual(loaded, state)  # globals compared by value
        self.assertEqual(TrainerState.model_validate_json(json_str).globals.model_dump(), {"is_left_circle": True})

        # ...and is validated into the rule's type on the next stage entry
        loaded = trainer.evaluate(loaded, ReportMetrics(performance=0.9))
        self.assertEqual(loaded.stage.task.task_parameters.left_target, "circle")

    def test_curriculum_serialization_round_trip(self):
        curriculum, _, _ = make_curriculum()
        curriculum.validate_curriculum()
        deserialized = MyCurriculum.model_validate_json(curriculum.model_dump_json())
        self.assertEqual(deserialized.see_stages()[0].on_entry, StageEntryRule(apply_contingency))
        self.assertEqual(deserialized.see_stages()[1].on_entry, StageEntryRule(apply_contingency_other))

    def test_entry_rule_signature_validation(self):
        def wrong(metrics: ReportMetrics, task: ReportTask) -> ReportTask:
            return task

        with self.assertRaises(TypeError):
            StageEntryRule(wrong)

    def test_globals_type_from_annotation(self):
        self.assertIs(StageEntryRule(apply_contingency).globals_type, ContingencyGlobals)
        self.assertIs(StageEntryRule(apply_contingency_untyped).globals_type, Globals)

    def test_untyped_globals_coerced_into_rule_type(self):
        rule = StageEntryRule(apply_contingency)
        coerced = rule.coerce_globals(Globals(is_left_circle=True))
        self.assertIsInstance(coerced, ContingencyGlobals)
        self.assertTrue(coerced.is_left_circle)
        same = ContingencyGlobals(is_left_circle=False)
        self.assertIs(rule.coerce_globals(same), same)

    def test_untyped_rule_receives_globals_as_is(self):
        stage_a = Stage(name="StageA", task=ReportTask(), on_entry=StageEntryRule(apply_contingency_untyped))
        curriculum = MyCurriculum()
        curriculum.add_stage(stage_a)
        state = Trainer(curriculum).create_enrollment(globals=Globals(is_left_circle=True))
        self.assertTrue(state.stage.task.task_parameters.is_left_circle)

    def test_enrollment_checks_every_stage(self):
        # Only the second stage has a rule: enrollment must still fail without globals
        stage_a = Stage(name="StageA", task=ReportTask())
        stage_b = Stage(name="StageB", task=OtherTask(), on_entry=StageEntryRule(apply_contingency_other))
        curriculum = MyCurriculum()
        curriculum.add_stage_transition(stage_a, stage_b, perf_high)
        with self.assertRaises(ValueError):
            Trainer(curriculum).create_enrollment()
        # Globals missing a field required by a later stage's rule
        with self.assertRaisesRegex(ValueError, "StageB"):
            Trainer(curriculum).create_enrollment(globals=Globals())
        with self.assertRaises(ValueError):
            InMemoryTrainerServer().register_subject(0, curriculum, stage_a, globals=Globals())

    def test_validate_curriculum_with_sample_globals(self):
        curriculum, _, _ = make_curriculum()
        curriculum.validate_curriculum(sample_globals=ContingencyGlobals(is_left_circle=True))

        broken = MyCurriculum()
        broken.add_stage(Stage(name="StageA", task=ReportTask(), on_entry=StageEntryRule(returns_wrong_task)))
        broken.validate_curriculum()  # No sample: rules are not run
        with self.assertRaisesRegex(ValueError, "returned OtherTask"):
            broken.validate_curriculum(sample_globals=ContingencyGlobals(is_left_circle=True))

    def test_validate_globals_does_not_mutate_curriculum(self):
        curriculum, stage_a, _ = make_curriculum()
        curriculum.validate_globals(ContingencyGlobals(is_left_circle=True))
        self.assertFalse(curriculum.see_stages()[0].task.task_parameters.is_left_circle)

    def test_trainer_server_propagates_globals(self):
        curriculum, stage_a, stage_b = make_curriculum()
        server = InMemoryTrainerServer()
        server.register_subject(0, curriculum, stage_a, globals=ContingencyGlobals(is_left_circle=True))
        self.assertTrue(server.states[0].stage.task.task_parameters.is_left_circle)

        server.metrics[0] = ReportMetrics(performance=0.9)
        server.evaluate_subjects()
        self.assertEqual(server.states[0].stage.name, "StageB")
        self.assertEqual(server.states[0].stage.task.task_parameters.left_target, "circle")

        server.override_subject_status(0, stage_a, [])
        self.assertTrue(server.states[0].stage.task.task_parameters.is_left_circle)

        server.eject_subject(0)
        self.assertIsNone(server.states[0].stage)
        self.assertEqual(server.states[0].globals, ContingencyGlobals(is_left_circle=True))

    def test_unset_fields_are_not_serialized(self):
        """Curricula and states that do not use globals must serialize exactly as
        before, so that older versions of the library can still read them."""
        stage_a = Stage(name="StageA", task=ReportTask())
        curriculum = MyCurriculum()
        curriculum.add_stage(stage_a)
        state = Trainer(curriculum).create_enrollment()

        self.assertNotIn("on_entry", stage_a.model_dump())
        self.assertNotIn("on_entry", json.loads(stage_a.model_dump_json()))
        self.assertNotIn("globals", state.model_dump())
        self.assertNotIn("globals", json.loads(state.model_dump_json()))
        self.assertNotIn("on_entry", json.loads(state.model_dump_json())["stage"])

        # ...but are serialized when set
        curriculum, _, _ = make_curriculum()
        state = Trainer(curriculum).create_enrollment(globals=ContingencyGlobals(is_left_circle=True))
        dumped = json.loads(state.model_dump_json())
        self.assertEqual(dumped["globals"], {"is_left_circle": True})
        self.assertEqual(dumped["stage"]["on_entry"], StageEntryRule(apply_contingency).name)

    def test_example_runs(self):
        from example_project_globals.__main__ import main

        with contextlib.redirect_stdout(io.StringIO()) as out:
            main()
        self.assertIn("mouse_b: stage=Withhold  is_left_circle=False delay=0.7", out.getvalue())


if __name__ == "__main__":
    unittest.main()
