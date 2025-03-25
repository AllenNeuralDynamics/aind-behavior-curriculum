"""
Core Trainer primitive.
"""

from abc import abstractmethod
from collections.abc import Iterable
from typing import Annotated, Generic, List, Optional, Self, Type, TypeVar

from pydantic import Field, create_model

from aind_behavior_curriculum.base import AindBehaviorModel
from aind_behavior_curriculum.curriculum import (
    Curriculum,
    Metrics,
    Policy,
    Stage,
    make_task_discriminator,
)
from aind_behavior_curriculum.task import TaskParameters

TCurriculum = TypeVar("TCurriculum", bound=Curriculum)
TMetrics = TypeVar("TMetrics", bound=Metrics)


class TrainerState(AindBehaviorModel, Generic[TCurriculum]):
    """
    Trainer State.
    Pydantic model for de/serialization.
    """

    curriculum: Optional[TCurriculum] = Field(
        ...,
        validate_default=True,
        description="The curriculum used by the trainer",
    )
    stage: Optional[Stage] = Field(
        ...,
        validate_default=True,
        description="The output suggestion of the curriculum",
    )
    is_on_curriculum: bool = Field(
        default=True,
        validate_default=True,
        description="Was the output suggestion generated as part of the curriculum?",
    )
    # Note: This will deserialize to a base Stage object.
    # Should users require the subclass, they are incentivized to use
    # the Trainer.create_trainer_state property instead
    active_policies: Optional[List[Policy]] = Field(
        default=[],
        validate_default=True,
        description="The active policies for the current stage",
    )

    @classmethod
    def default(cls) -> Self:
        """
        Class method to create a default instance of the class.

        Returns:
            Self: An instance of the class with default parameters.
        """
        return cls(
            curriculum=None,
            stage=None,
            is_on_curriculum=False,
            active_policies=None,
        )

    def __eq__(self, other: object) -> bool:
        """
        TrainerState Equality
        """
        if not isinstance(other, TrainerState):
            raise NotImplementedError("Equality comparison only implemented for _TrainerState objects.")

        # Compare 'stage' and 'is_on_curriculum' attributes
        if self.stage != other.stage or self.is_on_curriculum != other.is_on_curriculum:
            return False

        # Compare active_policies using set equality
        if self.active_policies is None and other.active_policies is None:
            return True
        if self.active_policies is None or other.active_policies is None:
            return False

        # Extract Rule callable which is hashable for set equality
        self_rules = [p for p in self.active_policies]
        other_rules = [p for p in other.active_policies]

        return set(self_rules) == set(other_rules)


