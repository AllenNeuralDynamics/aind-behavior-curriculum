"""
Core Trainer primitive.
"""

from abc import abstractmethod
from collections.abc import Iterable
from typing import List, Optional, Tuple, TypeAlias

from pydantic import Field

from aind_behavior_curriculum.base import AindBehaviorModel
from aind_behavior_curriculum.curriculum import (
    Curriculum,
    Metrics,
    Policy,
    Stage,
)
from aind_behavior_curriculum.task import TaskParameters

Stage_Entry: TypeAlias = Stage | None
Policy_Entry: TypeAlias = Tuple[Policy, ...] | None


class SubjectHistory(AindBehaviorModel):
    """
    Record of subject locations in Curriculum.
    Histories can hold a 'None' object indicating user
    override off-curriculum.
    Pydantic model for de/serialization.
    """

    stage_history: list[Stage_Entry] = Field(default=[], validate_default=True)
    policy_history: list[Policy_Entry] = Field(
        default=[], validate_default=True
    )

    def add_entry(self, stage: Stage_Entry, policies: Policy_Entry) -> None:
        """
        Add to stage and policy history synchronously.
        """
        self.stage_history.append(stage)

        # Sort policies for ease of reading/testing.
        if not (policies is None):
            policies = tuple(sorted(policies, key=lambda x: x.rule.__name__))

        self.policy_history.append(policies)

    def peek_last_entry(self) -> tuple[Stage_Entry, Policy_Entry]:
        """
        Return most-recently added entry.
        """
        return (self.stage_history[-1], self.policy_history[-1])


