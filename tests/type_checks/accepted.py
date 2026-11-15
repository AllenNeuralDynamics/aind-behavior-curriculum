"""
User code that must type-check cleanly (checked by pyright in CI) and
must also run (executed by tests/test_type_checks.py).

Any new pyright error here means a change made the public API harder to use.
"""

import tempfile
from pathlib import Path
from typing import TypeVar, assert_type

from aind_behavior_curriculum import (
    Metrics,
    Policy,
    PolicyTransition,
    Stage,
    StageTransition,
    Task,
    Trainer,
    create_curriculum,
    export_json,
)

from ._models import MyMetrics, MyParams, MyTask


def typed_rule(metrics: MyMetrics, task: MyTask) -> MyTask:
    return task


def metrics_agnostic_rule(metrics: Metrics, task: MyTask) -> MyTask:
    return task


T = TypeVar("T", bound=Task)


def task_agnostic_rule(metrics: Metrics, task: T) -> T:
    return task


def typed_transition(metrics: MyMetrics) -> bool:
    return metrics.score > 0


def generic_transition(metrics: Metrics) -> bool:
    return True


def run() -> None:
    # Rule construction infers precise types
    policy = Policy(typed_rule)
    assert_type(policy, Policy[MyMetrics, MyTask])
    assert_type(PolicyTransition(typed_transition), PolicyTransition[MyMetrics])
    assert_type(StageTransition(generic_transition), StageTransition[Metrics])

    # Metrics contravariance: an already-built rule for `Metrics` is usable where a `MyMetrics` rule is expected
    agnostic_policy = Policy(metrics_agnostic_rule)
    assert_type(agnostic_policy, Policy[Metrics, MyTask])
    as_typed_policy: Policy[MyMetrics, MyTask] = agnostic_policy
    generic_stage_transition = StageTransition(generic_transition)
    as_typed_transition: StageTransition[MyMetrics] = generic_stage_transition
    started_stage: Stage[MyMetrics, MyTask] = Stage(
        name="started", task=MyTask(task_parameters=MyParams()), start_policies=[policy, agnostic_policy]
    )
    assert_type(started_stage.start_policies, list[Policy[MyMetrics, MyTask]])
    _ = (as_typed_policy, as_typed_transition)

    typed_stage: Stage[MyMetrics, MyTask] = Stage(name="typed", task=MyTask(task_parameters=MyParams()))
    typed_stage.add_policy(policy)
    typed_stage.add_policy(Policy(metrics_agnostic_rule))
    typed_stage.add_policy_transition(policy, Policy(task_agnostic_rule), PolicyTransition(generic_transition))

    # Plain functions are accepted wherever they are normalized at runtime
    stage = Stage(name="plain", task=MyTask(task_parameters=MyParams()))
    stage.add_policy_transition(typed_rule, metrics_agnostic_rule, typed_transition)
    stage.set_start_policies([typed_rule])
    stage.set_start_policies(p for p in (typed_rule, metrics_agnostic_rule))
    stage.set_policy_transition_priority(typed_rule, stage.see_policy_transitions(typed_rule))
    assert_type(stage.get_task(), MyTask)

    # Curriculum construction
    curriculum = create_curriculum("TypedCurriculum", "0.0.1", [MyTask])(version="0.0.1", name="TypedCurriculum")
    curriculum.add_stage_transition(stage, typed_stage, typed_transition)
    curriculum.add_stage_transition(typed_stage, stage, StageTransition(generic_transition))
    curriculum.set_stage_transition_priority(stage, curriculum.see_stage_transitions(stage))

    # Trainer helpers accept mixed policies and plain functions
    task = Trainer.get_net_parameter_update(MyTask(task_parameters=MyParams()), [policy, typed_rule], MyMetrics())
    assert_type(task, MyTask)

    # Export helpers accept str paths
    with tempfile.TemporaryDirectory() as tmp:
        export_json(curriculum, str(Path(tmp) / "curriculum.json"))