class Trainer(Generic[TCurriculum]):
    """
    Trainer class for managing and evaluating curriculum stages and policy transitions,
    and updating the task parameters based on the active policies and provided metrics.
    The entry point is the "evaluate" method.
    Attributes:
        curriculum (TCurriculum): The curriculum used by the trainer.
    Methods:
        __init__(self, curriculum: TCurriculum):
        curriculum(self) -> TCurriculum:
        _evaluate_stage_transition(curriculum: Curriculum, current_stage: Stage, metrics: TMetrics) -> Optional[Stage]:
        _evaluate_policy_transitions(cls, current_stage: Stage, active_policies: Iterable[Policy], metrics: TMetrics) -> List[Policy]:
            Evaluates policy transitions for the given current stage and currently active policies, based on the provided metrics.
        evaluate(self, trainer_state: TrainerState, metrics: TMetrics) -> TrainerState:
        get_net_parameter_update(stage_parameters: TaskParameters, stage_policies: Iterable[Policy], curr_metrics: Metrics) -> TaskParameters:
            Aggregates parameter updates of input stage_policies given current stage_parameters and current metrics.
        _get_unique_policies(policies: List[Policy]) -> List[Policy]:
            Filters unique policies based on their rule functions and reassembles the Policy objects.
    """

    def __init__(self, curriculum: TCurriculum):
        """
        Initializes the Trainer with the given curriculum.
        Args:
            curriculum (TCurriculum): The curriculum to be used by the trainer.
        """

        self._curriculum = curriculum
        self._trainer_state_factory = self._construct_trainer_state_type_from_curriculum(curriculum)

    @property
    def curriculum(self) -> TCurriculum:
        """
        Property that returns the current curriculum.

        Returns:
            TCurriculum: The current curriculum instance.
        """
        return self._curriculum

    def create_trainer_state(
        self,
        *,
        stage: Optional[Stage],
        is_on_curriculum: bool = True,
        active_policies: Optional[Iterable[Policy]] = None,
    ) -> TrainerState:
        """
        Property that returns a type-aware TrainerState class.

        Returns:
            Type[TrainerState]: type-aware TrainerState type.
        """
        return self._trainer_state_factory(
            curriculum=self.curriculum,
            stage=stage,
            is_on_curriculum=is_on_curriculum,
            active_policies=list(active_policies) if active_policies else None,
        )

    @staticmethod
    def _construct_trainer_state_type_from_curriculum(
        curriculum: Curriculum,
    ) -> Type[TrainerState]:
        """Constructs a task-type-aware TrainerState"""
        _union_type = make_task_discriminator(curriculum._known_tasks)

        _props = {
            "stage": Annotated[
                Optional[Stage[_union_type]],
                Field(frozen=True, validate_default=True),
            ],
        }

        trainer = create_model(f"{curriculum.name}TrainerState", __base__=TrainerState[type(curriculum)], **_props)  # type: ignore
        return trainer

    @staticmethod
    def _evaluate_stage_transition(curriculum: Curriculum, current_stage: Stage, metrics: TMetrics) -> Optional[Stage]:
        """
        Evaluates whether a transition to a new stage is needed based on the given metrics.

        Args:
            curriculum (Curriculum): The curriculum containing the stage transitions.
            current_stage (Stage): The current stage of the curriculum.
            metrics (TMetrics): The metrics used to evaluate the stage transition.

        Returns:
            Optional[Stage]: The new stage if a transition is made, otherwise None.
        """
        updated_stage: Optional[Stage] = None
        # This line binds the Stage object to the curriculum.
        # TODO may be worth finding a better way to hash the stage object.
        stage_transitions = curriculum.see_stage_transitions(current_stage)
        for stage_eval, dest_stage in stage_transitions:
            # On the first (and only first) true evaluation we transition.
            if stage_eval.invoke(metrics):  # type: ignore
                updated_stage = dest_stage
                break
        return updated_stage

    @classmethod
    def _evaluate_policy_transitions(
        cls,
        current_stage: Stage,
        active_policies: Iterable[Policy],
        metrics: TMetrics,
    ) -> List[Policy]:
        """
        Evaluates policy transitions, for the given current stage and currently active policies, based on the provided metrics.
        Args:
            current_stage (Stage): The current stage in the curriculum.
            active_policies (Iterable[Policy]): Currently active policies.
            metrics (TMetrics): The metrics used to evaluate policy transitions.
        Returns:
            List[Policy]: a list of unique policies that are active after the evaluation.
        """
        # Buffer data structures to store result of active policy transitions.
        dest_policies: list[Policy] = []

        for active_policy in active_policies:
            policy_transitions = current_stage.see_policy_transitions(active_policy)

            _has_transitioned = False
            for policy_eval, dest_policy in policy_transitions:
                # On first true evaluation, add to buffers
                # and evaluate next active_policy.
                if policy_eval.invoke(metrics):  # type: ignore
                    dest_policies.append(dest_policy)
                    _has_transitioned = True
                    break  # onto next active policy
            if not _has_transitioned:  # if no policy transition keep the current one
                dest_policies.append(active_policy)

        return cls._get_unique_policies(dest_policies)

    def evaluate(self, trainer_state: TrainerState, metrics: TMetrics) -> TrainerState:
        """
        Evaluates the current state of the trainer and updates the stage and policies based on the provided metrics.
        Args:
            trainer_state (TrainerState): The current state of the trainer, including the current stage and active policies.
            metrics (TMetrics): The metrics used to evaluate the current state and determine transitions.
        Returns:
            TrainerState: The updated state of the trainer, including the new stage and active policies.
        Raises:
            ValueError: If the current stage or active policies are not set in the trainer state.
        """
        current_stage = trainer_state.stage
        active_policies: Optional[Iterable[Policy]] = trainer_state.active_policies

        if current_stage is None:
            raise ValueError("No current stage. This likely means subject is off-curriculum.")

        # 1) Evaluate stage transitions
        updated_stage = self._evaluate_stage_transition(self.curriculum, current_stage, metrics)

        # 2) Evaluate policy transitions
        # If we've already transitioned stages, we don't need to check policies.
        if updated_stage is None:
            updated_stage = current_stage

            active_policies = active_policies if active_policies is not None else []

            active_policies = self._evaluate_policy_transitions(current_stage, active_policies, metrics)
            # 3) Bootstrap updated parameters with new policies
            updated_task_parameters = self.get_net_parameter_update(
                updated_stage.get_task_parameters(), active_policies, metrics
            )
            updated_stage.set_task_parameters(updated_task_parameters)

        # If we've transitioned stages, we keep to default task_parameters,
        # and reset active_policies to the start_policies of the new stage.
        else:
            active_policies = updated_stage.start_policies

        return self._trainer_state_factory(
            curriculum=self.curriculum,
            stage=updated_stage,
            is_on_curriculum=True,
            active_policies=active_policies,
        )

    @staticmethod
    def get_net_parameter_update(
        stage_parameters: TaskParameters,
        stage_policies: Iterable[Policy],
        curr_metrics: Metrics,
    ) -> TaskParameters:
        """
        Aggregates parameter update of input stage_policies
        given current stage_parameters and current metrics.
        """

        updated_params = stage_parameters.model_copy(deep=True)
        for p in stage_policies:
            p = Policy.normalize_rule_or_callable(p)
            updated_params = p.invoke(curr_metrics, updated_params)

        return updated_params

    @staticmethod
    def _get_unique_policies(policies: List[Policy]) -> List[Policy]:
        """
        set(policies) is not hashable, although Policy
        only contains a function, which is hashable.
        This utility filters on policy functions and
        reassembles the Policy objects.
        """

        filtered_funcs = list(set(p for p in policies))
        output = [Policy(f) for f in filtered_funcs]

        return output


