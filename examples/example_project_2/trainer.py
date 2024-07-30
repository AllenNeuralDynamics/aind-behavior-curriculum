"""
Example of Trainer creation
"""

from collections import defaultdict
from typing import Callable, Dict

import example_project_2 as ex2

from aind_behavior_curriculum import Curriculum, Metrics, Trainer, TrainerState

# Proxy Database
# NOTE: Trainer's concerte implementation
# assumes a higher-level process defines mouse ID's ahead of time
MICE_CURRICULUMS: dict[int, Curriculum] = {}
MICE_SUBJECT_HISTORY: dict[int, list[TrainerState]] = defaultdict(list)
MICE_METRICS: dict[int, Metrics] = {
    0: ex2.ExampleMetrics2(),
    1: ex2.ExampleMetrics2(),
    2: ex2.ExampleMetrics2(),
}


class ExampleTrainer(Trainer):
    def __init__(self) -> None:
        """
        Custom init w/ super.__init__()
        Add database connections, etc. here
        """
        super().__init__()

        self.subject_history: Dict[int, TrainerState] = defaultdict(list)

    def load_data(
        self, subject_id: int
    ) -> tuple[Curriculum, TrainerState, Metrics]:
        """
        Read from proxy database.
        """
        return (
            MICE_CURRICULUMS[subject_id],
            MICE_SUBJECT_HISTORY[subject_id][-1],
            MICE_METRICS[subject_id],
        )

    def write_data(
        self,
        subject_id: int,
        curriculum: Curriculum,
        trainer_state: TrainerState,
    ) -> None:
        """
        Add to proxy database.
        """
        MICE_CURRICULUMS[subject_id] = curriculum
        MICE_SUBJECT_HISTORY[subject_id].append(trainer_state)

        self.subject_history[subject_id].append(trainer_state)
