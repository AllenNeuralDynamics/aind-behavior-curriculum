# Getting started

## Installation

=== "pip"

    ```bash
    pip install aind-behavior-curriculum
    ```

=== "uv"

    ```bash
    uv add aind-behavior-curriculum
    ```

!!! note

    Diagram export needs [Graphviz](https://graphviz.org/) installed and on your `PATH`.

## Your first curriculum

A curriculum is built from a task, a set of metrics and a rule that moves a mouse from one stage to the next.

```python
from pydantic import Field

from aind_behavior_curriculum import (
    GRADUATED,
    Metrics,
    Stage,
    StageTransition,
    TaskParameters,
    create_curriculum,
    create_task,
)


class LickParameters(TaskParameters):
    reward_size: float = Field(default=2.0)


class MyMetrics(Metrics):
    n_trials: int = 0


LickTask = create_task(name="Lick Task", task_parameters=LickParameters)
MyCurriculum = create_curriculum(name="My Curriculum", version="0.1.0", tasks=(LickTask,))


def enough_trials(metrics: MyMetrics) -> bool:
    return metrics.n_trials > 200


stage = Stage(name="Stage 1", task=LickTask(task_parameters=LickParameters()))
curriculum = MyCurriculum(name="My Curriculum")
curriculum.add_stage_transition(stage, GRADUATED, StageTransition(enough_trials))
```

Render it to review the graph:

```python
from aind_behavior_curriculum.curriculum_utils import export_diagram

export_diagram(curriculum, "my_curriculum.svg")
```

## Where to go next

1. Read the [concepts](concepts/curriculum.md) to understand stages, transitions, policies and the trainer.
2. Follow the [guides](guides/building.md) to structure a real curriculum.
3. Browse the [examples](examples/index.md) to see complete, rendered curricula.
