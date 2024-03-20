"""
Core Stage and Curriculum Primitives.
"""
from __future__ import annotations
from importlib import import_module
import inspect
from typing import Any, Callable, Generic, TypeVar
import warnings

from pydantic import Field, field_validator, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

from aind_behavior_curriculum import (
    AindBehaviorModel,
    AindBehaviorModelExtra,
    Task,
    TaskParameters
)

TTask = TypeVar("TTask", bound=Task)


class Metrics(AindBehaviorModelExtra, Generic[TTask]):
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
            return obj

    @staticmethod
    def _serialize_callable(value: str | Callable) -> Callable:
        """
        Custom Serialization.
        Simlply exports reference to function as package + function name.
        """
        if isinstance(value, str):
            value = Rule._deserialize_callable(value)

        return value.__module__ + "." + value.__name__


class Policy(AindBehaviorModel, Generic[TTask]):
    """
    User-defined function that defines
    how current Task parameters change according to metrics.
    """
    rule: Rule = Field(..., description="Callable with Serialization.")

    @field_validator('rule')
    @classmethod
    def validate_rule(cls, r: Rule):
        """
        Policy Signature:
        I:
        - metrics: Metrics object
        - task_parameters: TaskParameters object

        O:
        - result: TaskParameters object
        """
        if not callable(r):
            raise ValueError('Rule must be callable.')

        # Check rule follows Transition signature
        params = list(inspect.signature(r).parameters)
        param_1 = inspect.signature(r).parameters[params[0]].annotation
        param_2 = inspect.signature(r).parameters[params[1]].annotation
        return_type = inspect.signature(r).return_annotation

        module = import_module(param_1.__module__)
        param_1_obj = getattr(module, param_1.__name__)
        module = import_module(param_2.__module__)
        param_2_obj = getattr(module, param_2.__name__)
        module = import_module(return_type.__module__)
        return_type_obj = getattr(module, return_type.__name__)

        incorrect_num_params = (len(inspect.signature(r).parameters) != 2)
        incorrect_input_types = not (issubclass(param_1_obj, Metrics) and
                                     issubclass(param_2_obj, TaskParameters))
        incorrect_return_type = not (issubclass(return_type_obj, TaskParameters))

        if (incorrect_num_params or
            incorrect_input_types or
            incorrect_return_type):
            raise ValueError('Invalid signature.' \
                             f'{Policy.validate_rule.__doc__}')

        return r


class PolicyTransition(AindBehaviorModel, Generic[TTask]):
    """
    User-defined function that defines
    criteria for transitioning between policies based on metrics.
    """
    rule: Rule = Field(..., description="Callable with Serialization.")

    @field_validator('rule')
    @classmethod
    def validate_rule(cls, r: Rule):
        """
        Policy Transition Signature:
        I:
        - metrics: Metrics object

        O:
        - result: bool
        """
        if not callable(r):
            raise ValueError('Rule must be callable.')

        # Check rule follows Transition signature
        params = list(inspect.signature(r).parameters)
        param_1 = inspect.signature(r).parameters[params[0]].annotation
        return_type = inspect.signature(r).return_annotation

        module = import_module(param_1.__module__)
        param_1_obj = getattr(module, param_1.__name__)
        module = import_module(return_type.__module__)
        return_type_obj = getattr(module, return_type.__name__)

        incorrect_num_params = (len(inspect.signature(r).parameters) != 1)
        incorrect_input_types = not (issubclass(param_1_obj, Metrics))
        incorrect_return_type = not (issubclass(return_type_obj, bool))

        if (incorrect_num_params or
            incorrect_input_types or
            incorrect_return_type):
            raise ValueError('Invalid signature.' \
                             f'{PolicyTransition.validate_rule.__doc__}')

        return r


