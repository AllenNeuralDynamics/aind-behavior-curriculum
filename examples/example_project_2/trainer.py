"""
Example of Trainer creation
"""

from collections import defaultdict

import example_project as ex

from aind_behavior_curriculum import Curriculum, Metrics, Trainer, TrainerState

# Proxy Database
# NOTE: Trainer's concerte implementation
# assumes a higher-level process defines mouse ID's ahead of time
MICE_CURRICULUMS: dict[int, Curriculum] = {}
MICE_SUBJECT_HISTORY: dict[int, TrainerState] = defaultdict(list)
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
    ) -> tuple[Curriculum, TrainerState, Metrics]:
        """
        Read from proxy database.
        """
        return (
            MICE_CURRICULUMS[subject_id],
            MICE_SUBJECT_HISTORY[subject_id][-1],
            MICE_METRICS[subject_id],
        )

    @Trainer.log_subject_history
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

    def clear_database(self) -> None:
        """
        Testing utility, clears the database for the next unit test.
        """
        MICE_CURRICULUMS: dict[int, Curriculum] = {}
        MICE_SUBJECT_HISTORY: dict[int, TrainerState] = defaultdict(list)
        MICE_METRICS: dict[int, Metrics] = {
            0: ex.ExampleMetrics(),
            1: ex.ExampleMetrics(),
            2: ex.ExampleMetrics(),
        }
