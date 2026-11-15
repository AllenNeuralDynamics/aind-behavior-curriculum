"""
Example of a curriculum using subject-level Globals.

Animals report the shape on the screen: one shape means "push left",
the other "push right". To counterbalance motor output, half of the animals
are trained with circle -> left and the other half with square -> left.
This contingency is fixed per animal and must survive every stage transition,
while everything else resets to the new stage's defaults.

Run the demo from the `examples` directory with: python -m example_project_globals
"""

from typing import Literal

from pydantic import Field

from aind_behavior_curriculum import (
    Curriculum,
    Globals,
    Metrics,
    Policy,
    PolicyTransition,
    Stage,
    StageEntryRule,
    StageGraph,
    StageTransition,
    Task,
    TaskParameters,
    make_task_discriminator,
)

__all__ = [
    "CounterbalanceGlobals",
    "ShapeReportMetrics",
    "ShapeReportParameters",
    "ShapeReportTask",
    "ShapeReportCurriculum",
    "construct_curriculum",
]


# --- TASK ---
class ShapeReportParameters(TaskParameters):
    is_left_circle: bool = Field(default=True, description="If True, circle -> left and square -> right.")
    response_delay: float = Field(default=0.0, ge=0, description="Time (s) the animal must withhold its response.")


class ShapeReportTask(Task):
    name: Literal["ShapeReport"] = "ShapeReport"
    task_parameters: ShapeReportParameters = Field(default_factory=ShapeReportParameters)


# --- GLOBALS ---
# Subject-level variables that persist across all stages.
# Set once on enrollment; the Trainer never modifies them.
class CounterbalanceGlobals(Globals):
    is_left_circle: bool = Field(description="The animal's shape -> side contingency.")


# --- METRICS ---
class ShapeReportMetrics(Metrics):
    performance: float = Field(default=0.0, ge=0, le=1)


# --- STAGE ENTRY RULE ---
# Runs once, whenever a subject enters a stage, on that stage's default task.
# The Globals type is taken from the first parameter's annotation: the subject's
# globals are validated into CounterbalanceGlobals before the rule is called.
def apply_counterbalance(globals: CounterbalanceGlobals, task: ShapeReportTask) -> ShapeReportTask:
    task.task_parameters.is_left_circle = globals.is_left_circle
    return task


# --- POLICIES ---
def keep_task(metrics: ShapeReportMetrics, task: ShapeReportTask) -> ShapeReportTask:
    return task


def increase_delay(metrics: ShapeReportMetrics, task: ShapeReportTask) -> ShapeReportTask:
    task.task_parameters.response_delay += 0.1
    return task


def performance_above_70(metrics: ShapeReportMetrics) -> bool:
    return metrics.performance > 0.7


def performance_above_80(metrics: ShapeReportMetrics) -> bool:
    return metrics.performance > 0.8


# --- CURRICULUM ---
Tasks = make_task_discriminator([ShapeReportTask])


class ShapeReportCurriculum(Curriculum):
    name: Literal["ShapeReportCurriculum"] = "ShapeReportCurriculum"
    version: Literal["0.1.0"] = "0.1.0"
    graph: StageGraph[Metrics, Tasks] = Field(default_factory=StageGraph[Metrics, Tasks])  # type: ignore


def construct_curriculum() -> ShapeReportCurriculum:
    # The same entry rule is attached to every stage that needs the contingency.
    counterbalance = StageEntryRule(apply_counterbalance)

    # Stage 1: respond as soon as the stimulus appears.
    immediate = Stage(name="Immediate", task=ShapeReportTask(), on_entry=counterbalance)

    # Stage 2: withhold the response; the delay grows while performance is high.
    withhold = Stage(
        name="Withhold",
        task=ShapeReportTask(task_parameters=ShapeReportParameters(response_delay=0.5)),
        on_entry=counterbalance,
    )
    withhold.add_policy_transition(Policy(keep_task), Policy(increase_delay), PolicyTransition(performance_above_70))
    withhold.set_start_policies(Policy(keep_task))

    curriculum = ShapeReportCurriculum()
    curriculum.add_stage_transition(immediate, withhold, StageTransition(performance_above_80))
    return curriculum
