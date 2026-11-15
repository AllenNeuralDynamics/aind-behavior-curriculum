"""Shared user-style models for the static type-check fixtures."""

from typing import Literal

from aind_behavior_curriculum import Metrics, Task, TaskParameters


class MyParams(TaskParameters):
    value: int = 0


class MyTask(Task[MyParams]):
    name: Literal["MyTask"] = "MyTask"  # pyright: ignore[reportIncompatibleVariableOverride]


class OtherTask(Task[MyParams]):
    name: Literal["OtherTask"] = "OtherTask"  # pyright: ignore[reportIncompatibleVariableOverride]


class MyMetrics(Metrics):
    score: int = 0
