"""
User mistakes that pyright must keep rejecting. Never executed.

Each line holds exactly one mistake, suppressed with a rule-specific ignore.
Because `reportUnnecessaryTypeIgnoreComment` is an error, CI fails if the
library ever stops flagging one of these lines.
"""

from aind_behavior_curriculum import Metrics, Policy, PolicyTransition, Stage, StageTransition, Task, Trainer

from ._models import MyMetrics, MyParams, MyTask, OtherTask


def int_metrics_rule(metrics: int, task: MyTask) -> MyTask:
    return task


def returns_other_task(metrics: MyMetrics, task: MyTask) -> OtherTask:
    return OtherTask(task_parameters=MyParams())


def returns_base_task(metrics: Metrics, task: Task) -> Task:
    return task


def str_transition(metrics: MyMetrics) -> str:
    return ""


def subclass_metrics_transition(metrics: MyMetrics) -> bool:
    return True


def _never_called(typed_stage: Stage[MyMetrics, MyTask], base_stage: Stage[Metrics, MyTask]) -> None:
    # Metrics must be a `Metrics` subclass
    Policy(int_metrics_rule)  # pyright: ignore[reportArgumentType]
    # Policies must return the stage's task type
    typed_stage.add_policy(returns_other_task)  # pyright: ignore[reportArgumentType]
    typed_stage.add_policy(returns_base_task)  # pyright: ignore[reportArgumentType]
    # Transitions must return bool
    PolicyTransition(str_transition)  # pyright: ignore[reportArgumentType]
    # Contravariance is one-way: a rule needing `MyMetrics` cannot serve a stage that only provides `Metrics`
    base_stage.add_policy_transition(
        base_stage.see_policies()[0],
        base_stage.see_policies()[0],
        PolicyTransition(subclass_metrics_transition),  # pyright: ignore[reportArgumentType]
    )
    _: StageTransition[Metrics] = StageTransition(subclass_metrics_transition)  # pyright: ignore[reportAssignmentType]
    # Policies written for `MyMetrics` cannot be evaluated with base `Metrics`
    Trainer.get_net_parameter_update(
        MyTask(task_parameters=MyParams()),
        [Policy(returns_my_task)],
        Metrics(),  # pyright: ignore[reportArgumentType]
    )


def returns_my_task(metrics: MyMetrics, task: MyTask) -> MyTask:
    return task
