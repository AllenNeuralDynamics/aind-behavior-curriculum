"""
Example of Curriculum creation
"""

import json
from typing import Literal, Union

from pydantic import Field

import aind_behavior_curriculum as abc


# --- TASKS ---
class TaskAParameters(abc.TaskParameters):
    field_a: int = abc.ModifiableAttr(default=0)


class TaskA(abc.Task):
    name: Literal["Task A"] = "Task A"
    task_parameters: TaskAParameters = Field(
        ..., description="Fill w/ Parameter Defaults"
    )


class TaskBParameters(abc.TaskParameters):
    field_b: float = abc.ModifiableAttr(default=0.0)


class TaskB(abc.Task):
    name: Literal["Task B"] = "Task B"
    task_parameters: TaskBParameters = Field(
        ..., description="Fill w/ Parameter Defaults"
    )


# --- METRICS ---
class ExampleMetrics(abc.Metrics):
    """
    Totally made up values we will edit ourselves to simulate mouse training.
    Each theta value is reserved for a test case.
    """

    theta_1: int = abc.ModifiableAttr(default=0)
    theta_2: int = abc.ModifiableAttr(default=0)
    theta_3: int = abc.ModifiableAttr(default=0)


# --- STAGES ---
class StageA(abc.Stage):
    name: Literal["Stage A"] = "Stage A"
    task: TaskA = Field(..., description="Fill with Task Instance")


class StageB(abc.Stage):
    name: Literal["Stage B"] = "Stage B"
    task: TaskB = Field(..., description="Fill with Task Instance")


# --- POLICIES ---
def stageA_policyA_rule(metrics: ExampleMetrics,
                   task_params: TaskAParameters
                   ) -> TaskAParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_a = 8
    return task_params
stageA_policyA = abc.Policy(rule=stageA_policyA_rule)

def stageA_policyB_rule(metrics: ExampleMetrics,
                   task_params: TaskAParameters
                   ) -> TaskAParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_a = 16
    return task_params
stageA_policyB = abc.Policy(rule=stageA_policyB_rule)

def stageB_policyA_rule(metrics: ExampleMetrics,
                   task_params: TaskBParameters
                   ) -> TaskBParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_b = 8
    return task_params
stageB_policyA = abc.Policy(rule=stageB_policyA_rule)

def stageB_policyB_rule(metrics: ExampleMetrics,
                   task_params: TaskBParameters
                   ) -> TaskBParameters:
    task_params = task_params.model_copy(deep=True)
    task_params.field_b = 16
    return task_params
stageB_policyB = abc.Policy(rule=stageB_policyB_rule)


# --- POLICY TRANSTITIONS ---
def t1_5_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_1 > 5
t1_5 = abc.PolicyTransition(rule=t1_5_rule)

def t1_10_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_1 > 10
t1_10 = abc.PolicyTransition(rule=t1_10_rule)

def t3_5_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_3 > 5
t3_5 = abc.PolicyTransition(rule=t3_5_rule)

def t3_10_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_3 > 10
t3_10 = abc.PolicyTransition(rule=t3_10_rule)


# --- STAGE TRANSITIONS ---
def t2_5_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_2 > 5
t2_5 = abc.StageTransition(rule=t2_5_rule)

def t2_10_rule(metrics: ExampleMetrics) -> bool:
    return metrics.theta_2 > 10
t2_10 = abc.StageTransition(rule=t2_10_rule)


# --- CURRICULUM ---
class MyCurriculum(abc.Curriculum):
    name: Literal["My Curriculum"] = "My Curriculum"

    stages: dict[int, Union[StageA, StageB, abc.Graduated]] = {}
    graph: dict[int, list[tuple[abc.StageTransition, int]]] = {}


def construct_curriculum() -> MyCurriculum:
    """
    Useful for testing.
    """

    # Init Stages
    taskA = TaskA(task_parameters=TaskAParameters())
    taskB = TaskB(task_parameters=TaskBParameters())
    stageA = StageA(task=taskA)
    stageB = StageB(task=taskB)

    stageA.add_policy_transition(abc.INIT_STAGE, stageA_policyA, t1_10)
    stageA.add_policy_transition(abc.INIT_STAGE, stageA_policyA, t1_5)
    stageA.add_policy_transition(stageA_policyA, stageA_policyB, t1_10)

    stageB.add_policy_transition(abc.INIT_STAGE, stageB_policyB, t3_10)
    stageB.add_policy_transition(abc.INIT_STAGE, stageB_policyA, t3_5)
    stageB.add_policy_transition(stageB_policyA, stageB_policyB, t3_10)

    # Construct the Curriculum
    ex_curr = MyCurriculum(name="My Curriculum")
    ex_curr.add_stage_transition(stageA, abc.GRADUATED, t2_10)
    ex_curr.add_stage_transition(stageA, stageB, t2_5)
    ex_curr.add_stage_transition(stageB, abc.GRADUATED, t2_10)

    return ex_curr


if __name__ == "__main__":
    ex_curr = construct_curriculum()

    with open("examples/stage_instance.json", "w") as f:
        stageA = ex_curr.stages[0]
        json_dict = stageA.model_dump()
        json_string = json.dumps(json_dict, indent=4)
        f.write(json_string)

    with open("examples/curr_instance.json", "w") as f:
        json_dict = ex_curr.model_dump()
        json_string = json.dumps(json_dict, indent=4)
        f.write(json_string)