class TrainerServer:
    """
    Pulls subject curriculum and history and performs evaluation.

    Intended usage:
    1) Implement abstract methods
    2) Call Trainer.register_subject() x N
    3) Call Trainer.evaluate_subject() or Trainer.override_subject_status() x N
    """

    def __init__(self):
        """
        Trainer manages a list of subjects initialized here.
        NOTE: Within Trainer subclass, please call super().__init__()
        """
        self.subject_ids: List[int] = []

    @abstractmethod
    def load_data(self, subject_id: int) -> tuple[Curriculum, TrainerState, Metrics]:
        """
        User-defined.
        Loads 3 pieces of data in the following format:
        - subject Curriculum
        - subject Trainer State
        - subject Metrics
        """
        raise NotImplementedError

    @abstractmethod
    def write_data(
        self,
        subject_id: int,
        curriculum: Curriculum,
        trainer_state: TrainerState,
    ) -> None:
        """
        User-defined.
        Exports 3 pieces of data to database.
        - subject Id
        - subject Curriculum
        - subject Trainer State

        """
        raise NotImplementedError

    def _update_subject_trainer_state(
        self,
        s_id: int,
        curriculum: Curriculum,
        stage: Optional[Stage],
        updated_stage_parameters: Optional[TaskParameters],
        stage_policies: Optional[Iterable[Policy]],
    ) -> None:
        """
        Updates subject history, which involves many steps.
        Stage parameters and policies are expected to be part
        of stage-- not checked here b/c this is a private utility.

        If any of {stage, updated_stage_parameters, stage_policies} are None,
        all of the elements are expected to be None.
        """
        if not (stage is None or updated_stage_parameters is None or stage_policies is None):
            stage = stage.model_copy(deep=True)
            stage.set_task_parameters(updated_stage_parameters)

        trainer = Trainer(curriculum)
        if stage is None:
            trainer_state = trainer.create_trainer_state(stage=None, is_on_curriculum=False, active_policies=None)
        else:
            trainer_state = trainer.create_trainer_state(
                stage=stage,
                is_on_curriculum=True,
                active_policies=(list(stage_policies) if stage_policies else None),
            )

        self.write_data(s_id, curriculum, trainer_state)

    def register_subject(
        self,
        subject_id: int,
        curriculum: Curriculum,
        start_stage: Stage,
        start_policies: Optional[Policy | List[Policy]] = None,
    ) -> None:
        """
        Adds subject into the Trainer system.
        If start_policies is None,
        registration defaults to the Stage.start_policies.
        """

        curriculum = curriculum.validate_curriculum()

        if start_stage not in curriculum.see_stages():
            raise ValueError("Provided start_stage is not in provided curriculum.")
        if subject_id in self.subject_ids:
            raise ValueError(f"Subject_id {subject_id} is already registered.")

        if start_policies is None:
            start_policies = start_stage.start_policies
        elif isinstance(start_policies, Policy):
            start_policies = [start_policies]

        for s_policy in start_policies:
            if s_policy not in start_stage.see_policies():
                raise ValueError(f"Provided start_policy {s_policy} not in provided start_stage {start_stage.name}.")

        _start_policies = list(start_policies)

        initial_params = Trainer.get_net_parameter_update(
            start_stage.get_task_parameters(),
            _start_policies,
            curr_metrics=Metrics(),  # Metrics is empty on registration.
        )
        self._update_subject_trainer_state(
            subject_id,
            curriculum,
            start_stage,
            initial_params,
            _start_policies,
        )

        # Add to trainer's local list!
        self.subject_ids.append(subject_id)

    def evaluate_subjects(self) -> None:
        """
        Calls user-defined functions to automatically update
        subject stage along curriculum.
        The time-step between evaluate_subject calls is flexible--
        this function will skip subject to the latest stage/policy
        they are applicable for.

        Evaluation checks for stage transitions before policy transitions.

        If subject does not satisfy any transition criteria,
        this method creates a duplicate current (stage, policy) entry
        in stage history.
        """

        for s_id in self.subject_ids:
            curriculum, trainer_state, curr_metrics = self.load_data(s_id)
            trainer = Trainer(curriculum)

            if trainer_state.stage is not None:
                updated_trainer_state = trainer.evaluate(trainer_state, curr_metrics)
                if updated_trainer_state.stage is None:
                    raise ValueError("Trainer.evaluate() returned None stage. This should not happen.")
                updated_parameters = (
                    updated_trainer_state.stage.get_task_parameters()  # pylint: disable=no-member
                )
            else:
                updated_trainer_state = trainer.create_trainer_state(
                    stage=None,
                    is_on_curriculum=False,
                    active_policies=trainer_state.active_policies,
                )  # Not sure if this is correct, but a user may want to keep track of the policies that were active when the subject was off-curriculum.
                updated_parameters = None

            self._update_subject_trainer_state(
                s_id,
                curriculum,
                updated_trainer_state.stage,
                updated_parameters,
                updated_trainer_state.active_policies,
            )

    def override_subject_status(
        self,
        s_id: int,
        override_stage: Stage,
        override_policies: Policy | list[Policy],
    ) -> None:
        """
        Override subject (stage, policies) independent of evaluation.
        Stage and Policy objects may be accessed by calling
        Trainer.load_data and looking inside of the returned Curriculum.

        (Soft Rejection-- send mouse to Stage/Policy w/in Curriculum)
        """
        if s_id not in self.subject_ids:
            raise ValueError(f"subject id {s_id} not in self.subject_ids.")

        curriculum, _, curr_metrics = self.load_data(s_id)

        if override_stage not in curriculum.see_stages():
            raise ValueError(
                f"Override stage {override_stage.name} not in curriculum.\
                curriculum stages for subject id {s_id}."
            )

        if not isinstance(override_policies, Iterable):
            override_policies = [override_policies]
        for o_policy in override_policies:
            o_policy = Policy.normalize_rule_or_callable(o_policy)
            if o_policy not in override_stage.see_policies():
                raise ValueError(
                    f"Override policy {o_policy} not in \
                    given override stage {override_stage.name}."
                )

        # Update Stage parameters according to override policies
        updated_params = Trainer(curriculum).get_net_parameter_update(
            override_stage.get_task_parameters(),
            override_policies,
            curr_metrics,
        )
        self._update_subject_trainer_state(
            s_id,
            curriculum,
            override_stage,
            updated_params,
            list(override_policies),
        )

    def eject_subject(self, s_id: int) -> None:
        """
        Send mouse off curriculum.
        Only way to get mouse back into system is
        with Trainer.override_subject_status(...)
        """

        curriculum, _, _ = self.load_data(s_id)

        self._update_subject_trainer_state(
            s_id,
            curriculum,
            stage=None,
            updated_stage_parameters=None,
            stage_policies=None,
        )
