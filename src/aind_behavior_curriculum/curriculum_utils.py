"""
Useful Placeholders when making Curriculums
"""

from typing import Any

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


class Graduated(Stage):
    """
    Optional:
    Use this Stage as the final Stage in a Curriculums's PolicyGraph.
    """

    name: str = Field("GRADUATED STAGE", description="Stage name.")
    task: Task = Task(
        name="Empty Task",
        version="0.0.0",
        task_parameters=TaskParameters(),
    )

    def model_post_init(self, __context: Any) -> None:
        """
        Trivially add placeholder stage
        """
        self.add_policy(INIT_STAGE)


GRADUATED = Graduated()
