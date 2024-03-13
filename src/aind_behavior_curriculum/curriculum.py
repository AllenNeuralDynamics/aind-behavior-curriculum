"""
Stage-based implementation
"""

from abc import abstractmethod
from importlib import import_module
from typing import Any, Callable, Generic, TypeVar, overload, Optional

from pydantic import Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

import aind_behavior_curriculum as abc
from aind_behavior_curriculum import Task


TTask = TypeVar("TTask", bound=Task)


class Metrics(abc.AindBehaviorModelExtra, Generic[TTask]):
    """
    Abstract Metrics class.
    Subclass with Metric values.
    """


class Rule:
    """
    Custom Pydantic Type that defines de/serialiation for Callables.
    """

    def __eq__(self, __value: object) -> bool:
        """
        Custom equality method.
        Two instances of the same subclass type are considered equal.
        """
        return isinstance(__value, self.__class__)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        """
        Custom validation, Ref:
        https://docs.pydantic.dev/latest/concepts/types/#handling-third-party-types
        """

        def validate_from_str(value: str) -> Callable:
            """Pass string through deserialization."""
            return cls._deserialize_callable(value)

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(
                    validate_from_str
                ),
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
            serialization=core_schema.plain_serializer_function_ser_schema(
                function=cls._serialize_callable
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
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
            assert (
                len(split) > 0
            ), f"Invalid rule value while attempting to deserialize callable. \
                Got {value}, expected string in the format '<module>.Rule'"

            module = import_module(split[0])
            obj = getattr(module, split[1])
            return obj()

    @staticmethod
    def _serialize_callable(value: str | Callable) -> Callable:
        """
        Custom Serialization.
        Simlply exports reference to function as package + function name.
        """
        if isinstance(value, str):
            value = Rule._deserialize_callable(value)
        return value.__module__ + "." + type(value).__name__


class Policy(Rule, Generic[TTask]):
    """
    User-defined function that defines
    how current Task parameters change according to metrics.
    """
    
    @abstractmethod
    def __call__(
        self, metrics: Metrics[TTask], task_params: abc.TaskParameters[TTask]
    ) -> abc.TaskParameters[TTask]:
        """
        User-defined.
        Input is metrics instance with user-defined Metric subclass schema
        and Task instance managed by the current Stage.

        Returns set of updated TaskParameters.
        """
        return NotImplementedError


class InitalizeStage(Policy[TTask]):
    """
    First Policy in a Stage's Policy Graph.
    """

    @overload
    def __call__(
        self,
        task_params: abc.TaskParameters[TTask],
        metrics: Metrics[TTask],
    ) -> abc.TaskParameters[TTask]: ...

    @overload
    def __call__(
        self, task_params: abc.TaskParameters[TTask]
    ) -> abc.TaskParameters[TTask]: ...

    def __call__(
        self,
        task_params: abc.TaskParameters[TTask],
        metrics: Optional[Metrics[TTask]] = None,
    ) -> abc.TaskParameters[TTask]:
        """
        Trivially pass the default
        """
        return task_params


INIT_STAGE = InitalizeStage()


class PolicyTransition(Rule, Generic[TTask]):
    """
    User-defined function that defines
    criteria for transitioning between policies based on metrics.
    """

    @abstractmethod
    def __call__(self, metrics: Metrics[TTask]) -> bool:
        """
        User-defined.
        Input is metrics instance with user-defined Metric subclass schema.
        Returns a True/False go/no-go condition to next stage.
        """
        return NotImplementedError


class Stage(abc.AindBehaviorModel, Generic[TTask]):
    """
    Instance of a Task.
    Task Parameters may change according to rules defined in PolicyGraph.
    Stage manages a PolicyGraph instance with a read/write API.
    """

    name: str = Field(..., description="Stage name.")
    task: TTask = Field(
        ..., description="Task in which this stage is based off of."
    )

    policies: dict[int, Policy[TTask]] = {}
    graph: dict[int, list[tuple[PolicyTransition[TTask], int]]] = {}

    def _get_policy_id(self, p: Policy[TTask]) -> int:
        """
        Dictionaries are ordered for Python 3.7+ so this is safe.
        This library requires Python 3.8+.
        """
        dict_keys = list(self.policies.keys())
        dict_values = list(self.policies.values())

        i = dict_values.index(p)
        return dict_keys[i]

    @overload
    def add_policy_transition(self, start_policy: Policy[TTask], dest_policy: Policy[TTask], rule: PolicyTransition[TTask]) -> None: ...


    @overload
    def add_policy_transition(self, start_policy: Policy[TTask]) -> None: ...
    # TODO Ensure this overload is handled correctly for floating policies

    def add_policy_transition(
        self, start_policy: Policy[TTask], dest_policy: Optional[Policy[TTask]]=None, rule: Optional[PolicyTransition[TTask]]=None
    ) -> None:
        """
        Add transition to policy graph.
        NOTE: The order in which this method
        is called is the order of transition priority.
        """

        def _create_policy_id() -> int:
            """
            Helper method. More readable than using hash(Policy).
            """
            new_id = 0
            if len(self.policies) > 0:
                new_id = max(len(self.policies), max(self.policies.keys()) + 1)
            return new_id

        if not (start_policy in self.policies.values()):
            new_id = _create_policy_id()
            self.policies[new_id] = start_policy
        start_id = self._get_policy_id(start_policy)

        if not (dest_policy in self.policies.values()):
            new_id = _create_policy_id()
            self.policies[new_id] = dest_policy
        dest_id = self._get_policy_id(dest_policy)

        if not (start_id in self.graph):
            self.graph[start_id] = []
        self.graph[start_id].append((rule, dest_id))

    def remove_policy_transition(
        self, start_policy: Policy[TTask], dest_policy: Policy[TTask], rule: PolicyTransition[TTask]
    ) -> None:
        # TODO I think you will need a method to just remove a float policy too
        """
        Remove a transition from curriculum graph.
        Destination policies with no transitions to them are
        also removed from the managed Stage.policies record.
        NOTE: Potentially changes the order of transition priority.
        """
        assert (
            start_policy in self.policies.values()
        ), "start_policy is not in stage."

        start_id = self._get_policy_id(start_policy)
        dest_id = self._get_policy_id(dest_policy)
        assert (rule, dest_id) in self.graph[
            start_id
        ], "(rule, dest_policy) pair is not in stage."

        # Remove the policy transition
        self.graph[start_id].remove((rule, dest_id))

        # Final cleanup:
        # Check if removed dest_id exists anywhere in the graph values
        # and remove dest_id from policies if this is not the case.
        collapsed_values = [
            item[1] for sublist in self.graph.values() for item in sublist
        ]
        if not (dest_id in collapsed_values):
            self.policies.pop(dest_id)

    def see_policy_transitions(
        self, policy: Policy[TTask]
    ) -> list[tuple[PolicyTransition[TTask], Policy[TTask]]]:
        """
        See transitions of stage in policy graph.
        """

        assert (
            policy in self.policies.values()
        ), f"policy {policy} is not in curriculum."
        policy_id = self._get_policy_id(policy)

        return self.graph[policy_id]

    def see_policies(self) -> list[Policy[TTask]]:
        """
        See policies of policy graph.
        """
        return list(self.policies.values())

    def get_task_parameters(self) -> abc.TaskParameters[TTask]:
        """
        See current task parameters of Task.
        """
        return self.task.task_parameters

    def set_task_parameters(self, task_params: abc.TaskParameters[TTask]) -> None:
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

    name: str = Field("GRADUATED STAGE", description="Stage name.")
    task: abc.Task = abc.Task(
        name="Empty Task",
        version="0.0.0",
        task_parameters=abc.TaskParameters(),
    )

    def model_post_init(self, __context: Any) -> None:
        self.add_policy_transition(INIT_STAGE)  # Floating stage


GRADUATED = Graduated()


class StageTransition(Rule, Generic[TTask]):
    """
    User-defined function that defines
    criteria for transitioning stages based on metrics.
    """

    @abstractmethod
    def __call__(self, task_parameters: abc.TaskParameters[TTask], metrics: Metrics[TTask]) -> bool:
        """
        User-defined.
        Input is metrics instance with user-defined Metric subclass schema.
        Returns a True/False go/no-go condition to next stage.
        """
        return NotImplementedError

InboundStage = TypeVar("InboundStage", bound='Stage')
OutboundStage = TypeVar("OutboundStage", bound='Stage')

class Curriculum(abc.AindBehaviorModel):
    """
    Curriculum manages a StageGraph instance with a read/write API.
    To use, subclass this and add subclass metrics.
    """

    pkg_location: str = ""
    name: str = Field(..., description="Curriculum name")

    stages: dict[int, InboundStage] = {}
    graph: dict[int, list[tuple[StageTransition, int]]] = {}

    def model_post_init(self, __context: Any) -> None:
        """
        Add Curriculum pkg location
        """
        super().model_post_init(__context)
        self.pkg_location = self.__module__ + "." + type(self).__name__

    def _get_stage_id(self, s: InboundStage) -> int:
        """
        Dictionaries are ordered for Python 3.7+ so this is safe.
        This library requires Python 3.8+.
        """
        dict_keys = list(self.stages.keys())
        dict_values = list(self.stages.values())

        i = dict_values.index(s)
        return dict_keys[i]

    def add_stage_transition(
        self,
        start_stage: InboundStage,
        dest_stage: OutboundStage,
        rule: StageTransition,
    ) -> None:
        """
        Add transition to curriculum graph.
        NOTE: The order in which this method
        is called is the order of transition priority.
        """

        def _create_stage_id() -> int:
            """
            Helper method. More readable than using hash(Stage).
            """
            new_id = 0
            if len(self.stages) > 0:
                new_id = max(len(self.stages), max(self.stages.keys()) + 1)
            return new_id

        if not (start_stage in self.stages.values()):
            new_id = _create_stage_id()
            self.stages[new_id] = start_stage
        start_id = self._get_stage_id(start_stage)

        if not (dest_stage in self.stages.values()):
            new_id = _create_stage_id()
            self.stages[new_id] = dest_stage
        dest_id = self._get_stage_id(dest_stage)

        if not (start_id in self.graph):
            self.graph[start_id] = []
        self.graph[start_id].append((rule, dest_id))

    def remove_stage_transition(
        self,
        start_stage: InboundStage,
        dest_stage: OutboundStage,
        rule: StageTransition,
    ) -> None:
        """
        Remove a transition from curriculum graph.
        Destination stages with no transitions to them are
        also removed from the managed curriculum.stages record.
        NOTE: Potentially changes the order of transition priority.
        """

        assert (
            start_stage in self.stages.values()
        ), "start_stage is not in curriculum."

        start_id = self._get_stage_id(start_stage)
        dest_id = self._get_stage_id(dest_stage)
        assert (rule, dest_id) in self.graph[
            start_id
        ], "(rule, dest_stage) pair is not in curriculum."

        # Remove the policy transition
        self.graph[start_id].remove((rule, dest_id))

        # Final cleanup:
        # Check if removed dest_id exists anywhere in the graph values
        # and remove dest_id from policies if this is not the case.
        collapsed_values = [
            item[1] for sublist in self.graph.values() for item in sublist
        ]
        if not (dest_id in collapsed_values):
            self.stages.pop(dest_id)

    def see_stage_transitions(
        self, stage: InboundStage
    ) -> list[tuple[StageTransition, OutboundStage]]:
        """
        See transitions of stage in curriculum graph.
        """
        assert (
            stage in self.stages.values()
        ), f"Stage {stage} is not in curriculum."
        stage_id = self._get_stage_id(stage)

        return self.graph[stage_id]

    def see_stages(self) -> list[InboundStage]:
        """
        See stages of curriculum graph.
        """
        return list(self.stages.values())

    def export_visual():
        """
        Export visual representation of graph to inspect correctness.
        """
        # TODO
