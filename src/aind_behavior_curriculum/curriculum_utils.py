"""
Useful Placeholders when making Curriculums
"""

from typing import Literal

from pydantic import Field

from aind_behavior_curriculum.curriculum import (
    Metrics,
    Policy,
    Stage,
    make_task_discriminator,
)
from aind_behavior_curriculum.task import Task, TaskParameters


def get_task_types():
    """
    Used for Curriculum StageGraph declaration.
    Ex:

    Tasks = get_task_types()

    class MyCurriculum(Curriculum):
        name: Literal["My Curriculum"] = "My Curriculum"
        graph: StageGraph[Tasks] = Field(default=StageGraph())

    Explanation:

    Invokes Task.__subclasses__() in the module in which all Tasks have been defined.

    """

    return make_task_discriminator(*Task.__subclasses__())


def init_stage_rule(
    metrics: Metrics, task_params: TaskParameters
) -> TaskParameters:
    """
    Trivially pass the default
    """
    return task_params


INIT_STAGE = Policy(rule=init_stage_rule)


class Graduated(Task):
    """
    Utility Final Task.
    """

    name: Literal["Graduated"] = "Graduated"
    task_parameters: TaskParameters = Field(
        default=TaskParameters(), description="Fill w/ Parameter Defaults"
    )


GRADUATED = Stage(name="GRADUATED", task=Graduated())
