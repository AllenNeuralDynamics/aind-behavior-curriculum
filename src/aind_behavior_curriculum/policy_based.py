"""
Policy-based implementation

- Define notion of 'Parameter' which contains extra rate information.
- Curriculum defines a series of 'base tasks' as opposed to enumerating
every possible stage change.
- Trainer chooses a transition in the following order:
    - First, check if any rules inside Curriculum are True in listed order
    - Otherwise, perform a parameter update according to the rates defined
    in the 'Parameter' class. For this implementation, each parameter is
    updated independently of the other parameters.

This Trainer loop allows a mouse to take large steps along Base Stage transitions
or small steps along policy update transitions.

This implementation does not provide the full flexibility of
transitioning between any two arbitrary stages forwards/backwards,
but approximates this arbitrary transition through large/small steps.
"""

from copy import deepcopy

from pydantic import Field
import aind_behavior_curriculum as abc


# *** New Parameter Abstraction ***
# Intended to be used as type inside of TaskParameters.
class Parameter(abc.AindBehaviorModel):
    curr_value: float = Field(..., description='Initalized with base parameter value.')
    rate_of_change: float = Field(..., description='Parameter increment.')
    max_value: float = Field(..., description='Maximum value parameter can be incremented to.')


class Stage(abc.AindBehaviorModel):
    """
    See stage_based.py
    """


class Metrics(abc.AindBehaviorModel):
    """
    See stage_based.py
    """


class Rule:
    """
    See stage_based.py
    """


class CurriculumGraph(abc.AindBehaviorModel):
    """
    See stage_based.py
    """


class Curriculum:
    """
    See stage_based.py
    """


class Trainer:
    """
    Pulls mouse curriculum and history,
    and performs fundamental curriculum evaluation/update.
    """

    def load_data(self,
                  mouse_id: int
                  ) -> tuple[Curriculum,
                             list[Stage],
                             Metrics]:
        """
        User-defined.
        Loads 3 pieces of data in the following format:
        - Mouse Curriculum
        - List of Stage History
        - Mouse Metrics
        """
        raise NotImplementedError

    def write_data(self,
                   mouse_id: int,
                   curriculum: Curriculum,
                   history: list[Stage],
                   ) -> None:
        """
        User-defined.
        Exports 3 pieces of data to database.
        - Mouse Id
        - Mouse Curriculum
        - List of Stage History
        """
        raise NotImplementedError

    @property
    def mouse_ids(self) -> list[int]:
        """
        User-defined.
        Returns list of mouse ids that this Trainer is managing.
        """
        raise NotImplementedError

    def evaluate_past_session(self):
        """
        Calls user-defined functions to automatically update
        mouse stage along curriculum.
        """

        for m_id in self.mouse_ids:
            a, b, c = self.load_data(m_id)
            curriculum: Curriculum = a
            stage_history: list[Stage] = b
            curr_metrics: Metrics = c

            current_stage: Stage = stage_history[-1]
            transitions = curriculum.see_transitions(current_stage)
            for t_eval, t_stage in transitions:
                # On first true evaluation, update stage history
                # and publish back to database.
                if t_eval(curr_metrics):
                    stage_history.append(t_stage)
                    self.write_data(m_id, curriculum, stage_history)

                # If all transitions evaluate to False,
                # update stage history with policy update
                # and publish back to database.
                elif (t_eval, t_stage) == transitions[-1]:
                    modified_stage = deepcopy(current_stage)

                    all_parameters = modified_stage.task.task_parameters
                    task_parameters: list[Parameter] = [getattr(all_parameters, attr)
                                              for attr in all_parameters.model_fields
                                              if isinstance(getattr(all_parameters, attr), Parameter)]
                    for p in task_parameters:
                        p.curr_value = min(p.curr_value + p.rate_of_change,
                                           p.max_value)

                    stage_history.append(modified_stage)
                    self.write_data(m_id, curriculum, stage_history)

    def override_mouse_stage(self, m_id: int, override_stage: Stage):
        """
        See stage_based.py
        """

    def export_visual(self):
        """
        See stage_based.py
        """
