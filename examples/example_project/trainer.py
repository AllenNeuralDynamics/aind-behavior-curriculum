"""
Example of Trainer creation
"""

from collections import defaultdict

import aind_behavior_curriculum as abc
import example_project as ex


# Proxy Database
# NOTE: Trainer's concerte implementation
# assumes a higher-level process defines mouse ID's ahead of time
MICE_CURRICULUMS: dict[int, abc.Curriculum] = {}
MICE_STAGE_HISTORY: dict[int, list[tuple[abc.Stage, abc.Policy]]] = defaultdict(list)
MICE_METRICS: dict[int, abc.Metrics] = {0: ex.ExampleMetrics(),
                                        1: ex.ExampleMetrics(),
                                        2: ex.ExampleMetrics()}


class ExampleTrainer(abc.Trainer):
    def __init__(self) -> None:
        super().__init__()
        self.m_ids = []

    def load_data(self,
                  mouse_id: int
                  ) -> tuple[abc.Curriculum,
                             list[tuple[abc.Stage, abc.Policy]],
                             abc.Metrics]:
        """
        Read from proxy database.
        """
        return (MICE_CURRICULUMS[mouse_id],
                MICE_STAGE_HISTORY[mouse_id],
                MICE_METRICS[mouse_id])

    def write_data(self,
                   mouse_id: int,
                   curriculum: abc.Curriculum,
                   history: list[tuple[abc.Stage, abc.Policy]]
                   ) -> None:
        """
        Add to proxy database.
        """
        MICE_CURRICULUMS[mouse_id] = curriculum
        MICE_STAGE_HISTORY[mouse_id] = history
        self.m_ids.append(mouse_id)

    @property
    def mouse_ids(self) -> list[int]:
        """
        Return managed mouse_ids.
        """
        return self.m_ids


if __name__ == "__main__":
    # TODO: TEST THIS

    # Simulation: Alternate between evaluating mice
    # and editing metrics.
    ex_trainer = ExampleTrainer()
    ex_trainer.evaluate_mice()
    MICE_METRICS[...] = ...

    ex_trainer.evaluate_mice()
    MICE_METRICS[...] = ...

    ex_trainer.evaluate_mice()
    MICE_METRICS[...] = ...