"""
Example of Curriculum creation
"""

import json
from typing import Literal

from pydantic import Field

from aind_behavior_curriculum import (
    Curriculum,
    Metrics,
    Policy,
    PolicyTransition,
    Stage,
    StageGraph,
    StageTransition,
    Task,
    TaskParameters,
    make_task_discriminator,
)
from aind_behavior_curriculum.curriculum_utils import (
    export_diagram,
    export_json,
)


# --- TASKS ---
class DummyParameters(TaskParameters):
    field_1: int = Field(default=0, validate_default=True)
    field_2: int = Field(default=0, validate_default=True)


class DummyTask(Task):
    name: Literal["DummyTask"] = "DummyTask"
    task_parameters: DummyParameters = Field(..., description="Fill w/ Parameter Defaults", validate_default=True)


# --- METRICS ---
class ExampleMetrics2(Metrics):
    """
    Totally made up values we will edit ourselves to simulate mouse training.
    Each theta value is reserved for a test case.
    """

    m1: int = Field(default=0)
    m2: int = Field(default=0)


# --- POLICIES ---
# Policies 1-3 do the same thing
# Policies 4-6 do the same thing
def policy_1_rule(metrics: ExampleMetrics2, task_params: DummyParameters) -> DummyParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_1 += 5
    return task_params


policy_1 = Policy(policy_1_rule)


def policy_2_rule(metrics: ExampleMetrics2, task_params: DummyParameters) -> DummyParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_1 += 5
    return task_params


policy_2 = Policy(policy_2_rule)


def policy_3_rule(metrics: ExampleMetrics2, task_params: DummyParameters) -> DummyParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_1 += 5
    return task_params


policy_3 = Policy(policy_3_rule)


def policy_4_rule(metrics: ExampleMetrics2, task_params: DummyParameters) -> DummyParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_2 += 5
    return task_params


policy_4 = Policy(policy_4_rule)


def policy_5_rule(metrics: ExampleMetrics2, task_params: DummyParameters) -> DummyParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_2 += 5
    return task_params


policy_5 = Policy(policy_5_rule)


def policy_6_rule(metrics: ExampleMetrics2, task_params: DummyParameters) -> DummyParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_2 += 5
    return task_params


policy_6 = Policy(policy_6_rule)


# --- POLICY/STAGE TRANSITIONS ---
def m1_rule(metrics: ExampleMetrics2) -> bool:
    return metrics.m1 > 0


m1_policy_transition = PolicyTransition(m1_rule)
m1_stage_transition = StageTransition(m1_rule)


def m2_rule(metrics: ExampleMetrics2) -> bool:
    return metrics.m2 > 0


m2_policy_transition = PolicyTransition(m2_rule)
m2_stage_transition = StageTransition(m2_rule)


# --- CURRICULUM ---
Tasks = make_task_discriminator(tasks=[DummyTask])


class MyCurriculum(Curriculum):
    name: Literal["My Curriculum"] = "My Curriculum"
    graph: StageGraph[Tasks] = Field(default=StageGraph[Tasks]())  # type: ignore


def construct_track_curriculum() -> MyCurriculum:
    dummy_task = DummyTask(task_parameters=DummyParameters())
    test_stage = Stage(name="Track Stage", task=dummy_task)

    test_stage.add_policy_transition(policy_1, policy_2, m1_policy_transition)
    test_stage.add_policy_transition(policy_2, policy_3, m1_policy_transition)
    test_stage.add_policy_transition(policy_4, policy_5, m2_policy_transition)
    test_stage.add_policy_transition(policy_5, policy_6, m2_policy_transition)
    test_stage.set_start_policies([policy_1, policy_4])

    test_curr = MyCurriculum(name="My Curriculum")
    test_curr.add_stage(test_stage)

    return test_curr


def construct_tree_curriculum() -> MyCurriculum:
    dummy_task = DummyTask(task_parameters=DummyParameters())
    test_stage = Stage(name="Tree Stage", task=dummy_task)

    test_stage.add_policy_transition(policy_1, policy_4, m1_policy_transition)
    test_stage.add_policy_transition(policy_2, policy_4, m1_policy_transition)
    test_stage.add_policy_transition(policy_2, policy_5, m1_policy_transition)
    test_stage.add_policy_transition(policy_3, policy_5, m1_policy_transition)
    test_stage.add_policy_transition(policy_4, policy_6, m2_policy_transition)
    test_stage.add_policy_transition(policy_5, policy_6, m2_policy_transition)
    test_stage.set_start_policies([policy_1, policy_2, policy_3])

    test_curr = MyCurriculum(name="My Curriculum")
    test_curr.add_stage(test_stage)

    return test_curr


def construct_policy_triangle_curriculum() -> MyCurriculum:
    dummy_task = DummyTask(task_parameters=DummyParameters())
    test_stage = Stage(name="Triangle Stage", task=dummy_task)

    # Counter-clockwise, higher priority
    test_stage.add_policy_transition(policy_1, policy_2, m1_policy_transition)
    test_stage.add_policy_transition(policy_2, policy_3, m1_policy_transition)
    test_stage.add_policy_transition(policy_3, policy_1, m1_policy_transition)

    # Clockwise
    test_stage.add_policy_transition(policy_1, policy_3, m2_policy_transition)
    test_stage.add_policy_transition(policy_3, policy_2, m2_policy_transition)
    test_stage.add_policy_transition(policy_2, policy_1, m2_policy_transition)

    test_stage.set_start_policies([policy_1])

    test_curr = MyCurriculum(name="My Curriculum")
    test_curr.add_stage(test_stage)

    return test_curr


def construct_stage_triangle_curriculum() -> MyCurriculum:
    dummy_task = DummyTask(task_parameters=DummyParameters())

    test_stage_1 = Stage(name="Stage 1", task=dummy_task)
    test_stage_2 = Stage(name="Stage 2", task=dummy_task)
    test_stage_3 = Stage(name="Stage 3", task=dummy_task)

    test_curr = MyCurriculum(name="My Curriculum")
    # Counter-clockwise, higher priority
    test_curr.add_stage_transition(test_stage_1, test_stage_2, m1_stage_transition)
    test_curr.add_stage_transition(test_stage_2, test_stage_3, m1_stage_transition)
    test_curr.add_stage_transition(test_stage_3, test_stage_1, m1_stage_transition)

    # Clockwise
    test_curr.add_stage_transition(test_stage_1, test_stage_3, m2_stage_transition)
    test_curr.add_stage_transition(test_stage_3, test_stage_2, m2_stage_transition)
    test_curr.add_stage_transition(test_stage_2, test_stage_1, m2_stage_transition)

    return test_curr


if __name__ == "__main__":
    for h in [
        construct_track_curriculum,
        construct_tree_curriculum,
        construct_policy_triangle_curriculum,
        construct_stage_triangle_curriculum,
    ]:
        curriculum = h()
        name = h.__name__.removeprefix("construct_")
        with open(
            f"./examples/example_project_2/assets/{name}_schema.json",
            "w+",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(curriculum.model_json_schema(), indent=4))
        export_json(curriculum, path=f"./examples/example_project_2/assets/{name}.json")
        _ = export_diagram(curriculum, f"./examples/example_project_2/assets/{name}.svg")
