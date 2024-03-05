"""
Stage-based implementation
"""

from abc import abstractmethod
from collections import defaultdict
from importlib import import_module
from typing import Any, Callable

from pydantic import Field, GetJsonSchemaHandler
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue

import aind_behavior_curriculum as abc


class Metrics(abc.AindBehaviorModel):
    """
    Abstract Metrics class.
    Subclass with Metric values.
    """
    pass


class Rule:
    """
    Custom Pydantic Type that defines de/serialiation for Callables.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        """
        Custom validation, Ref:
        https://docs.pydantic.dev/latest/concepts/types/#as-a-method-on-a-custom-type
        """

        def validate_from_str(value: str) -> Callable:
            """Pass string through deserialization."""
            return cls._deserialize_callable(value)

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(Callable),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(function=cls._serialize_callable),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """
        Custom validation, Ref:
        https://docs.pydantic.dev/latest/concepts/types/#as-a-method-on-a-custom-type
        """
        return handler(core_schema.str_schema())

    @staticmethod
    def _deserialize_callable(value: str | Callable) -> Callable:
        """
        Custom Deserialization.
        Imports function according to package and function name.
        """
        if callable(value):
            return value
        else:
            split = value.rsplit(".", 1)
            if len(split) == 0:
                raise ValueError(
                    "Invalid rule value while attempting to deserialize callable. \
                        Got {value}, expected string in the format 'module.function'}"
                )
            elif len(split) == 1:
                return globals()[split]
            else:
                module = import_module(split[0])
                return getattr(module, split[1])

    @staticmethod
    def _serialize_callable(value: str | Callable) -> Callable:
        """
        Custom Serialization.
        Simply exports reference to function as package + function name.
        """
        if isinstance(value, str):
            value = Rule._deserialize_callable(value)
        return value.__module__ + "." + value.__name__


class Policy(Rule):
    """
    User-defined function that defines
    how current Task parameters change according to metrics.
    """

    def __hash__(self) -> str:
        """
        Custom Hash Function so that Policy
        can be keys inside of a PolicyGraph.
        """
        return self.__module__ + '.' + self.__name__

    @abstractmethod
    def __call__(self,
                 metrics: Metrics,
                 task_params: abc.TaskParameters
                 ) -> abc.TaskParameters:
        """
        User-defined.
        Input is metrics instance with user-defined Metric subclass schema
        and Task instance managed by the current Stage.

        Returns set of updated TaskParameters.
        """
        return NotImplementedError


class InitalizeStage(Policy):
    """
    First Policy in a Stage's Policy Graph.
    """
    def __call__(self, metrics: Metrics, task_params: abc.TaskParameters) -> abc.TaskParameters:
        """
        Trivially pass the default values defined in Task initalization.
        """
        return task_params
INIT_STAGE = InitalizeStage()


class PolicyTransition(Rule):
    """
    User-defined function that defines
    criteria for transitioning between policies based on metrics.
    """

    @abstractmethod
    def __call__(self, metrics: Metrics) -> bool:
        """
        User-defined.
        Input is metrics instance with user-defined Metric subclass schema.
        Returns a True/False go/no-go condition to next stage.
        """
        return NotImplementedError


class PolicyGraph(abc.AindBehaviorModel):
    """
    Graph of Polices.
    Nodes are Polices and directed edges are PolicyTransitions.
    Each Policy holds a reference to a list of PolicyTransitions
    ordered in transition priority.
    """
    graph: dict[Policy, list[tuple[PolicyTransition, Policy]]]


class Stage(abc.AindBehaviorModel):
    """
    Instance of a Task.
    Task Parameters may change according to rules defined in PolicyGraph.
    Stage manages a PolicyGraph instance with a read/write API.
    """

    name: str = Field(..., description='Stage name.')
    task: abc.Task = Field(..., description='Task in which this stage is based off of.')
    graph: PolicyGraph = defaultdict(list)

    def __hash__(self) -> str:
        """
        Custom Hash Function so that Stages
        can be keys inside of a StageGraph.
        """
        return self.name + '.' + self.task.name


    def add_policy_transition(self,
                       start_policy: Policy,
                       dest_policy: Policy,
                       rule: PolicyTransition
                       ) -> None:
        """
        Add transition to policy graph.
        NOTE: The order in which this method
        is called is the order of transition priority.
        """

        self.graph[start_policy].append((rule, dest_policy))

    def remove_policy_transition(self,
                          start_policy: Policy,
                          dest_policy: Policy,
                          rule: PolicyTransition
                          ) -> None:
        """
        Remove a transition from curriculum graph.
        """
        assert start_policy in self.graph.keys(), \
            'start_policy is not in curriculum.'

        assert (rule, dest_policy) in self.graph[start_policy], \
            '(rule, dest_policy) pair is not in curriculum.'

        self.graph[start_policy].remove((rule, dest_policy))

    def see_policy_transitions(self, policy: Policy) -> list[tuple[PolicyTransition, Policy]]:
        """
        See transitions of stage in policy graph.
        """
        return self.graph[policy]

    def see_policies(self) -> list[Policy]:
        """
        See policies of policy graph.
        """
        return list(self.graph.keys())

    def get_task_parameters(self) -> abc.TaskParameters:
        """
        See current task parameters of Task.
        """
        return self.task.task_parameters

    def set_task_parameters(self,
                            task_params: abc.TaskParameters
                            ) -> None:
        """
        Set task with new set of task parameters.
        Task revalidates TaskParameters on assignment.
        """
        self.task.task_parameters = task_params

    def export_visual():
        """
        Export visual representation of graph to inspect correctness.
        """
        # TODO


class Graduated(Stage):
    """
    Optional:
    Use this Stage as the final Stage in a Curriculums's PolicyGraph.
    """
    name: str = Field("GRADUATED STAGE", description='Stage name.')
    task: abc.Task = abc.Task(name='Empty Task',
                              version='0.0.0',
                              task_parameters=abc.TaskParameters())
GRADUATED = Graduated()


class StageTransition(Rule):
    """
    User-defined function that defines
    criteria for transitioning stages based on metrics.
    """

    @abstractmethod
    def __call__(self, metrics: Metrics) -> bool:
        """
        User-defined.
        Input is metrics instance with user-defined Metric subclass schema.
        Returns a True/False go/no-go condition to next stage.
        """
        return NotImplementedError


class StageGraph(abc.AindBehaviorModel):
    """
    Graph of Stages.
    Nodes are Stages, instances of tasks.
    Directed Edges are StageTransitions.
    Each Stage holds a reference to a list of StageTransitions
    ordered in transition priority.
    """
    graph: dict[Stage, list[tuple[StageTransition, Stage]]]


class Curriculum(abc.AindBehaviorModel):
    """
    Curriculum manages a StageGraph instance with a read/write API.
    """
    graph: StageGraph = defaultdict(list)
    metrics: Metrics = Field(..., description='Reference Metrics object' + \
                             'that defines what Metrics are used in this curriculum.')

    def add_stage_transition(self,
                       start_stage: Stage,
                       dest_stage: Stage,
                       rule: StageTransition,
                       ) -> None:
        """
        Add transition to curriculum graph.
        NOTE: The order in which this method
        is called is the order of transition priority.
        """

        self.graph[start_stage].append((rule, dest_stage))

    def remove_stage_transition(self,
                          start_stage: Stage,
                          dest_stage: Stage,
                          rule: StageTransition,
                          ) -> None:
        """
        Remove a transition from curriculum graph.
        """
        assert start_stage in self.graph.keys(), \
            'start_stage is not in curriculum.'

        assert (rule, dest_stage) in self.graph[start_stage], \
            '(rule, dest_stage) pair is not in curriculum.'

        self.graph[start_stage].remove((rule, dest_stage))

    def see_stage_transitions(self, stage: Stage) -> list[tuple[StageTransition, Stage]]:
        """
        See transitions of stage in curriculum graph.
        """
        return self.graph[stage]

    def see_stages(self) -> list[Stage]:
        """
        See stages of curriculum graph.
        """
        return list(self.graph.keys())

    def export_visual():
        """
        Export visual representation of graph to inspect correctness.
        """
        # TODO
