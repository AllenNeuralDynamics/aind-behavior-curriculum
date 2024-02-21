"""
Stage-based implementation
"""

from collections import defaultdict

from pydantic import Field
import aind_behavior_curriculum as abc


class Stage(abc.AindBehaviorModel):
    """
    Instance of a Task containing TaskParameters.
    """

    name: str = Field(..., description='Stage name.')
    task: abc.Task = Field(..., description='Task in which this stage is based off of.')

    # TODO: Check serialization of Task and see if overriding the field serializer is necessary
GRADUATED = Stage(...)
# ^TODO, Fill Graduated

class Metrics(abc.AindBehaviorModel):
    """
    Abstract Metrics class.
    Subclass with Metric values.
    """

    # TODO: Add some schema check


class Rule:
    """
    Represents directed edge in curriculum graph.
    NOTE: Rule, a callable, recieves unique serialization
    """

    def __call__(self, metrics: Metrics, **kwargs) -> bool:
        """
        User-defined.
        Input is metrics instance with user-defined Metric subclass schema.
        Returns a True/False go/no-go condition to next stage.

        kwargs: extra information such as the current parameters of a Stage.
        """

        return NotImplementedError

    # TODO: Check serialization of Rule and see what overrides are necessary.


class CurriculumGraph(abc.AindBehaviorModel):
    """
    Graph of mouse tasks.
    Nodes are Stages, instances of tasks.
    Directed Edges are Rules.
    Each Stage holds a reference to a list of Rules
    ordered in transition priority.
    """
    graph: dict[Stage, list[tuple[Rule, Stage]]]


class Curriculum:
    """
    Pairs Curriculum Graph with utilities.
    """

    def __init__(self):
        """
        Simply manages a graph instance.
        """
        self.graph: CurriculumGraph = defaultdict(list)

    def import_curriculum(self, json_data: dict):
        """
        Copy/Pickle Constructor
        """
        self.graph = CurriculumGraph.model_validate_json(json_data)

    def add_transition(self,
                 start_stage: Stage,
                 dest_stage: Stage,
                 rule: Rule,
                 ) -> None:
        """
        Add rule to curriculum graph.
        NOTE: Call this method in the order of transition priority!
        """

        self.graph[start_stage].append((rule, dest_stage))

    def remove_transition(self,
                    start_stage: Stage,
                    rule: Rule,
                    dest_stage: Stage
                    ) -> None:
        """
        Remove a rule from curriculum graph.
        """
        assert start_stage in self.graph.keys(), \
            'start_stage is not in curriculum.'

        assert (rule, dest_stage) in self.graph[start_stage], \
            '(rule, dest_stage) pair is not in curriculum.'

        self.graph[start_stage].remove((rule, dest_stage))

    def see_transitions(self, stage: Stage) -> list[tuple[Rule, Stage]]:
        """
        See transitions of stage in curriculum graph.
        """
        return self.graph[stage]

    def see_stages(self) -> list[Stage]:
        """
        See stages of curriculum graph.
        """
        return list(self.graph.keys())

    def export_curriculum():
        """
        Call serialization on curriculum graph instance.
        """
        # TODO

    def export_visual():
        """
        Export visual representation of curriculum to inspect correctness.
        """
        # TODO


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

            current_stage = stage_history[-1]
            transitions = curriculum.see_transitions(current_stage)
            for t_eval, t_stage in transitions:
                # On first true evaluation, update stage history
                # and publish back to database.
                if t_eval(curr_metrics):
                    stage_history.append(t_stage)
                    self.write_data(m_id, curriculum, stage_history)
                    break

    def override_mouse_stage(self, m_id: int, override_stage: Stage):
        """
        Override mouse stage 
        """
        assert m_id in self.mouse_ids, \
            f'mouse id {m_id} not in self.mouse_ids.'

        a, b, c = self.load_data(m_id)
        curriculum: Curriculum = a
        stage_history: list[Stage] = b
        curr_metrics: Metrics = c

        assert override_stage in curriculum.see_stages(), \
            f'override stage {override_stage} not in curriculum stages for mouse id {m_id}.'

        stage_history.append(override_stage)
        self.write_data(m_id, curriculum, stage_history)

    def export_visual(self):
        """
        Export visual representation of curriculum to inspect status.
        """

        # TODO