"""
Core Stage and Curriculum Primitives.
"""

import importlib
import inspect
import warnings
from types import EllipsisType
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    ParamSpec,
    Self,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from pydantic import Field, GetJsonSchemaHandler, ValidationError, create_model
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing_extensions import TypeAliasType

from aind_behavior_curriculum.base import (
    AindBehaviorModel,
    AindBehaviorModelExtra,
)
from aind_behavior_curriculum.task import SEMVER_REGEX, Task, TaskParameters

TTask = TypeVar("TTask", bound=Task)
_P = ParamSpec("_P")
_R = TypeVar("_R")


class Metrics(AindBehaviorModelExtra):
    """
    Abstract Metrics class.
    Subclass with Metric values.
    """


class _Rule(Generic[_P, _R]):
    """
    Custom Pydantic Type that defines de/serialization for Callables.
    This type is not intended to be used directly, but rather subclassed
    with explicit typing in the generics.

    The _Rule type wraps a Callable with a specific signature.
    The Callable type signature is evaluated at runtime to ensure that the
    type hinting matches the expected _Rule (or subtype) type signature.
    For the duck-type aficionados, this type can be skipped by calling
    Rule(..., skip_validation=True) or by not annotating the Callable.
    """

    def __init__(self, function: Callable[_P, _R], *, skip_validation: bool = False) -> None:
        """
        Initializes a new instance of the class.
        Args:
            function (Callable[_P, _R]): The function to be used. If an instance of _Rule is passed,
                                         the callable attribute of the _Rule instance will be used.
            skip_validation (bool, optional): If set to True, skips the validation of the callable's typing.
                                              Defaults to False.
        Returns:
            None
        """

        # Just in case people pass the _Rule instance directly
        # Instead of the callable
        if isinstance(function, _Rule):
            function = function.callable

        if not skip_validation:
            self._validate_callable_typing(function)
        self._callable = function

    def invoke(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """Wraps the inner callable."""
        return self._callable(*args, **kwargs)

    def __eq__(self, other: Any) -> bool:
        """
        Custom equality method.
        Two instances of the same subclass type are considered equal.
        """
        if not isinstance(other, _Rule):
            return False
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        """
        Returns the hash value for the object.
        """
        return hash(hash(self.name) + hash(self.callable))

    @property
    def name(self) -> str:
        """
        Name of the Rule.
        """
        return self.serialize_rule(self)

    @property
    def callable(self) -> Callable[_P, _R]:
        """Returns the wrapped callable."""
        return self._callable

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

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls._deserialize_rule),
            ]
        )

        from_callable_schema = core_schema.chain_schema(
            [
                core_schema.callable_schema(),
                core_schema.no_info_plain_validator_function(cls._deserialize_rule),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    from_str_schema,
                    from_callable_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(function=cls.serialize_rule),
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

    @classmethod
    def normalize_rule_or_callable(cls, rule: Callable | "_Rule") -> Self:
        """Ensures the outgoing type is normalized from a Callable or _Rule."""
        if isinstance(rule, cls):
            return rule
        if isinstance(rule, _Rule):
            return cls(rule.callable)
        if callable(rule):
            return cls(rule)
        else:
            raise TypeError("rule must be a Callable or _Rule type.")

    @classmethod
    def _deserialize_rule(cls, value: str | Callable[_P, _R]) -> "_Rule[_P, _R]":
        """
        Custom Deserialization.
        Imports function according to package and function name.
        """
        callable_handle: Callable[_P, _R]
        if callable(value):
            return cls(value)

        if isinstance(value, str):
            try:
                module_name, _, attr_path = value.partition(".")
                while "." in attr_path:
                    module_name += "." + attr_path.split(".", 1)[0]
                    attr_path = attr_path.split(".", 1)[1]

                module = importlib.import_module(module_name)
                obj = module
                for attr in attr_path.split("."):
                    obj = getattr(obj, attr)
            except (ModuleNotFoundError, AttributeError) as e:
                assert isinstance(value, str)
                callable_handle = _NonDeserializableCallable[_P, _R](value, e)
            else:
                callable_handle = cast(Callable[_P, _R], obj)

        return cls(callable_handle)

    @classmethod
    def serialize_rule(cls, value: Union[str, "_Rule[_P, _R]"]) -> str:
        """
        Custom Serialization.
        Simply exports reference to function as package + function name.
        """

        if isinstance(value, str):
            ret = cls._deserialize_rule(value)
        else:
            ret = value
        assert isinstance(ret, _Rule)

        if is_non_deserializable_callable(ret.callable):
            # Python 3.13 has a better way to infer
            # types with arbitrary clause code, but for now...
            assert isinstance(ret.callable, _NonDeserializableCallable)
            return ret.callable.mock_serialize()
        else:
            module = ret.callable.__module__
            qualname = ret.callable.__qualname__
            return f"{module}.{qualname}"

    @classmethod
    def _validate_callable_typing(cls, r: Callable[_P, _R]) -> None:
        """
        Validates that the provided callable `r` matches the expected signature
        defined by the generic types of the class.
        Args:
            r (Callable[_P, _R]): The callable to validate.
        Raises:
            ValueError: If `r` is not callable.
            TypeError: If the class does not define its generic types explicitly,
                    or if the callable `r` does not match the expected signature.
        """

        if isinstance(r, cls):
            return

        if is_non_deserializable_callable(r):
            return

        if not callable(r):
            raise ValueError("Rule must be callable.")

        # For some reason, generics do not materialize by default.
        # We fetch them manually....
        if isinstance(x := cls._solve_generic_typing(cls), TypeError):
            raise x
        else:
            expected_callable, expected_return = x

        # Compare signatures
        sig = inspect.signature(r)

        try:
            # Compare inputs
            if (_eval := cls._validate_signature_input(expected_callable, sig)) is not None:
                raise _eval

            if (_eval := cls._validate_signature_output(expected_return, sig)) is not None:
                raise _eval

        except TypeError as e:
            e.add_note(f"Expected callable type signature: {expected_callable} -> {expected_return}. Got {sig}.")
            raise e

    @staticmethod
    def _validate_signature_input(expected_callable: Any, sig: inspect.Signature) -> Optional[TypeError]:
        """Validates the input signature of the incoming callable against
        the expected input type."""

        if isinstance(expected_callable, EllipsisType):
            return None

        if not (len(sig.parameters) == 0 and expected_callable is type(None)):
            if not (len(sig.parameters) == len(expected_callable)):
                return TypeError(
                    f"Callable must have {len(expected_callable)} parameters, but {len(sig.parameters)} were found."
                )

            for param, expected_type in zip(list(sig.parameters.values()), expected_callable):
                if param.annotation is not param.empty:
                    if not issubclass(param.annotation, expected_type):
                        return TypeError(
                            f"Parameter '{param.name}' must be of type {expected_type}, but {param.annotation} was found."
                        )
        return None

    @staticmethod
    def _validate_signature_output(expected_return: Any, sig: inspect.Signature) -> Optional[TypeError]:
        """Validates the output signature of the incoming callable against
        the expected output type."""

        if isinstance(expected_return, EllipsisType):
            return None

        if sig.return_annotation is None and expected_return is type(None):
            return None

        if sig.return_annotation is not inspect.Signature.empty:
            if not issubclass(sig.return_annotation, expected_return):
                return TypeError(
                    f"Callable return type must be {expected_return}, but {sig.return_annotation} was found."
                )

        return None

    @staticmethod
    def _solve_generic_typing(cls_: Any) -> Tuple[Any, Any] | TypeError:
        """Returns an inner generic type's type hint information"""
        origin_bases = getattr(cls_, "__orig_bases__", [])
        if not origin_bases:
            return TypeError(f"Class {cls_.__name__} must define its generic types.")

        for base in origin_bases:
            # Hopefully nobody uses multiple inheritance with Rule
            # But just in case we grab the first Rule parent
            origin = get_origin(base)
            args = get_args(base)

            if origin is _Rule and len(args) == 2:
                # we assume that the constructor only takes a single
                # callable as argument. Can always be extended
                # partials with partial
                return (args[0], args[1])
        return TypeError(f"Class {cls_.__name__} must define its generic types explicitly.")


def is_non_deserializable_callable(value: Any) -> bool:
    """
    Check if the given value is an instance of _NonDeserializableCallable.
    Args:
        value (Any): The value to check.
    Returns:
        bool: True if the value is an instance of _NonDeserializableCallable, False otherwise.
    """

    return isinstance(value, _NonDeserializableCallable)


def try_materialize_non_deserializable_callable_error(
    value: "_NonDeserializableCallable",
) -> Optional[Exception]:
    """
    Attempts to materialize the error from a non-deserializable callable.

    Args:
        value (_NonDeserializableCallable): The value to check and potentially
                                            extract the error from.

    Returns:
        Optional[Exception]: The error associated with the non-deserializable
                             callable if it exists, otherwise None.
    """
    if not is_non_deserializable_callable(value):
        return None
    return value.error


class _NonDeserializableCallable(Generic[_P, _R]):
    """
    A class representing a reference to callable that could not be deserialized.
    """

    def __init__(self, callable_repr: str, error: Exception) -> None:
        """
        Initializes the instance with a callable representation and an error.

        Args:
            callable_repr (str): A string representation of the callable.
            error (Exception): The exception that was raised.

        Returns:
            None
        """
        self._callable_repr = callable_repr
        self._error = error

    @property
    def error(self) -> Exception:
        """
        Property that returns the error associated with the curriculum.

        Returns:
            Exception: The error associated with the curriculum.
        """
        return self._error

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """Shim method to raise an error when the callable is called."""
        raise RuntimeError(f"Cannot call the non-deserializable callable reference '{self._callable_repr}'.")

    def mock_serialize(self) -> str:
        """Shim method to return the callable representation."""
        return self._callable_repr

    def __hash__(self):
        """Shim method to return the hash of the callable."""
        return hash(self._callable_repr)


class Policy(_Rule[[Metrics, TaskParameters], TaskParameters]):
    """
    User-defined function that defines
    how current Task parameters change according to metrics.
    It subclasses _Rule.
    """

    pass


class PolicyTransition(_Rule[[Metrics], bool]):
    """
    User-defined function that defines
    how current Policies change during a Stage.
    It subclasses _Rule.
    """

    pass


NodeTypes = TypeVar("NodeTypes")
EdgeType = TypeVar("EdgeType")


class BehaviorGraph(AindBehaviorModel, Generic[NodeTypes, EdgeType]):
    """
    Core directed graph data structure used in Stage and Curriculum.
    """

    nodes: Dict[int, NodeTypes] = Field(default={}, validate_default=True)
    graph: Dict[int, List[Tuple[EdgeType, int]]] = Field(default={}, validate_default=True)

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
        if node not in self.nodes.values():
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
        if start_node not in self.nodes.values():
            new_id = self._create_node_id()
            self.nodes[new_id] = start_node
            self.graph[new_id] = []
        start_id = self._get_node_id(start_node)

        # Resolve id of dest_node
        if dest_node not in self.nodes.values():
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

        if start_node not in self.nodes.values():
            raise ValueError(f"Node {start_node} is not in the behavior graph to be removed.")

        if dest_node not in self.nodes.values():
            raise ValueError(f"Node {dest_node} is not in the behavior graph to be removed.")

        start_id = self._get_node_id(start_node)
        dest_id = self._get_node_id(dest_node)
        if (rule, dest_id) not in self.graph[start_id]:
            raise ValueError(f"Node {start_node} does not transition into Node {dest_node} with Rule {rule}.")

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

    def see_node_transitions(self, node: NodeTypes) -> List[Tuple[EdgeType, NodeTypes]]:
        """
        See transitions of node in behavior graph.
        """

        if node not in self.nodes.values():
            raise ValueError(f"Node {node} is not in the behavior graph.")

        node_id = self._get_node_id(node)
        node_list = self.graph[node_id]
        return [(rule, self.nodes[p_id]) for (rule, p_id) in node_list]

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
            if n not in self.nodes.values():
                raise ValueError(f"Node {n} is not a node inside the behavior graph.")
            input_transitions.append((rule, self._get_node_id(n)))

        n_id = self._get_node_id(node)
        self.graph[n_id] = input_transitions

    def __eq__(self, other: Any) -> bool:
        """
        Compare this object with another for equality.

        Args:
            other (Any): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        if not isinstance(other, BehaviorGraph):
            return False
        return self.model_dump() == other.model_dump()


class PolicyGraph(BehaviorGraph[Policy, PolicyTransition]):
    """
    Graph for Stage.
    """

    pass


class MetricsProvider(_Rule[..., Metrics]):
    """A type for a callable that is able to produce Metrics"""

    pass


class Stage(AindBehaviorModel, Generic[TTask]):
    """
    Instance of a Task.
    Task Parameters may change according to rules defined in BehaviorGraph.
    Stage manages a BehaviorGraph instance with a read/write API.
    """

    name: str = Field(..., description="Stage name.")
    task: TTask = Field(..., description="Task in which this stage is based off of.")
    graph: PolicyGraph = Field(
        default_factory=PolicyGraph,
        validate_default=True,
        description="Policy Graph.",
    )
    start_policies: List[Policy] = Field(default_factory=list, description="List of starting policies.")
    metrics_provider: Optional[MetricsProvider] = Field(
        default=None,
        description="A MetricsProvider instance that keeps a reference to a handle to create a metrics object for this stage.",
    )

    def __eq__(self, other: Any) -> bool:
        """
        Custom equality method.
        Two Stage instances are only distinguished by name.
        """
        # TODO. We should consider cleaning this up in the future.
        # Since Stage is mutable at the level of the TaskParameters
        # we cannot simply compare the model_dump() of the two instances.
        # However, we need the __eq__ to look for nodes in the graph.
        # The solution is probably to make our own "look_up" method
        # This should generally be safe since the Stage name is unique,
        # but it is a brittle solution.
        if not isinstance(other, Stage):
            return False
        return self.name == other.name

    def model_post_init(self, __context):
        """Runs after model_construct to ensure that the
        initial policies update the PolicyGraph"""
        super().model_post_init(__context)
        self.set_start_policies(self.start_policies, append_non_existing=True)

    def set_start_policies(
        self,
        start_policies: Policy | Iterable[Policy],
        append_non_existing: bool = True,
    ) -> None:
        """
        Sets stage's start policies to start policies provided.
        Input overwrites existing start policies.
        """
        if not isinstance(start_policies, Iterable):
            start_policies = [start_policies]

        for policy in start_policies:
            policy = Policy.normalize_rule_or_callable(policy)
            if policy not in self.graph.see_nodes():
                if append_non_existing:
                    self.add_policy(policy)
                else:
                    raise ValueError(f"Policy {policy} is not in the policy graph.")

        self.start_policies = list(start_policies)

    def add_policy(self, policy: Policy) -> None:
        """
        Adds a floating policy to the Stage adjacency graph.
        """
        policy = Policy.normalize_rule_or_callable(policy)
        if policy in self.graph.see_nodes():
            raise ValueError(f"Policy {policy.name} is a duplicate Policy in Stage {self.name}.")

        self.graph.add_node(policy)

    def remove_policy(self, policy: Policy) -> None:
        """
        Removes policy and all associated incoming/outgoing
        transition rules from the stage graph.
        NOTE: Removed nodes and transitions have the side effect
        of changing transition priority.
        """
        policy = Policy.normalize_rule_or_callable(policy)
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

        self.graph.add_transition(
            Policy.normalize_rule_or_callable(start_policy),
            Policy.normalize_rule_or_callable(dest_policy),
            PolicyTransition.normalize_rule_or_callable(rule),
        )

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
            Policy.normalize_rule_or_callable(start_policy),
            Policy.normalize_rule_or_callable(dest_policy),
            PolicyTransition.normalize_rule_or_callable(rule),
            remove_start_policy,
            remove_dest_policy,
        )

    def see_policies(self) -> List[Policy]:
        """
        See policies of policy graph.
        """
        return self.graph.see_nodes()

    def see_policy_transitions(self, policy: Policy) -> List[Tuple[PolicyTransition, Policy]]:
        """TTask
        See transitions of stage in policy graph.
        """

        return self.graph.see_node_transitions(Policy.normalize_rule_or_callable(policy))

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
        policy = Policy.normalize_rule_or_callable(policy)
        policy_transitions = [
            (
                PolicyTransition.normalize_rule_or_callable(t),
                Policy.normalize_rule_or_callable(p),
            )
            for (t, p) in policy_transitions
        ]
        current_list = [(t, p) for (t, p) in self.see_policy_transitions(policy)]

        if len(policy_transitions) != len(current_list):
            raise ValueError(
                f"Number of input node transitions {policy_transitions} does not \
                match the number of elements under this node: {self.see_policy_transitions(policy)}.\
                Please call 'see_policy_transitions()' for a precise list of elements."
            )

        self.graph.set_transition_priority(policy, policy_transitions)

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

    def validate_stage(self) -> Self:
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


class StageTransition(_Rule[[Metrics], bool]):
    """
    User-defined function that defines
    criteria for transitioning stages based on metrics.
    Subclasses _Rule.
    """

    pass


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
    graph: Annotated[StageGraph, Field(default=StageGraph(), validate_default=True)]

    @property
    def _known_tasks(self) -> List[Type[Task]]:
        """Get all known tasks in the curriculum."""

        # We introspect into the StageGraph[T] type to get the known tasks.
        _generic = self.model_fields["graph"].annotation
        _inner_args = _generic.__dict__["__pydantic_generic_metadata__"]["args"]

        _inner_union: Type
        if len(_inner_args) == 0:
            _inner_union = Task
        else:
            _inner_args = _inner_args[0]
            _inner_union = get_args(_inner_args.__value__)[0]

        if isinstance(_inner_union, type):
            _known_tasks = [_inner_union]
        else:
            _known_tasks = [x for x in get_args(_inner_union)]

        # Since we are here, we also check if the known tasks match the nodes in the graph
        # The tasks known to the graph type should be a super set of the known tasks in the nodes
        _known_nodes = [type(stage.task) for stage in self.graph.see_nodes()]
        if not set(_known_tasks).issuperset(set(_known_nodes)):
            raise ValueError(
                "Known tasks in the Curriculum do not match the tasks in the StageGraph. This is likely a problem with StageGraph type definition."
            )
        return _known_tasks

    def task_discriminator_type(self) -> TypeAliasType:
        """Create a Discriminated Union  type for the known tasks."""
        return make_task_discriminator(self._known_tasks)

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
            raise ValueError(f"Task {stage.task} is not a known task type in the Curriculum.")

        if stage in self.graph.see_nodes():
            raise ValueError(f"Stage {stage.name} is a duplicate stage in Curriculum.")

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
            from the existing Stage_A.
        If Stage_B has been added to stage before, this method creates a transition
            into the existing Stage_B.

        NOTE: The order in which this method
        is called sets the order of transition priority.
        """

        self.graph.add_transition(
            start_stage,
            dest_stage,
            StageTransition.normalize_rule_or_callable(rule),
        )

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
            StageTransition.normalize_rule_or_callable(rule),
            remove_start_stage,
            remove_dest_stage,
        )

    def see_stages(self) -> List[Stage]:
        """
        See stages of curriculum graph.
        """
        return self.graph.see_nodes()

    def see_stage_transitions(self, stage: Stage) -> List[Tuple[StageTransition, Stage]]:
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

        stage_transitions = [(StageTransition.normalize_rule_or_callable(t), s) for (t, s) in stage_transitions]

        if len(stage_transitions) != len(self.see_stage_transitions(stage)):
            raise ValueError(
                f"Elements of input node transitions {stage_transitions} does not \
                    match the elements under this node: {self.see_stage_transitions(stage)}. \
                        Please call 'see_stage_transitions()' for a precise list of elements."
            )

        self.graph.set_transition_priority(stage, stage_transitions)

    def validate_curriculum(self) -> Self:
        """
        Validate curriculum for export/serialization.
        """

        if not all([self._is_task_type_known(stage.task) for stage in self.see_stages()]):
            raise ValueError("Not all tasks in the curriculum are known. Please add stages with known tasks.")

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


def create_curriculum(
    name: str,
    version: str,
    tasks: Iterable[Type[Task]],
    pkg_location: Optional[str] = None,
) -> Type[Curriculum]:
    """
    Creates a new curriculum model with the specified name, version, and tasks.
    Args:
        name (str): The name of the curriculum.
        version (str): The version of the curriculum, following semantic versioning.
        tasks (Iterable[Type[Task]]): An iterable of Task types to be included in the curriculum.
        pkg_location (Optional[str]): Optional package location string.
    Returns:
        Type[Curriculum]: A new curriculum model type.
    Raises:
        ValueError: If no tasks are provided.
    """

    if not any(tasks):
        raise ValueError("At least one task must be provided.")

    _tasks_tagged = make_task_discriminator(tasks)
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
            StageGraph[_tasks_tagged],  # type: ignore
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


def make_task_discriminator(tasks: Iterable[Type[Task]]) -> TypeAliasType:
    """
    Creates a discriminated union type for the given tasks.
    This function takes a variable number of Task types and generates a
    discriminated union type using the 'name' field of each task to create
    a discriminated union.
    Args:
        tasks (Iterable[Type[Task]]): A variable number of Task types.
    Returns:
        Type: A TypeAliasType with the discriminated union type of the provided tasks.
    """

    return TypeAliasType(
        "known_task_types",
        Annotated[
            Union[tuple(set(tasks))],
            Field(discriminator="name"),
        ],
    )