class Stage(AindBehaviorModel, Generic[TTask]):
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

    def _create_policy_id(self) -> int:
        """
        Helper method for add_node and add_transition.
        More readable than using hash(Policy).
        """
        new_id = 0
        if len(self.policies) > 0:
            new_id = max(len(self.policies), max(self.policies.keys()) + 1)
        return new_id

    def add_policy(self, policy: Policy[TTask]) -> None:
        """
        Adds a floating policy to the Stage adjacency graph.
        """

        if policy in self.policies.values():
            warnings.warn(f'Policy {policy} has already been added to this Stage.' \
                            'Stages cannot have duplicate policies.')
        else:
            p_id = self._create_policy_id()
            self.policies[p_id] = policy

    def remove_policy(self, policy: Policy[TTask]) -> None:
        """
        Removes policy and all associated incoming/outgoing
        transition rules from the stage graph.
        NOTE: Removed nodes and transitions have the side effect
        of changing transition priority.
        """
        assert (policy in self.policies.values()), \
            f'Policy {policy} is not in the stage graph to be removed.'

        # Resolve policy id
        p_id = self._get_policy_id(policy)

        # Remove policy from policy list
        del self.policies[p_id]

        # Remove policy from stage graph
        for start_id in self.graph:
            if start_id == p_id:
                # Remove outgoing transitions
                del self.graph[p_id]
                continue

            for (rule, dest_id) in self.graph[start_id]:
                if dest_id == p_id:
                    # Remove incoming transitions
                    self.graph[start_id].remove((rule, dest_id))

    def add_policy_transition(
        self,
        start_policy: Policy[TTask],
        dest_policy: Policy[TTask],
        rule: PolicyTransition[TTask]
    ) -> None:
        """
        Add policy transition between two policies:
        Policy_A -> Policy_B.

        If Policy_A has been added to stage before, this method starts a transition
            from the exisiting Policy_A.
        If Policy_B has been added to stage before, this method creates a transition
            into the existing Policy_B.

        NOTE: The order in which this method
        is called sets the order of transition priority.
        """

        # Resolve id of start_policy
        if not (start_policy in self.policies.values()):
            new_id = self._create_policy_id()
            self.policies[new_id] = start_policy
        start_id = self._get_policy_id(start_policy)

        # Resolve id of dest_policy
        if not (dest_policy in self.policies.values()):
            new_id = self._create_policy_id()
            self.policies[new_id] = dest_policy
        dest_id = self._get_policy_id(dest_policy)

        # Add the new transition to the stage graph
        if not (start_id in self.graph):
            self.graph[start_id] = []
        self.graph[start_id].append((rule, dest_id))

    def remove_policy_transition(
        self,
        start_policy: Policy[TTask],
        dest_policy: Policy[TTask],
        rule: PolicyTransition[TTask],
        remove_start_policy: bool = False,
        remove_dest_policy: bool = False
    ) -> None:
        """
        Removes transition with options to remove start/end policies
        associated with the transition.
        NOTE: Removed nodes and transitions has the side effect
        of changing transition priority.

        """

        assert (start_policy in self.policies.values()), \
            f'Policy {start_policy} is not in the stage graph to be removed.'

        assert (dest_policy in self.policies.values()), \
            f'Policy {dest_policy} is not in the stage graph to be removed.'

        start_id = self._get_policy_id(start_policy)
        dest_id = self._get_policy_id(dest_policy)
        assert (rule, dest_id) in self.graph[start_id], \
            f'Policy {start_policy} does not transition' + \
            f'into Policy {dest_policy} with Rule {rule}.'

        # Optionally remove nodes
        if remove_start_policy:
            self.remove_policy(start_policy)
        if remove_dest_policy:
            self.remove_policy(dest_policy)

        # Remove transition
        self.graph[start_id].remove((rule, dest_id))

    def see_policy_transitions(
        self, policy: Policy[TTask]
    ) -> list[tuple[PolicyTransition[TTask], Policy[TTask]]]:
        """
        See transitions of stage in policy graph.
        """

        assert (
            policy in self.policies.values()
        ), f"Policy {policy} is not in curriculum."
        policy_id = self._get_policy_id(policy)

        return self.graph[policy_id]

    def see_policies(self) -> list[Policy[TTask]]:
        """
        See policies of policy graph.
        """
        return list(self.policies.values())

    def get_task_parameters(self) -> TaskParameters[TTask]:
        """
        See current task parameters of Task.
        """
        return self.task.task_parameters

    def set_task_parameters(self, task_params: TaskParameters[TTask]) -> None:
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


class StageTransition(AindBehaviorModel, Generic[TTask]):
    """
    User-defined function that defines
    criteria for transitioning stages based on metrics.
    """
    rule: Rule = Field(..., description="Callable with Serialization.")

    @field_validator('rule')
    @classmethod
    def validate_rule(cls, r: Rule):
        """
        Stage Transition Signature:
        I:
        - metrics: Metrics object

        O:
        - result: bool
        """
        if not callable(r):
            raise ValueError('Rule must be callable.')

        # Check rule follows Transition signature
        params = list(inspect.signature(r).parameters)
        param_1 = inspect.signature(r).parameters[params[0]].annotation
        return_type = inspect.signature(r).return_annotation

        module = import_module(param_1.__module__)
        param_1_obj = getattr(module, param_1.__name__)
        module = import_module(return_type.__module__)
        return_type_obj = getattr(module, return_type.__name__)

        incorrect_num_params = (len(inspect.signature(r).parameters) != 1)
        incorrect_input_types = not (issubclass(param_1_obj, Metrics))
        incorrect_return_type = not (issubclass(return_type_obj, bool))

        if (incorrect_num_params or
            incorrect_input_types or
            incorrect_return_type):
            raise ValueError('Invalid signature.' \
                             f'{StageTransition.validate_rule.__doc__}')
        return r


