"""
Core Stage and Curriculum Primitives.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import warnings
from importlib import import_module
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
)

import boto3
from jinja2 import Template
from pydantic import (
    BaseModel,
    Discriminator,
    Field,
    GetJsonSchemaHandler,
    Tag,
    ValidationError,
    create_model,
    field_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

from aind_behavior_curriculum.base import (
    AindBehaviorModel,
    AindBehaviorModelExtra,
)
from aind_behavior_curriculum.task import SEMVER_REGEX, Task, TaskParameters

TTask = TypeVar("TTask", bound=Task)


class Metrics(AindBehaviorModelExtra):
    """
    Abstract Metrics class.
    Subclass with Metric values.
    """


class Rule:
    """
    Custom Pydantic Type that defines de/serialization for Callables.
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
            if not (len(split) > 0):
                raise ValueError(
                    f"Invalid rule value while attempting to deserialize callable. \
                    Got {value}, expected string in the format '<module>.Rule'"
                )

            module = import_module(split[0])
            obj = getattr(module, split[1])
            return obj

    @staticmethod
    def _serialize_callable(value: str | Callable) -> str:
        """
        Custom Serialization.
        Simply exports reference to function as package + function name.
        """
        if isinstance(value, str):
            value = Rule._deserialize_callable(value)

        return value.__module__ + "." + value.__name__


class Policy(AindBehaviorModel):
    """
    User-defined function that defines
    how current Task parameters change according to metrics.
    """

    rule: Rule = Field(..., description="Callable with Serialization.")

    @field_validator("rule")
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
            raise ValueError("Rule must be callable.")

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

        incorrect_num_params = len(inspect.signature(r).parameters) != 2
        incorrect_input_types = not (
            issubclass(param_1_obj, Metrics)
            and issubclass(param_2_obj, TaskParameters)
        )
        incorrect_return_type = not (
            issubclass(return_type_obj, TaskParameters)
        )

        if (
            incorrect_num_params
            or incorrect_input_types
            or incorrect_return_type
        ):
            raise ValueError(
                "Invalid signature." f"{Policy.validate_rule.__doc__}"
            )

        return r


class PolicyTransition(AindBehaviorModel):
    """
    User-defined function that defines
    criteria for transitioning between policies based on metrics.
    """

    rule: Rule = Field(..., description="Callable with Serialization.")

    @field_validator("rule")
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
            raise ValueError("Rule must be callable.")

        # Check rule follows Transition signature
        params = list(inspect.signature(r).parameters)
        param_1 = inspect.signature(r).parameters[params[0]].annotation
        return_type = inspect.signature(r).return_annotation

        module = import_module(param_1.__module__)
        param_1_obj = getattr(module, param_1.__name__)
        module = import_module(return_type.__module__)
        return_type_obj = getattr(module, return_type.__name__)

        incorrect_num_params = len(inspect.signature(r).parameters) != 1
        incorrect_input_types = not (issubclass(param_1_obj, Metrics))
        incorrect_return_type = not (issubclass(return_type_obj, bool))

        if (
            incorrect_num_params
            or incorrect_input_types
            or incorrect_return_type
        ):
            raise ValueError(
                "Invalid signature."
                f"{PolicyTransition.validate_rule.__doc__}"
            )

        return r


NodeTypes = TypeVar("NodeTypes")
EdgeType = TypeVar("EdgeType")


