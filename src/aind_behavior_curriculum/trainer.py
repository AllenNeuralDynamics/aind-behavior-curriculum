"""
Core Trainer primitive.
"""

from abc import abstractmethod
from collections.abc import Iterable
from typing import Generic, List, Optional, Self, Tuple, TypeAlias, TypeVar

from pydantic import Field

from aind_behavior_curriculum.base import AindBehaviorModel
from aind_behavior_curriculum.curriculum import (
    Curriculum,
    Metrics,
    Policy,
    Stage,
)
from aind_behavior_curriculum.task import TaskParameters

StageEntry: TypeAlias = Optional[Stage]
PolicyEntry: TypeAlias = Optional[Tuple[Policy, ...]]


class _TrainerState(AindBehaviorModel):
    """
    Trainer State.
    Pydantic model for de/serialization.
    """

    stage: StageEntry = Field(
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
    # Should users require the subclass, they will need to either serialize it themselves,
    # or we should make CurriculumState a generic model on Union[SubStage1, SubStage2, ...]
    active_policies: PolicyEntry = Field(
        default=None,
        validate_default=True,
        description="The active policies for the current stage",
    )

    @classmethod
    def default(cls) -> Self:
        return cls(stage=None, is_on_curriculum=False, active_policies=None)

    def __eq__(self, other: object) -> bool:
        """
        TrainerState Equality
        """
        if not isinstance(other, _TrainerState):
            return NotImplemented

        # Compare 'stage' and 'is_on_curriculum' attributes
        if (
            self.stage != other.stage
            or self.is_on_curriculum != other.is_on_curriculum
        ):
            return False

        # Compare active_policies using set equality
        if self.active_policies is None and other.active_policies is None:
            return True
        if self.active_policies is None or other.active_policies is None:
            return False

        # Extract Rule callable which is hashable for set equality
        self_rules = [p.rule for p in self.active_policies]
        other_rules = [p.rule for p in other.active_policies]

        return set(self_rules) == set(other_rules)


TCurriculum = TypeVar("TCurriculum", bound=Curriculum)
TMetrics = TypeVar("TMetrics", bound=Metrics)


def _make_trainer_state_type_aware(curriculum: Curriculum) -> _TrainerState:
    """
    Makes the Curriculum type aware of the Trainer state.
    """
    return curriculum


class Trainer(Generic[TCurriculum]):

    def __init__(self, curriculum: TCurriculum):
        self._curriculum = curriculum
        self._trainer = _make_trainer_state_type_aware(self.curriculum)

    @property
    def curriculum(self) -> TCurriculum:
        return self._curriculum

    @staticmethod
    def _evaluate_stage_transition(
        curriculum: Curriculum, current_stage: Stage, metrics: TMetrics
    ) -> Optional[Stage]:
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
            if stage_eval.rule(metrics):  # type: ignore
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
            policy_transitions = current_stage.see_policy_transitions(
                active_policy
            )

            _has_transitioned = False
            for policy_eval, dest_policy in policy_transitions:
                # On first true evaluation, add to buffers
                # and evaluate next active_policy.
                if policy_eval.rule(metrics):  # type: ignore
                    dest_policies.append(dest_policy)
                    _has_transitioned = True
                    break  # onto next active policy
            if (
                not _has_transitioned
            ):  # if no policy transition keep the current one
                dest_policies.append(active_policy)

        return cls._get_unique_policies(dest_policies)

    def evaluate(
        self, trainer_state: _TrainerState, metrics: TMetrics
    ) -> _TrainerState:
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
        active_policies: Optional[Iterable[Policy]] = (
            trainer_state.active_policies
        )

        if current_stage is None:
            raise ValueError(
                "No current stage. This likely means subject is off-curriculum."
            )
        if active_policies is None:
            raise ValueError(
                "No active policies. This likely means subject is off-curriculum."
            )

        # 1) Stage Transition
        updated_stage = self._evaluate_stage_transition(
            self.curriculum, current_stage, metrics
        )

        # 2) Policy Transition
        # If we've already transitioned stages, we don't need to check policies.
        if updated_stage is None:
            updated_stage = current_stage
            active_policies = self._evaluate_policy_transitions(
                current_stage, active_policies, metrics
            )
        # If we've transitioned stages, we need to reset the active policies.
        else:
            active_policies = updated_stage.start_policies

        # 3) Bootstrap updated parameters
        updated_task_parameters = self.get_net_parameter_update(
            current_stage.get_task_parameters(), active_policies, metrics
        )

        updated_stage.set_task_parameters(updated_task_parameters)

        return _TrainerState(
            stage=updated_stage,
            is_on_curriculum=True,
            active_policies=tuple(active_policies),
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
            updated_params = p.rule(curr_metrics, updated_params)

        return updated_params

    @staticmethod
    def _get_unique_policies(policies: List[Policy]) -> List[Policy]:
        """
        set(policies) is not hashable, although Policy
        only contains a function, which is hashable.
        This utility filters on policy functions and
        reassembles the Policy objects.
        """

        filtered_funcs = list(set(p.rule for p in policies))
        output = [Policy(rule=f) for f in filtered_funcs]

        return output


class TrainerServer:
    """
    Pulls subject curriculum and history,
    and performs fundamental curriculum evaluation/update.

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
        self.subject_ids = []

    @abstractmethod
    def load_data(
        self, subject_id: int
    ) -> tuple[Curriculum, _TrainerState, Metrics]:
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
        trainer_state: _TrainerState,
    ) -> None:
        """
        User-defined.
        Exports 3 pieces of data to database.
        - subject Id
        - subject Curriculum
        - subject Trainer State

        For Curriculums with no internal policies, insert tacit INIT_STAGE
        """
        raise NotImplementedError

    def _update_subject_trainer_state(
        self,
        s_id: int,
        curriculum: Curriculum,
        stage: StageEntry,
        updated_stage_parameters: Optional[TaskParameters],
        stage_policies: PolicyEntry,
    ) -> None:
        """
        Updates subject history, which involves many steps.
        Stage parameters and policies are expected to be part
        of stage-- not checked here b/c this is a private utility.

        If any of {stage, updated_stage_parameters, stage_policies} are None,
        all of the elements are expected to be None.
        """
        if not (
            stage is None
            or updated_stage_parameters is None
            or stage_policies is None
        ):
            stage = stage.model_copy(deep=True)
            stage.set_task_parameters(updated_stage_parameters)

        if stage is None:
            trainer_state = _TrainerState(
                stage=None, is_on_curriculum=False, active_policies=None
            )
        else:
            trainer_state = _TrainerState(
                stage=stage,
                is_on_curriculum=True,
                active_policies=stage_policies,
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

        if not (start_stage in curriculum.see_stages()):
            raise ValueError(
                "Provided start_stage is not in provided curriculum."
            )
        if subject_id in self.subject_ids:
            raise ValueError(f"Subject_id {subject_id} is already registered.")

        if start_policies is None:
            start_policies = start_stage.see_policies()
        elif isinstance(start_policies, Policy):
            start_policies = [start_policies]

        for s_policy in start_policies:
            if not (s_policy in start_stage.see_policies()):
                raise ValueError(
                    f"Provided start_policy {s_policy} not in "
                    f"provided start_stage {start_stage.name}."
                )

        _start_policies = tuple(start_policies)

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

    def evaluate_subjects(self) -> None:  # noqa: C901
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

            updated_trainer_state = trainer.evaluate(
                trainer_state, curr_metrics
            )
            if updated_trainer_state.stage is None:
                updated_parameters = None
            else:
                updated_parameters = (
                    updated_trainer_state.stage.get_task_parameters()
                )

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
        if not (s_id in self.subject_ids):
            raise ValueError(f"subject id {s_id} not in self.subject_ids.")

        curriculum, _, curr_metrics = self.load_data(s_id)

        if not (override_stage in curriculum.see_stages()):
            raise ValueError(
                f"Override stage {override_stage.name} not in curriculum.\
                curriculum stages for subject id {s_id}."
            )

        if isinstance(override_policies, Policy):
            override_policies = [override_policies]
        for o_policy in override_policies:
            if not (o_policy in override_stage.see_policies()):
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
            tuple(override_policies),
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