class Curriculum(AindBehaviorModel):
    """
    Curriculum manages a StageGraph instance with a read/write API.
    To use, subclass this and add subclass metrics.
    """

    pkg_location: str = ""
    name: str = Field(..., description="Curriculum name")

    stages: dict[int, Stage] = {}
    graph: dict[int, list[tuple[StageTransition, int]]] = {}

    def model_post_init(self, __context: Any) -> None:
        """
        Add Curriculum pkg location
        """
        super().model_post_init(__context)
        self.pkg_location = self.__module__ + "." + type(self).__name__

    def _get_stage_id(self, s: Stage) -> int:
        """
        Dictionaries are ordered for Python 3.7+ so this is safe.
        This library requires Python 3.8+.
        """
        dict_keys = list(self.stages.keys())
        dict_values = list(self.stages.values())

        i = dict_values.index(s)
        return dict_keys[i]

    def _create_stage_id(self) -> int:
        """
        Helper method. More readable than using hash(Stage).
        """
        new_id = 0
        if len(self.stages) > 0:
            new_id = max(len(self.stages), max(self.stages.keys()) + 1)
        return new_id

    def add_stage(self, stage: Stage) -> None:
        """
        Adds a floating stage to the Curriculum adjacency graph.
        """

        if stage in self.stages.values():
            warnings.warn(f'Stage {stage} has already been added to this Curriculum.' \
                            'A Curriculum cannot have duplicate stages.')
        else:
            p_id = self._create_stage_id()
            self.stages[p_id] = stage

    def remove_stage(self, stage: Stage) -> None:
        """
        Removes stage and all associated incoming/outgoing
        transition rules from the curriculum graph.
        NOTE: Removed nodes and transitions have the side effect
        of changing transition priority.
        """

        assert (stage in self.stages.values()), \
            f'Stage {stage} is not in the stage graph to be removed.'

        # Resolve policy id
        p_id = self._get_stage_id(stage)

        # Remove policy from policy list
        del self.stages[p_id]

        # Remove policy from stage graph
        for start_id in self.graph:
            if start_id == p_id:
                # Remove outgoing transitions
                del self.graph[p_id]
                continue

            for (rule, dest_id) in self.graph[start_id]:
                if dest_id == p_id:
                    # Remove incoming transitions
                    self.graph[start_id].remove((rule, dest_id))

    def add_stage_transition(
        self,
        start_stage: Stage,
        dest_stage: Stage,
        rule: StageTransition,
    ) -> None:
        """
        Add stage transition between two stages:
        Stage_A -> Stage_B.

        If Stage_A has been added to stage before, this method starts a transition
            from the exisiting Stage_A.
        If Stage_B has been added to stage before, this method creates a transition
            into the existing Stage_B.

        NOTE: The order in which this method
        is called sets the order of transition priority.
        """

        # Resolve id of start_stage
        if not (start_stage in self.stages.values()):
            new_id = self._create_stage_id()
            self.stages[new_id] = start_stage
        start_id = self._get_stage_id(start_stage)

        # Resolve id of dest_stage
        if not (dest_stage in self.stages.values()):
            new_id = self._create_stage_id()
            self.stages[new_id] = dest_stage
        dest_id = self._get_stage_id(dest_stage)

        # Add the new transition to the stage graph
        if not (start_id in self.graph):
            self.graph[start_id] = []
        self.graph[start_id].append((rule, dest_id))

    def remove_stage_transition(
        self,
        start_stage: Policy[TTask],
        dest_stage: Policy[TTask],
        rule: PolicyTransition[TTask],
        remove_start_stage: bool = False,
        remove_dest_stage: bool = False
    ) -> None:
        """
        Removes transition with options to remove start/end stages
        associated with the transition.
        NOTE: Removed nodes and transitions has the side effect
        of changing transition priority.
        """

        assert (start_stage in self.stages.values()), \
            f'Stage {start_stage} is not in the stage graph to be removed.'

        assert (dest_stage in self.stages.values()), \
            f'Policy {dest_stage} is not in the stage graph to be removed.'

        start_id = self._get_stage_id(start_stage)
        dest_id = self._get_stage_id(dest_stage)
        assert (rule, dest_id) in self.graph[start_id], \
            f'Stage {start_stage} does not transition' + \
            f'into Stage {dest_stage} with Rule {rule}.'

        # Optionally remove nodes
        if remove_start_stage:
            self.remove_stage(start_stage)
        if remove_dest_stage:
            self.remove_stage(dest_stage)

        # Remove transition
        self.graph[start_id].remove((rule, dest_id))

    def see_stage_transitions(
        self, stage: Stage
    ) -> list[tuple[StageTransition, Stage]]:
        """
        See transitions of stage in curriculum graph.
        """
        assert (
            stage in self.stages.values()
        ), f"Stage {stage} is not in curriculum."
        stage_id = self._get_stage_id(stage)

        return self.graph[stage_id]

    def see_stages(self) -> list[Stage]:
        """
        See stages of curriculum graph.
        """
        return list(self.stages.values())

    def export_visual():
        """
        Export visual representation of graph to inspect correctness.
        """
        # TODO