class BehaviorGraph(AindBehaviorModel, Generic[NodeTypes, EdgeType]):
    """
    Core directed graph data structure used in Stage and Curriculum.
    """

    nodes: Dict[int, NodeTypes] = Field(default={}, validate_default=True)
    graph: Dict[int, List[Tuple[EdgeType, int]]] = Field(
        default={}, validate_default=True
    )

    def _get_node_id(self, node: NodeTypes) -> int:
        """
        Dictionaries are ordered for Python 3.7+ so this is safe.
        This library requires Python 3.8+.
        """
        dict_keys = list(self.nodes.keys())
        dict_values = list(self.nodes.values())

        i = dict_values.index(node)
        return dict_keys[i]

    def _create_node_id(self) -> int:
        """
        Helper method for add_node and add_transition.
        More readable than using hash(Policy).
        """
        new_id = 0
        if len(self.nodes) > 0:
            new_id = max(len(self.nodes), max(self.nodes.keys()) + 1)
        return new_id

    def add_node(self, node: NodeTypes) -> None:
        """
        Adds a floating node to the behavior graph.
        """
        p_id = self._create_node_id()
        self.nodes[p_id] = node
        self.graph[p_id] = []

    def remove_node(self, node: NodeTypes) -> None:
        """
        Removes node and all associated incoming/outgoing
        transition rules from the stage graph.
        NOTE: Removed nodes and transitions have the side effect
        of changing transition priority.
        """
        if not (node in self.nodes.values()):
            raise ValueError(f"Node {node} is not in the graph to be removed.")

        # Resolve node id
        p_id = self._get_node_id(node)

        # Remove node from node list
        del self.nodes[p_id]

        # Remove node from graph keys
        del self.graph[p_id]

        # Remove node from graph value lists
        for start_id in self.graph:
            for rule, dest_id in self.graph[start_id]:
                if dest_id == p_id:
                    self.graph[start_id].remove((rule, dest_id))

    def add_transition(
        self,
        start_node: NodeTypes,
        dest_node: NodeTypes,
        rule: EdgeType,
    ) -> None:
        """
        Add transition between two nodes:
        start_node -> dest_node.

        If start_node has been added to graph before, this method starts a transition
            from the existing start_node.
        If dest_node has been added to graph before, this method creates a transition
            into the existing dest_node.

        NOTE: The order in which this method
        is called sets the order of transition priority.
        """

        # Resolve id of start_node
        if not (start_node in self.nodes.values()):
            new_id = self._create_node_id()
            self.nodes[new_id] = start_node
            self.graph[new_id] = []
        start_id = self._get_node_id(start_node)

        # Resolve id of dest_node
        if not (dest_node in self.nodes.values()):
            new_id = self._create_node_id()
            self.nodes[new_id] = dest_node
            self.graph[new_id] = []
        dest_id = self._get_node_id(dest_node)

        # Add the new transition to the graph
        self.graph[start_id].append((rule, dest_id))

    def remove_node_transition(
        self,
        start_node: NodeTypes,
        dest_node: NodeTypes,
        rule: EdgeType,
        remove_start_node: bool = False,
        remove_dest_node: bool = False,
    ) -> None:
        """
        Removes transition with options to remove start/end nodes
        associated with the transition.
        NOTE: Removed nodes and transitions has the side effect
        of changing transition priority.
        """

        if not (start_node in self.nodes.values()):
            raise ValueError(
                f"Node {start_node} is not in the behavior graph to be removed."
            )

        if not (dest_node in self.nodes.values()):
            raise ValueError(
                f"Node {dest_node} is not in the behavior graph to be removed."
            )

        start_id = self._get_node_id(start_node)
        dest_id = self._get_node_id(dest_node)
        if not ((rule, dest_id) in self.graph[start_id]):
            raise ValueError(
                f"Node {start_node} does not transition into Node {dest_node} with Rule {rule}."
            )

        # Optionally remove nodes
        if remove_start_node:
            self.remove_node(start_node)
        if remove_dest_node:
            self.remove_node(dest_node)

        # Remove transition
        self.graph[start_id].remove((rule, dest_id))

    def see_nodes(self) -> List[NodeTypes]:
        """
        See nodes of behavior graph.
        """
        return list(self.nodes.values())

    def see_node_transitions(
        self, node: NodeTypes
    ) -> List[Tuple[EdgeType, NodeTypes]]:
        """
        See transitions of node in behavior graph.
        """

        if not (node in self.nodes.values()):
            raise ValueError(f"Node {node} is not in the behavior graph.")

        node_id = self._get_node_id(node)
        node_list = self.graph[node_id]
        node_list = [(rule, self.nodes[p_id]) for (rule, p_id) in node_list]

        return node_list

    def set_transition_priority(
        self,
        node: NodeTypes,
        node_transitions: List[Tuple[EdgeType, NodeTypes]],
    ) -> None:
        """
        Change order of node transitions listed under a node.
        Highest priority is ordered in node_transition from left -> right.
        """

        input_transitions = []
        for rule, n in node_transitions:
            if not (n in self.nodes.values()):
                raise ValueError(
                    f"Node {n} is not a node inside the behavior graph."
                )
            input_transitions.append((rule, self._get_node_id(n)))

        n_id = self._get_node_id(node)
        self.graph[n_id] = input_transitions

    def __eq__(self, other: object) -> bool:
        """
        Compare this object with another for equality.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        if not isinstance(other, type(self)):
            return False
        return self.model_dump() == other.model_dump()


class PolicyGraph(BehaviorGraph[Policy, PolicyTransition]):
    """
    Graph for Stage.
    """

    pass


class Stage(AindBehaviorModel, Generic[TTask]):
    """
    Instance of a Task.
    Task Parameters may change according to rules defined in BehaviorGraph.
    Stage manages a BehaviorGraph instance with a read/write API.
    """

    name: str = Field(..., description="Stage name.")
    task: TTask = Field(
        ..., description="Task in which this stage is based off of."
    )
    graph: PolicyGraph = PolicyGraph()
    start_policies: List[Policy] = []

    def __eq__(self, __value: object) -> bool:
        """
        Custom equality method.
        Two Stage instances are only distinguished by name.
        """
        return self.name == __value.name

    def add_policy(self, policy: Policy) -> None:
        """
        Adds a floating policy to the Stage adjacency graph.
        """
        if policy in self.graph.see_nodes():
            raise ValueError(
                f"Policy {policy.rule.__name__} is a duplicate Policy in Stage {self.name}."
            )

        self.graph.add_node(policy)

    def remove_policy(self, policy: Policy) -> None:
        """
        Removes policy and all associated incoming/outgoing
        transition rules from the stage graph.
        NOTE: Removed nodes and transitions have the side effect
        of changing transition priority.
        """
        self.graph.remove_node(policy)

        # Also remove reference to policy in start_policies if applicable.
        if policy in self.start_policies:
            self.start_policies.remove(policy)

            if len(self.start_policies) == 0:
                warnings.warn(f"Stage {self.name}.start_policies is empty.")

    def add_policy_transition(
        self,
        start_policy: Policy,
        dest_policy: Policy,
        rule: PolicyTransition,
    ) -> None:
        """
        Add policy transition between two policies:
        Policy_A -> Policy_B.

        If Policy_A has been added to stage before, this method starts a transition
            from the existing Policy_A.
        If Policy_B has been added to stage before, this method creates a transition
            into the existing Policy_B.

        NOTE: The order in which this method
        is called sets the order of transition priority.
        """

        if isinstance(rule, Rule):
            rule = PolicyTransition(rule=rule)
        if callable(rule) and not isinstance(rule, PolicyTransition):
            rule = PolicyTransition(rule=rule)

        self.graph.add_transition(start_policy, dest_policy, rule)

    def remove_policy_transition(
        self,
        start_policy: Policy,
        dest_policy: Policy,
        rule: PolicyTransition,
        remove_start_policy: bool = False,
        remove_dest_policy: bool = False,
    ) -> None:
        """
        Removes transition with options to remove start/end policies
        associated with the transition.
        NOTE: Removed nodes and transitions has the side effect
        of changing transition priority.
        """
        self.graph.remove_node_transition(
            start_policy,
            dest_policy,
            rule,
            remove_start_policy,
            remove_dest_policy,
        )

    def see_policies(self) -> List[Policy]:
        """
        See policies of policy graph.
        """
        return self.graph.see_nodes()

    def see_policy_transitions(
        self, policy: Policy
    ) -> List[Tuple[PolicyTransition, Policy]]:
        """TTask
        See transitions of stage in policy graph.
        """
        return self.graph.see_node_transitions(policy)

    def set_policy_transition_priority(
        self,
        policy: Policy,
        policy_transitions: List[Tuple[PolicyTransition, Policy]],
    ) -> None:
        """
        Change the order of policy transitions listed under a policy.
        To use, call see_policy_transitions() and order the transitions
        in the desired priority from left -> right.
        """

        policy_transitions_list = list(
            (t.rule, p.rule) for (t, p) in policy_transitions
        )
        current_list = list(
            (t.rule, p.rule) for (t, p) in self.see_policy_transitions(policy)
        )

        if len(policy_transitions_list) != len(current_list):
            raise ValueError(
                f"Number of input node transitions {policy_transitions} does not \
                match the number of elements under this node: {self.see_policy_transitions(policy)}.\
                Please call 'see_policy_transitions()' for a precise list of elements."
            )

        self.graph.set_transition_priority(policy, policy_transitions)

    def set_start_policies(self, start_policies: Policy | List[Policy]):
        """
        Sets stage's start policies to start policies provided.
        Input overwrites existing start policies.
        """
        if isinstance(start_policies, Policy):
            start_policies = [start_policies]
        self.start_policies = start_policies

    def get_task_parameters(self) -> TaskParameters:
        """
        See current task parameters of Task.
        """
        return self.task.task_parameters

    def set_task_parameters(self, task_params: TaskParameters) -> None:
        """
        Set task with new set of task parameters.
        Task re-validates TaskParameters on assignment.
        """
        self.task.task_parameters = task_params

    def validate_stage(self) -> Stage:
        """
        Validates that the stage can be (de)serialized.
        """

        # Check round trip serialization
        try:
            instance_json = self.model_dump_json()
            self.model_validate_json(instance_json)
        except ValidationError as e:
            e.add_note(
                f"Pydantic cannot serialize Stage {self.name}, please use "
                "mypy to verify your types "
                "(check signatures of policy functions, etc.)."
            )
            raise e

        return self


class StageTransition(AindBehaviorModel):
    """
    User-defined function that defines
    criteria for transitioning stages based on metrics.
    """

    rule: Rule = Field(..., description="Callable with Serialization.")

    @field_validator("rule")
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
            raise ValueError("Rule must be callable.")

        # Check rule follows Transition signature
        params = list(inspect.signature(r).parameters)
        param_1 = inspect.signature(r).parameters[params[0]].annotation
        return_type = inspect.signature(r).return_annotation

        module = import_module(param_1.__module__)
        param_1_obj = getattr(module, param_1.__name__)
        module = import_module(return_type.__module__)
        return_type_obj = getattr(module, return_type.__name__)

        incorrect_num_params = len(inspect.signature(r).parameters) != 1
        incorrect_input_types = not (issubclass(param_1_obj, Metrics))
        incorrect_return_type = not (issubclass(return_type_obj, bool))

        if (
            incorrect_num_params
            or incorrect_input_types
            or incorrect_return_type
        ):
            raise ValueError(
                "Invalid signature." f"{StageTransition.validate_rule.__doc__}"
            )
        return r


class StageGraph(BehaviorGraph[Stage[TTask], StageTransition], Generic[TTask]):
    """
    Graph for Curriculum.
    """

    pass


class Curriculum(AindBehaviorModel):
    """
    Curriculum manages a StageGraph instance with a read/write API.
    To use, subclass this and add subclass metrics.
    """

    pkg_location: str = Field(
        # https://docs.python.org/3/faq/programming.html#why-do-lambdas-defined-in-a-loop-with-different-values-all-return-the-same-result
        default_factory=lambda: Curriculum.default_pkg_location_factory(),  # pylint: disable=unnecessary-lambda
        frozen=True,
        description="Location of the python package \
                                that instantiated the Curriculum.",
    )
    name: str = Field(
        default="Please subclass, rename, and define \
                      a StageGraph with your own Stage objs \
                      Ex: StageGraph[Union[StageA, StageB, Graduated]]",
        description="Name of the Curriculum.",
        frozen=True,
    )
    version: str = Field(
        default="0.0.0",
        pattern=SEMVER_REGEX,
        frozen=True,
        validate_default=True,
        description="Curriculum version.",
    )
    graph: Annotated[
        StageGraph, Field(default=StageGraph(), validate_default=True)
    ]

    @property
    def _known_tasks(self) -> List[Type[Task]]:
        """Get all known tasks in the curriculum."""

        # We introspect into the StageGraph[T] type to get the known tasks.
        _generic = self.model_fields["graph"].annotation
        _inner_args = _generic.__dict__["__pydantic_generic_metadata__"][
            "args"
        ][0]
        _inner_union = get_args(_inner_args)[0]
        if isinstance(_inner_union, type):
            _known_tasks = [_inner_union]
        else:
            _known_tasks = [get_args(x)[0] for x in get_args(_inner_union)]

        # Since we are here, we also check if the known tasks match the nodes in the graph
        # The tasks known to the graph type should be a super set of the known tasks in the nodes
        _known_nodes = [type(stage.task) for stage in self.graph.see_nodes()]
        if not set(_known_tasks).issuperset(set(_known_nodes)):
            raise ValueError(
                "Known tasks in the Curriculum do not match the tasks in the StageGraph. This is likely a problem with StageGraph type definition."
            )
        return _known_tasks

    def task_discriminator_type(self) -> type:
        """Create a Discriminated Union  type for the known tasks."""
        return make_task_discriminator(*self._known_tasks)

    def _is_task_type_known(self, task_type: Task | Type[Task]) -> bool:
        """Check if a task type is known in the curriculum."""
        if isinstance(task_type, Task):
            task_type = type(task_type)
        if isinstance(task_type, type):
            return task_type in self._known_tasks
        raise ValueError("task_type must be a Task instance or a Task type.")

    @classmethod
    def default_pkg_location_factory(cls) -> str:
        """
        Location of the python package that instantiated the Curriculum.
        """
        return cls.__module__ + "." + type(cls).__name__

    def add_stage(self, stage: Stage) -> None:
        """
        Adds a floating stage to the Curriculum adjacency graph.
        """

        if not self._is_task_type_known(stage.task):
            raise ValueError(
                f"Task {stage.task} is not a known task type in the Curriculum."
            )

        if stage in self.graph.see_nodes():
            raise ValueError(
                f"Stage {stage.name} is a duplicate stage in Curriculum."
            )

        self.graph.add_node(stage)

    def remove_stage(self, stage: Stage) -> None:
        """
        Removes stage and all associated incoming/outgoing
        transition rules from the curriculum graph.
        NOTE: Removed nodes and transitions have the side effect
        of changing transition priority.
        """
        self.graph.remove_node(stage)

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


        if isinstance(rule, Rule):
            rule = StageTransition(rule=rule)
        if callable(rule) and not isinstance(rule, StageTransition):
            rule = StageTransition(rule=rule)

        self.graph.add_transition(start_stage, dest_stage, rule)

    def remove_stage_transition(
        self,
        start_stage: Stage,
        dest_stage: Stage,
        rule: StageTransition,
        remove_start_stage: bool = False,
        remove_dest_stage: bool = False,
    ) -> None:
        """
        Removes transition with options to remove start/end stages
        associated with the transition.
        NOTE: Removed nodes and transitions has the side effect
        of changing transition priority.
        """
        self.graph.remove_node_transition(
            start_stage,
            dest_stage,
            rule,
            remove_start_stage,
            remove_dest_stage,
        )

    def see_stages(self) -> List[Stage]:
        """
        See stages of curriculum graph.
        """
        return self.graph.see_nodes()

    def see_stage_transitions(
        self, stage: Stage
    ) -> List[Tuple[StageTransition, Stage]]:
        """
        See transitions of stage in curriculum graph.
        """
        return self.graph.see_node_transitions(stage)

    def set_stage_transition_priority(
        self,
        stage: Stage[TTask],
        stage_transitions: List[Tuple[StageTransition, Stage]],
    ) -> None:
        """
        Change the order of stage transitions listed under a stage.
        To use, call see_stage_transitions() and order the transitions
        in the desired priority from left -> right.
        """

        stage_transitions_list = list(
            (t.rule, s.name) for (t, s) in stage_transitions
        )
        current_list = list(
            (t.rule, s.name) for (t, s) in self.see_stage_transitions(stage)
        )

        if len(stage_transitions_list) != len(current_list):
            raise ValueError(
                f"Elements of input node transitions {stage_transitions} does not \
                    match the elements under this node: {self.see_stage_transitions(stage)}. \
                        Please call 'see_stage_transitions()' for a precise list of elements."
            )

        self.graph.set_transition_priority(stage, stage_transitions)

    def validate_curriculum(self) -> Curriculum:
        """
        Validate curriculum for export/serialization.
        """

        if not all(
            [
                self._is_task_type_known(stage.task)
                for stage in self.see_stages()
            ]
        ):
            raise ValueError(
                "Not all tasks in the curriculum are known. Please add stages with known tasks."
            )

        if len(self.see_stages()) == 0:
            raise ValueError("Curriculum is empty! Please add stages.")

        for s in self.see_stages():
            s.validate_stage()

        # Check round trip serialization
        try:
            instance_json = self.model_dump_json()
            self.model_validate_json(instance_json)
        except ValidationError as e:
            e.add_note(
                (
                    "Pydantic cannot serialize Curriculum, please use "
                    "mypy to verify your types (check stage transition signature, etc.)."
                )
            )
            raise e

        return self

    def export_diagram(self, png_path: str) -> None:  # noqa: C901
        """
        Makes diagram for input Curriculum and
        writes to output png_path.
        """

        def make_stage_script(s: Stage) -> str:
            """
            Stage to dot script conversion.
            """

            template_string = """
                digraph cluster_{{ stage_id }} {
                    labelloc="t";
                    label={{ stage_name }};

                    // Define nodes with increased font visibility
                    node [shape=box, style=filled, fontname=Arial, fontsize=12,
                    fillcolor=lightblue, color=black];

                    // Define nodes
                    {% for n in nodes %}
                    {{ n }};
                    {% endfor %}

                    // Define edges
                    {% for edge in edges %}
                    {{ edge }};
                    {% endfor %}
                }
            """
            template = Template(template_string)
            stage_name = '"' + s.name + '"'

            nodes = []
            for node_id, node in s.graph.nodes.items():
                # Add color to start policies
                if node in s.start_policies:
                    node_str = (
                        f'{node_id} [label="{node.rule.__name__}",'
                        'fillcolor="#FFEA00"]'
                    )
                else:
                    node_str = f'{node_id} [label="{node.rule.__name__}"]'
                nodes.append(node_str)

            edges = []
            for start_id, edge_list in s.graph.graph.items():
                for i, (edge, dest_id) in enumerate(edge_list):
                    # Use 1-indexing for labels
                    i = i + 1

                    # Edges must be StageTransition or PolicyTransition
                    edge_str = (
                        f'{start_id} -> {dest_id} [label="({i}) '
                        f'{edge.rule.__name__}", minlen=2]'
                    )
                    edges.append(edge_str)

            stage_dot_script = template.render(
                stage_id="".join(s.name.split()),
                stage_name=stage_name,
                nodes=nodes,
                edges=edges,
            )

            return stage_dot_script

        def make_curriculum_script(c: Curriculum) -> str:
            """
            Curriculum to dot script conversion.
            """

            curr_dot_script = """
                digraph cluster_curriculum {
                    color="white";
                    label={{ curr_name }};
                    fontsize=24;

                    node [shape=box, style=filled];
                    {% for n in nodes %}
                    {{ n }}
                    {% endfor %}

                    {% for edge in edges %}
                    {{ edge }};
                    {% endfor %}
                }
            """
            template = Template(curr_dot_script)

            # Add curriculum nodes
            nodes = [
                f'{node_id} [label="{node.name}"]'
                for node_id, node in c.graph.nodes.items()
            ]

            # Add curriculum edges
            edges = []
            for start_id, edge_list in c.graph.graph.items():
                for i, (edge, dest_id) in enumerate(edge_list):
                    # Use 1-indexing for labels
                    i = i + 1

                    # Edges must be StageTransition or PolicyTransition
                    edge_str = (
                        f'{start_id} -> {dest_id} [label="({i}) '
                        f'{edge.rule.__name__}", minlen=2]'
                    )
                    edges.append(edge_str)

            curriculum_dot_script = template.render(
                curr_name='"' + c.name + '"', nodes=nodes, edges=edges
            )

            return curriculum_dot_script

        if not png_path.endswith(".png"):
            raise ValueError("Please add .png extension to end of png_path.")

        self.validate_curriculum()

        dot_scripts = [make_curriculum_script(self)]
        last = []
        for stage in self.see_stages():
            if stage.name == "GRADUATED":
                last.append(make_stage_script(stage))
                continue
            dot_scripts.append(make_stage_script(stage))
        dot_scripts = dot_scripts + last

        # Finally concatenate these strings together in this order.
        final_script = "\n".join(dot_scripts)

        # Run graphviz export
        gvpack_command = ["gvpack", "-u"]
        dot_command = ["dot", "-Tpng", "-o", png_path]
        gvpack_process = subprocess.Popen(
            gvpack_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        dot_process = subprocess.Popen(dot_command, stdin=subprocess.PIPE)

        gvpack_output, _ = gvpack_process.communicate(
            input=final_script.encode()
        )
        dot_process.communicate(input=gvpack_output)

    def export_json(self, json_path: str) -> None:
        """
        Export curriculum json to export path
        """

        if not json_path.endswith(".json"):
            raise ValueError("Please add .json extension to end of json_path.")

        self.validate_curriculum()

        with open(json_path, "w", encoding="utf-8") as f:
            json_dict = self.model_dump()
            json_string = json.dumps(json_dict, indent=4)
            f.write(json_string)

    def export_curriculum(self, export_dir: str) -> None:
        """
        Export json and diagram into export dir.
        """

        self.export_json(str(Path(export_dir) / "schema.json"))
        self.export_diagram(str(Path(export_dir) / "diagram.png"))

    @classmethod
    def download_curriculum(
        cls,
        name: str,
        version: str,
        bucket="aind-behavior-curriculum-prod-o5171v",
    ) -> Curriculum:
        """
        Reconstruct curriculum object from cloud json.
        """

        def read_json(bucket_name: str, json_key: Path | str) -> dict:
            """
            Reads a json content hosted in S3

            Parameters
            ---------------
            bucket_name: str
                Bucket name

            json_key: PathLike
                Path where the json is stored in S3

            Returns
            ---------------
            dict
                Dictionary with the json content
            """

            s3 = boto3.client("s3")
            response = s3.get_object(Bucket=bucket_name, Key=json_key)
            json_data = json.loads(response["Body"].read().decode("utf-8"))
            return json_data

        json_dict = read_json(
            bucket, str(Path("curriculums") / name / version / "schema.json")
        )  # noqa: E501
        json_string = json.dumps(json_dict)
        curr = cls.model_validate_json(json_string)

        return curr


def create_curriculum(
    name: str,
    version: str,
    *tasks: Type[Task],
    pkg_location: Optional[str] = None,
) -> Type[Curriculum]:
    """_summary_

    Args:
        name (str): Name of the Curriculum.
        version (str): Curriculum version in SemVer format.

    Returns:
        Type[Curriculum]: A curriculum class with the specified tasks.
    """
    if len(tasks) == 0:
        raise ValueError("At least one task must be provided.")

    _tasks_tagged = make_task_discriminator(*tasks)
    _props = {
        "name": Annotated[
            Literal[name],
            Field(default=name, frozen=True, validate_default=True),
        ],
        "version": Annotated[
            Literal[version],
            Field(
                default=version,
                frozen=True,
                pattern=SEMVER_REGEX,
                validate_default=True,
            ),
        ],
        "graph": Annotated[
            StageGraph[_tasks_tagged],
            Field(default_factory=StageGraph, validate_default=True),
        ],
    }

    if pkg_location is not None:
        _props["pkg_location"] = Annotated[
            str,
            Field(default=pkg_location, frozen=False, validate_default=True),
        ]

    t_curriculum = create_model(name, __base__=Curriculum, **_props)  # type: ignore

    return t_curriculum


def make_task_discriminator(*tasks: Type[Task]) -> Type:
    """
    Creates a discriminated union type for the given tasks.
    This function takes a variable number of Task types and generates a
    discriminated union type using the 'name' field of each task to create
    a valid Tag and corresponding Discriminator.
    Args:
        *tasks (Type[Task]): A variable number of Task types.
    Returns:
        Type: A discriminated union type of the provided tasks.
    Raises:
        ValueError: If a task does not have a 'name' field defined as
                    Literal[name] or with a default value.
        ValueError: If a task has a 'name' field that is not a string.
        ValueError: If duplicate task names are found.
        ValueError: If one or more task names are not found.
    """

    # https://docs.pydantic.dev/2.10/concepts/unions/#discriminated-unions-with-callable-discriminator
    tasks = tuple(set(tasks))
    _candidate_discriminators: List[str] = []
    for task in tasks:
        name: Optional[str] = None
        try:  # Use reflection to try to get the name from the type annotation, i.e. Literal[T]
            name = get_args(task.model_fields["name"].annotation)[0]
        except (
            IndexError,
            KeyError,
        ):  # If we don't find it, keep going, while throwing any other errors
            pass
        if name is None:
            try:
                name = task.model_fields["name"].default
            except KeyError as exc:
                raise ValueError(
                    f"Task {task} does not have a name field defined as "
                    f"Literal[name] or with a default value."
                ) from exc
        if isinstance(name, str):
            _candidate_discriminators.append(name)
        else:
            raise ValueError(
                f"Task {task} has a name field that is not a string, got {name} of type {type(name)}"
            )

    if len(_candidate_discriminators) != len(set(_candidate_discriminators)):
        raise ValueError("Duplicate task names found.")
    if len(_candidate_discriminators) != len(tasks):
        raise ValueError("One of more task names were not found.")

    _union = Union[  # type: ignore
        tuple(
            [
                Annotated[task, Tag(task_name)]
                for task, task_name in zip(tasks, _candidate_discriminators)
            ]
        )
    ]

    Tasks = Annotated[
        _union,  # type: ignore
        Field(
            discriminator=Discriminator(
                _get_discriminator_value,
            )
        ),
    ]
    return Tasks  # type: ignore


def _get_discriminator_value(v: Task) -> str:
    """
    Retrieves the discriminator value from the given task.
    The discriminator value is extracted from the 'name' attribute of the input,
    which can be either a dictionary or an instance of BaseModel.
    Args:
        v (Task): The task from which to extract the discriminator value. This can
                  be either a dictionary or an instance of BaseModel.
    Returns:
        str: The discriminator value extracted from the input.
    Raises:
        ValueError: If the discriminator field is not found, is null, or is not of
                    string type.
    """

    _discriminator: Any = None
    if isinstance(v, dict):
        _discriminator = v.get("name", None)
    if isinstance(v, BaseModel):
        _discriminator = getattr(v, "name", None)
    if isinstance(_discriminator, str):
        return _discriminator
    raise ValueError(
        f"Discriminator field not found, null or not string type. Got {_discriminator}."
    )
