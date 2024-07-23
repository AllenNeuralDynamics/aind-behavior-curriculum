"""
Example of Curriculum creation
"""

import json
from typing import Literal

from pydantic import Field

from aind_behavior_curriculum import (
    GRADUATED,
    INIT_STAGE,
    Curriculum,
    Metrics,
    Policy,
    PolicyTransition,
    Stage,
    StageGraph,
    StageTransition,
    Task,
    TaskParameters,
    get_task_types,
)


# --- TASKS ---
class TaskAParameters(TaskParameters):
    field_a: int = Field(default=0, validate_default=True)


class TaskA(Task):
    name: Literal["Task A"] = "Task A"
    task_parameters: TaskAParameters = Field(
        ..., description="Fill w/ Parameter Defaults", validate_default=True
    )


class TaskBParameters(TaskParameters):
    field_b: float = Field(default=0.0)


class TaskB(Task):
    name: Literal["Task B"] = "Task B"
    task_parameters: TaskBParameters = Field(
        ..., description="Fill w/ Parameter Defaults"
    )


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
def stageA_policyA_rule(
    metrics: ExampleMetrics, task_params: TaskAParameters
) -> TaskAParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_a = 8
    return task_params


stageA_policyA = Policy(rule=stageA_policyA_rule)


def stageA_policyB_rule(
    metrics: ExampleMetrics, task_params: TaskAParameters
) -> TaskAParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_a = 16
    return task_params


stageA_policyB = Policy(rule=stageA_policyB_rule)


def stageB_policyA_rule(
    metrics: ExampleMetrics, task_params: TaskBParameters
) -> TaskBParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_b = 8
    return task_params


stageB_policyA = Policy(rule=stageB_policyA_rule)


def stageB_policyB_rule(
    metrics: ExampleMetrics, task_params: TaskBParameters
) -> TaskBParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_b = 16
    return task_params


stageB_policyB = Policy(rule=stageB_policyB_rule)


# --- POLICY TRANSTITIONS ---
def t1_5_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_1 > 5


t1_5 = PolicyTransition(rule=t1_5_rule)


def t1_10_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_1 > 10


t1_10 = PolicyTransition(rule=t1_10_rule)


def t3_5_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_3 > 5


t3_5 = PolicyTransition(rule=t3_5_rule)


def t3_10_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_3 > 10


t3_10 = PolicyTransition(rule=t3_10_rule)


# --- STAGE TRANSITIONS ---
def t2_5_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_2 > 5


t2_5 = StageTransition(rule=t2_5_rule)


def t2_10_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_2 > 10


t2_10 = StageTransition(rule=t2_10_rule)


# --- CURRICULUM ---
Tasks = get_task_types()


class MyCurriculum(Curriculum):
    name: Literal["My Curriculum"] = "My Curriculum"
    # graph: StageGraph[Union[TaskA, TaskB, Graduated]] = Field(default=StageGraph())
    graph: StageGraph[Tasks] = Field(default=StageGraph[Tasks]())  # type: ignore


def construct_curriculum() -> MyCurriculum:
    """
    Useful for testing.
    """

    with open("examples/example_project/jsons/schema.json", "w") as f:
        f.write(json.dumps(MyCurriculum.model_json_schema(), indent=4))

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

    with open("examples/example_project/jsons/stage_instance.json", "w") as f:
        stageA = ex_curr.see_stages()[0]
        json_dict = stageA.model_dump()
        json_string = json.dumps(json_dict, indent=4)
        f.write(json_string)

    with open("examples/example_project/jsons/curr_instance.json", "w") as f:
        json_dict = ex_curr.model_dump()
        json_string = json.dumps(json_dict, indent=4)
        f.write(json_string)

    # with open("examples/example_project/jsons/curr_instance.json", "r") as f:
    #     ex_curr = MyCurriculum.model_validate_json(f.read())
    #     print(ex_curr)

    ex_curr.export_diagram(
        "examples/example_project/diagrams/my_curr_diagram.png"
    )
