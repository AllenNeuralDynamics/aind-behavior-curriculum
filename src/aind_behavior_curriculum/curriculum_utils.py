"""
Useful Placeholders when making Curriculums
"""

from typing import Annotated, Literal, Union

from pydantic import Field

from aind_behavior_curriculum.curriculum import Metrics, Policy, Stage
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

    Tasks = Annotated[
        Union[tuple(Task.__subclasses__())], Field(discriminator="name")
    ]
    return Tasks


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
    """
    Utility Final Task.
    """

    name: Literal["Graduated"] = "Graduated"
    task_parameters: TaskParameters = Field(
        default=TaskParameters(), description="Fill w/ Parameter Defaults"
    )


GRADUATED = create_empty_stage(Stage(name="GRADUATED", task=Graduated()))
