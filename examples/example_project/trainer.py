"""
Example of Trainer creation
"""

from collections import defaultdict

import example_project as ex

import aind_behavior_curriculum as abc

# Proxy Database
# NOTE: Trainer's concerte implementation
# assumes a higher-level process defines mouse ID's ahead of time
MICE_CURRICULUMS: dict[int, abc.Curriculum] = {}
MICE_STAGE_HISTORY: dict[int, list[tuple[abc.Stage, abc.Policy]]] = (
    defaultdict(list)
)
MICE_METRICS: dict[int, abc.Metrics] = {
    0: ex.ExampleMetrics(),
    1: ex.ExampleMetrics(),
    2: ex.ExampleMetrics(),
}


class ExampleTrainer(abc.Trainer):
    def __init__(self) -> None:
        """
        Custom init w/ super.__init__()
        Add database connections, etc. here
        """
        super().__init__()


    def load_data(
        self, subject_id: int
    ) -> tuple[
        abc.Curriculum, list[tuple[abc.Stage, abc.Policy]], abc.Metrics
    ]:
        """
        Read from proxy database.
        """
        return (
            MICE_CURRICULUMS[subject_id],
            MICE_STAGE_HISTORY[subject_id],
            MICE_METRICS[subject_id],
        )

    def write_data(
        self,
        subject_id: int,
        curriculum: abc.Curriculum,
        history: list[tuple[abc.Stage, abc.Policy]],
    ) -> None:
        """
        Add to proxy database.
        """
        MICE_CURRICULUMS[subject_id] = curriculum
        MICE_STAGE_HISTORY[subject_id] = history
