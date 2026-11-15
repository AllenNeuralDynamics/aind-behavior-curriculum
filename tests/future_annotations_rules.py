"""
Rules defined in a module using postponed evaluation of annotations.
Used by test_typing.py; not a test module itself.
"""

from __future__ import annotations

from typing import Any

from aind_behavior_curriculum import Metrics, Task


def policy_rule(metrics: Metrics, task: Task) -> Task:
    return task


def any_transition(metrics: Any) -> Any:
    return True


def optional_transition(metrics: Metrics | None) -> bool:
    return True


def wrong_transition(metrics: int) -> bool:
    return True


class RuleHolder:
    @staticmethod
    def transition(metrics: Metrics) -> bool:
        return True
