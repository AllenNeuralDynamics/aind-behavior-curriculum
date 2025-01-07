"""
Example of Curriculum creation
"""

import json

from pydantic import Field

from aind_behavior_curriculum import (
    GRADUATED,
    Graduated,
    Metrics,
    Policy,
    PolicyTransition,
    Stage,
    StageTransition,
    TaskParameters,
    create_curriculum,
    create_task,
)
from aind_behavior_curriculum.curriculum_utils import (
    export_diagram,
    export_json,
)


def init_stage_rule(metrics: Metrics, task_params: TaskParameters) -> TaskParameters:
    """
    Trivially pass the default
    """
    return task_params


INIT_STAGE = Policy(init_stage_rule)


# --- TASKS ---
class TaskAParameters(TaskParameters):
    field_a: int = Field(default=0, validate_default=True)


TaskA = create_task(name="Task A", task_parameters=TaskAParameters)


class TaskBParameters(TaskParameters):
    field_b: float = Field(default=0.0)


TaskB = create_task(name="Task B", task_parameters=TaskBParameters)


# --- METRICS ---
class ExampleMetrics(Metrics):
    """
    Totally made up values we will edit ourselves to simulate mouse training.
    Each theta value is reserved for a test case.
    """

    theta_1: int = Field(default=0)
    theta_2: int = Field(default=0)
    theta_3: int = Field(default=0)


# --- POLICIES ---
def stageA_policyA_rule(metrics: ExampleMetrics, task_params: TaskAParameters) -> TaskAParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_a = 8
    return task_params


stageA_policyA = Policy(stageA_policyA_rule)


def stageA_policyB_rule(metrics: ExampleMetrics, task_params: TaskAParameters) -> TaskAParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_a = 16
    return task_params


stageA_policyB = Policy(stageA_policyB_rule)


def stageB_policyA_rule(metrics: ExampleMetrics, task_params: TaskBParameters) -> TaskBParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_b = 8
    return task_params


stageB_policyA = Policy(stageB_policyA_rule)


def stageB_policyB_rule(metrics: ExampleMetrics, task_params: TaskBParameters) -> TaskBParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_b = 16
    return task_params


stageB_policyB = Policy(stageB_policyB_rule)


# --- POLICY TRANSITIONS ---
def t1_5_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_1 > 5


t1_5 = PolicyTransition(t1_5_rule)


def t1_10_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_1 > 10


t1_10 = PolicyTransition(t1_10_rule)


def t3_5_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_3 > 5


t3_5 = PolicyTransition(t3_5_rule)


def t3_10_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_3 > 10


t3_10 = PolicyTransition(t3_10_rule)


# --- STAGE TRANSITIONS ---
def t2_5_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_2 > 5


t2_5 = StageTransition(t2_5_rule)


def t2_10_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_2 > 10


t2_10 = StageTransition(t2_10_rule)


# --- CURRICULUM ---


MyCurriculum = create_curriculum(name="My Curriculum", version="0.1.0", tasks=(TaskA, TaskB, Graduated))


def construct_curriculum():
    """
    Useful for testing.
    """

    # Init Stages
    taskA = TaskA(task_parameters=TaskAParameters())
    taskB = TaskB(task_parameters=TaskBParameters())
    stageA = Stage(name="StageA", task=taskA)
    stageB = Stage(name="StageB", task=taskB)

    stageA.add_policy_transition(INIT_STAGE, stageA_policyB, t1_10)
    stageA.add_policy_transition(INIT_STAGE, stageA_policyA, t1_5)
    stageA.add_policy_transition(stageA_policyA, stageA_policyB, t1_10)
    stageA.set_start_policies(INIT_STAGE)

    stageB.add_policy_transition(INIT_STAGE, stageB_policyB, t3_10)
    stageB.add_policy_transition(INIT_STAGE, stageB_policyA, t3_5)
    stageB.add_policy_transition(stageB_policyA, stageB_policyB, t3_10)
    stageB.set_start_policies(INIT_STAGE)

    # Construct the Curriculum
    ex_curr = MyCurriculum(name="My Curriculum")
    ex_curr.add_stage_transition(stageA, GRADUATED, t2_10)
    ex_curr.add_stage_transition(stageA, stageB, t2_5)
    ex_curr.add_stage_transition(stageB, GRADUATED, t2_10)

    return ex_curr


if __name__ == "__main__":
    ex_curr = construct_curriculum()
    name = "curriculum"
    with open(
        f"./examples/example_project/assets/{name}_schema.json",
        "w+",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(ex_curr.model_json_schema(), indent=4))
    export_json(ex_curr, path=f"./examples/example_project/assets/{name}.json")
    _ = export_diagram(ex_curr, f"./examples/example_project/assets/{name}.svg")
