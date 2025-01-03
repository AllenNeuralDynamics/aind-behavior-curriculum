"""
Useful Placeholders when making Curriculums
"""

from typing import Literal

from pydantic import Field

from aind_behavior_curriculum.curriculum import Stage
from aind_behavior_curriculum.task import Task, TaskParameters


class Graduated(Task):
    """
    Utility Final Task.
    """

    name: Literal["Graduated"] = "Graduated"
    task_parameters: TaskParameters = Field(
        default=TaskParameters(), description="Fill w/ Parameter Defaults"
    )


GRADUATED = Stage(name="GRADUATED", task=Graduated())