class Trainer:
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
    ) -> tuple[Curriculum, SubjectHistory, Metrics]:
        """
        User-defined.
        Loads 3 pieces of data in the following format:
        - subject Curriculum
        - subject History
        - subject Metrics
        """
        raise NotImplementedError

    @abstractmethod
    def write_data(
        self,
        subject_id: int,
        curriculum: Curriculum,
        history: SubjectHistory,
    ) -> None:
        """
        User-defined.
        Exports 3 pieces of data to database.
        - subject Id
        - subject Curriculum
        - subject History

        For Curriculums with no internal policies, insert tacit INIT_STAGE
        """
        raise NotImplementedError

    def _get_net_parameter_update(
        self,
        stage_parameters: TaskParameters,
        stage_policies: Iterable[Policy],
        curr_metrics: Metrics,
    ) -> TaskParameters:
        """
        Aggregates parameter update of input stage_policies
        given current stage_parameters and current metrics.
        """

        updated_params = stage_parameters
        for p in stage_policies:
            updated_params = p.rule(curr_metrics, updated_params)

        return updated_params

    def _get_unique_policies(self, policies: List[Policy]) -> List[Policy]:
        """
        set(policies) is not hashable, although Policy
        only contains a function, which is hashable.
        This utility filters on policy functions and
        reassembles the Policy objects.
        """

        filtered_funcs = list(set(p.rule for p in policies))
        output = [Policy(rule=f) for f in filtered_funcs]

        return output

    def _update_subject_history(
        self,
        s_id: int,
        curriculum: Curriculum,
        subject_history: SubjectHistory,
        stage: Stage_Entry,
        stage_parameters: TaskParameters | None,
        stage_policies: Policy_Entry,
    ) -> None:
        """
        Updates subject history, which involves many steps.
        Stage parameters and policies are expected to be part
        of stage-- not checked here b/c this is a private utility.

        If any of {stage, stage_parameters, stage_policies} are None,
        all of the elements are expected to be None.
        """
        if not (
            stage is None or stage_parameters is None or stage_policies is None
        ):
            stage = stage.model_copy(deep=True)
            stage.set_task_parameters(stage_parameters)

        subject_history.add_entry(stage, stage_policies)
        self.write_data(s_id, curriculum, subject_history)

    def register_subject(
        self,
        subject_id: int,
        curriculum: Curriculum,
        start_stage: Stage,
        start_policies: Optional[Policy | list[Policy]] = None,
    ) -> None:
        """
        Adds subject into the Trainer system.
        If start_policies is None,
        registration defaults to the Stage.start_policies.
        """

        curriculum = curriculum.validate_curriculum()

        assert (
            start_stage in curriculum.see_stages()
        ), "Provided start_stage is not in provided curriculum."

        assert (
            subject_id not in self.subject_ids
        ), f"Subject_id {subject_id} is already registered."

        if start_policies is None:
            start_policies = start_stage.see_policies()
        elif isinstance(start_policies, Policy):
            start_policies = [start_policies]
        for s_policy in start_policies:
            assert s_policy in start_stage.see_policies(), (
                f"Provided start_policy {s_policy} not in "
                f"provided start_stage {start_stage.name}."
            )
        start_policies = tuple(start_policies)

        initial_params = self._get_net_parameter_update(
            start_stage.get_task_parameters(),
            start_policies,
            curr_metrics=Metrics(),  # Metrics is empty on regsitration.
        )
        self._update_subject_history(
            subject_id,
            curriculum,
            SubjectHistory(),  # Brand New History.
            start_stage,
            initial_params,
            start_policies,
        )

        # Add to trainer's local list!
        self.subject_ids.append(subject_id)

    def evaluate_subjects(self) -> None:  # noqa: C901
        """
        Calls user-defined functions to automatically update
        subject stage along curriculum.
        The timestep between evaluate_subject calls is flexible--
        this function will skip subject to the latest stage/policy
        they are applicable for.

        Evaluation checks for stage transitions before policy transitions.

        If subject does not satisfy any transition criteria,
        this method creates a duplicate current (stage, policy) entry
        in stage history.
        """

        # Added Edge Case:
        # 0) Subject has been ejected off-curriculum

        # Three Transition Cases:
        # 1) Stage transition: update stage history with
        #   both stage + policy and execute the policy

        # 2) Policy transition: update stage history with
        #   policy and execute the policy

        # 3) No transition: update stage history with
        #   current stage + policy

        for s_id in self.subject_ids:
            a, b, c = self.load_data(s_id)
            curriculum: Curriculum = a
            subject_history: SubjectHistory = b
            curr_metrics: Metrics = c
            current_stage, current_policies = subject_history.peek_last_entry()

            # 0) Subject Ejected
            if current_stage is None or current_policies is None:
                self._update_subject_history(
                    s_id, curriculum, subject_history, None, None, None
                )
                break  # Head to next subject

            # 1) Stage Transition
            advance_stage = False
            stage_transitions = curriculum.see_stage_transitions(current_stage)
            for stage_eval, dest_stage in stage_transitions:
                # On first true evaluation, update SubjectHistory
                # and publish back to database.
                if stage_eval.rule(curr_metrics):
                    # Publish updated stage and start polices
                    updated_params = self._get_net_parameter_update(
                        dest_stage.get_task_parameters(),
                        dest_stage.start_policies,
                        curr_metrics,
                    )
                    self._update_subject_history(
                        s_id,
                        curriculum,
                        subject_history,
                        dest_stage,
                        updated_params,
                        tuple(dest_stage.start_policies),
                    )
                    advance_stage = True
                    break  # Finish stage transition, onto next subject

            # 2) Policy Transition
            advance_policy = False
            if not advance_stage:
                # Buffer data structures to store result of active policy transitions.
                dest_policies: list[Policy] = []
                for active_policy in current_policies:
                    policy_transitions = current_stage.see_policy_transitions(
                        active_policy
                    )
                    for policy_eval, dest_policy in policy_transitions:
                        # On first true evaluation, add to buffers
                        # and evaluate next active_policy.
                        if policy_eval.rule(curr_metrics):
                            dest_policies.append(dest_policy)
                            advance_policy = True
                            break  # onto next active policy

                if len(dest_policies) != 0:
                    # Publish updated stage and unique dest_polices
                    updated_params = self._get_net_parameter_update(
                        current_stage.get_task_parameters(),
                        dest_policies,
                        curr_metrics,
                    )

                    dest_policies = self._get_unique_policies(dest_policies)
                    self._update_subject_history(
                        s_id,
                        curriculum,
                        subject_history,
                        current_stage,
                        updated_params,
                        tuple(dest_policies),
                    )

            # 3) No Transition
            if not (advance_stage or advance_policy):
                self._update_subject_history(
                    s_id,
                    curriculum,
                    subject_history,
                    current_stage,
                    current_stage.get_task_parameters(),
                    current_policies,
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
        assert (
            s_id in self.subject_ids
        ), f"subject id {s_id} not in self.subject_ids."

        a, b, c = self.load_data(s_id)
        curriculum: Curriculum = a
        subject_history: SubjectHistory = b
        curr_metrics: Metrics = c

        assert override_stage in curriculum.see_stages(), (
            f"override stage {override_stage.name} not in "
            f"curriculum stages for subject id {s_id}."
        )

        if isinstance(override_policies, Policy):
            override_policies = [override_policies]
        for o_policy in override_policies:
            assert o_policy in override_stage.see_policies(), (
                f"override policy {o_policy} not in "
                f"given override stage {override_stage.name}."
            )

        # Update Stage parameters according to override policies
        updated_params = self._get_net_parameter_update(
            override_stage.get_task_parameters(),
            override_policies,
            curr_metrics,
        )
        self._update_subject_history(
            s_id,
            curriculum,
            subject_history,
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

        a, b, c = self.load_data(s_id)
        curriculum: Curriculum = a
        subject_history: SubjectHistory = b
        curr_metrics: Metrics = c  # noqa: F841

        self._update_subject_history(
            s_id,
            curriculum,
            subject_history,
            stage=None,
            stage_parameters=None,
            stage_policies=None,
        )
