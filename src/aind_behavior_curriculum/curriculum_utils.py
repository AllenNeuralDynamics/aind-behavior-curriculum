"""
Useful Placeholders when making Curriculums
"""

from typing import Literal

from pydantic import Field

from aind_behavior_curriculum import (
    Metrics,
    Policy,
    Stage,
    Task,
    TaskParameters,
)


def init_stage_rule(
    metrics: Metrics, task_params: TaskParameters
) -> TaskParameters:
    """
    Trivially pass the default
    """
    return task_params


INIT_STAGE = Policy(rule=init_stage_rule)


def create_empty_stage(s: Stage) -> Stage:
    """
    Prepares empty stage with tacit policy initalization.
    Convenient for initalizing many empty stages.
    """

    s.add_policy(INIT_STAGE)
    s.set_start_policies(INIT_STAGE)
    return s


class Graduated(Task):
    name: Literal["Graduated"] = "Graduated"
    task_parameters: TaskParameters = Field(
        default=TaskParameters(), description="Fill w/ Parameter Defaults"
    )

GRADUATED = create_empty_stage(
    Stage(name='GRADUATED', task=Graduated())
)
