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
class StageA_PolicyA(abc.Policy):
    def __call__(
        self, metrics: abc.Metrics, task_params: abc.TaskParameters
    ) -> abc.TaskParameters:
        param_dict = task_params.model_dump()
        param_dict["field_a"] = 8

        task_param_class = type(task_params)
        return task_param_class.model_validate(param_dict)


class StageA_PolicyB(abc.Policy):
    def __call__(
        self, metrics: abc.Metrics, task_params: abc.TaskParameters
    ) -> abc.TaskParameters:
        param_dict = task_params.model_dump()
        param_dict["field_a"] = 16

        task_param_class = type(task_params)
        return task_param_class.model_validate(param_dict)


class StageB_PolicyA(abc.Policy):
    def __call__(
        self, metrics: abc.Metrics, task_params: abc.TaskParameters
    ) -> abc.TaskParameters:
        param_dict = task_params.model_dump()
        param_dict["field_b"] = 8

        task_param_class = type(task_params)
        return task_param_class.model_validate(param_dict)


class StageB_PolicyB(abc.Policy):
    def __call__(
        self, metrics: abc.Metrics, task_params: abc.TaskParameters
    ) -> abc.TaskParameters:
        param_dict = task_params.model_dump()
        param_dict["field_b"] = 16

        task_param_class = type(task_params)
        return task_param_class.model_validate(param_dict)


# --- POLICY TRANSTITIONS ---
class T1_5(abc.PolicyTransition):
    def __call__(self, metrics: abc.Metrics) -> bool:
        return metrics.theta_1 > 5


class T1_10(abc.PolicyTransition):
    def __call__(self, metrics: abc.Metrics) -> bool:
        return metrics.theta_1 > 10


class T3_5(abc.PolicyTransition):
    def __call__(self, metrics: abc.Metrics) -> bool:
        return metrics.theta_3 > 5


class T3_10(abc.PolicyTransition):
    def __call__(self, metrics: abc.Metrics) -> bool:
        return metrics.theta_3 > 10


# --- STAGE TRANSITIONS ---
class T2_5(abc.StageTransition):
    def __call__(self, metrics: abc.Metrics) -> bool:
        return metrics.theta_2 > 5


class T2_10(abc.StageTransition):
    def __call__(self, metrics: abc.Metrics) -> bool:
        return metrics.theta_2 > 10


class MyCurriculum(abc.Curriculum):
    name: Literal["My Curriculum"] = "My Curriculum"
    metrics: ExampleMetrics = Field(...)

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
    stageA.add_policy_transition(abc.INIT_STAGE, StageA_PolicyB(), T1_10())
    stageA.add_policy_transition(abc.INIT_STAGE, StageA_PolicyA(), T1_5())
    stageA.add_policy_transition(StageA_PolicyA(), StageA_PolicyB(), T1_10())

    stageB.add_policy_transition(abc.INIT_STAGE, StageB_PolicyB(), T3_10())
    stageB.add_policy_transition(abc.INIT_STAGE, StageB_PolicyA(), T3_5())
    stageB.add_policy_transition(StageB_PolicyA(), StageB_PolicyB(), T3_10())

    # Construct the Curriculum
    ex_curr = MyCurriculum(name="My Curriculum", metrics=ExampleMetrics())
    ex_curr.add_stage_transition(stageA, abc.GRADUATED, T2_10())
    ex_curr.add_stage_transition(stageA, stageB, T2_5())
    ex_curr.add_stage_transition(stageB, abc.GRADUATED, T2_10())

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
