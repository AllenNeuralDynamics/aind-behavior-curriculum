"""
Example of Trainer creation
"""

from collections import defaultdict

import example_project as ex

from aind_behavior_curriculum import (
    Curriculum,
    Metrics,
    SubjectHistory,
    Trainer,
)

# Proxy Database
# NOTE: Trainer's concerte implementation
# assumes a higher-level process defines mouse ID's ahead of time
MICE_CURRICULUMS: dict[int, Curriculum] = {}
MICE_SUBJECT_HISTORY: dict[int, SubjectHistory] = defaultdict(SubjectHistory)
MICE_METRICS: dict[int, Metrics] = {
    0: ex.ExampleMetrics(),
    1: ex.ExampleMetrics(),
    2: ex.ExampleMetrics(),
}


class ExampleTrainer(Trainer):
    def __init__(self) -> None:
        """
        Custom init w/ super.__init__()
        Add database connections, etc. here
        """
        super().__init__()

    def load_data(
        self, subject_id: int
    ) -> tuple[Curriculum, SubjectHistory, Metrics]:
        """
        Read from proxy database.
        """
        return (
            MICE_CURRICULUMS[subject_id],
            MICE_SUBJECT_HISTORY[subject_id],
            MICE_METRICS[subject_id],
        )

    def write_data(
        self,
        subject_id: int,
        curriculum: Curriculum,
        history: SubjectHistory,
    ) -> None:
        """
        Add to proxy database.
        """
        MICE_CURRICULUMS[subject_id] = curriculum
        MICE_SUBJECT_HISTORY[subject_id] = history

    def clear_database(self) -> None:
        """
        Testing utility, clears the database for the next unit test.
        """
        MICE_CURRICULUMS: dict[int, Curriculum] = {}
        MICE_SUBJECT_HISTORY: dict[int, SubjectHistory] = defaultdict(list)
        MICE_METRICS: dict[int, Metrics] = {
            0: ex.ExampleMetrics(),
            1: ex.ExampleMetrics(),
            2: ex.ExampleMetrics(),
        }
