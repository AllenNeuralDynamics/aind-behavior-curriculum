"""
Core Trainer primitive.
"""

from abc import abstractmethod
from typing import Optional

from aind_behavior_curriculum import (
    AindBehaviorModel,
    Curriculum,
    Metrics,
    Policy,
    Stage,
    TaskParameters,
    validate_curriculum
)

class SubjectHistory(AindBehaviorModel):
    """
    Record of subject locations in Curriculum.
    Pydantic model for de/serialization.
    """

    stage_history: list[Stage]
    policy_history: list[tuple[Policy]]

    def add_entry(self, stage: Stage, policies: tuple[Policy]) -> None:
        """
        Add to stage and policy history synchronously.
        """
        self.stage_history.append(stage)
        self.policy_history.append(policies)

    def peek_last_entry(self) -> tuple[Stage, tuple[Policy]]:
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
    3) Call Trainer.evaluate_subject() or
            Trainer.override_subject_status() x N
    """

    def __init__(self):
        """
        Trainer manages a list of subjects initalized here.
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

    def register_subject(
        self,
        subject_id: int,
        curriculum: Curriculum,
        start_stage: Stage,
        start_policies: Optional[list[Policy]] = None,
    ):
        """
        Adds subject into the Trainer system.
        If start_policies is None,
        registration defaults to the Stage.start_policies.
        """

        curriculum = validate_curriculum(curriculum)

        assert (
            start_stage in curriculum.see_stages()
        ), "Provided start_stage is not in provided curriculum."

        assert (
            subject_id not in self.subject_ids
        ), f"Subject_id {subject_id} is already registered."

        if not (start_policies is None):
            for s_policy in start_policies:
                assert (
                    s_policy in start_stage.see_policies()
                ), f"Provided start_policy {s_policy} not in \
                    provided start_stage {start_stage}."

        new_history = SubjectHistory()
        if start_policies is None:
            new_history.add_entry(
                start_stage, tuple(start_stage.start_policies)
            )
            self.write_data(subject_id, curriculum, new_history)
        else:
            new_history.add_entry(start_stage, tuple(start_policies))
            self.write_data(subject_id, curriculum, new_history)
        self.subject_ids.append(subject_id)

    def _get_net_parameter_update(
        stage_parameters: TaskParameters,
        stage_policies: list[Policy],
        curr_metrics: Metrics
        ) -> TaskParameters:
        """
        Aggregates parameter update of input stage_policies
        given current stage_parameters and current metrics.
        """

        param_updates: list[TaskParameters] = []
        for init_policy in stage_policies:
            updated_params = init_policy.rule(
                curr_metrics, stage_parameters
            )
            param_updates.append(updated_params)

        # Merge Parameter Updates
        task_parameters_subtype = type(stage_parameters)
        merged_params = {}
        for params in param_updates:
            merged_params = {**merged_params, **dict(params)}
        updated_params = task_parameters_subtype(merged_params)

        return updated_params

    def evaluate_subjects(self):  # noqa: C901
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
                        curr_metrics
                    )
                    dest_stage = dest_stage.model_copy(deep=True)
                    dest_stage.set_task_parameters(updated_params)
                    subject_history.add_entry(
                        dest_stage, tuple(dest_stage.start_policies)
                    )
                    self.write_data(s_id, curriculum, subject_history)
                    advance_stage = True
                    break

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
                            break

                if len(dest_policies) != 0:
                    # Publish updated stage and unique dest_polices
                    updated_params = self._get_net_parameter_update(
                        current_stage.get_task_parameters(),
                        dest_policies,
                        curr_metrics
                    )
                    current_stage = current_stage.model_copy(deep=True)
                    current_stage.set_task_parameters(updated_params)
                    subject_history.add_entry(
                        current_stage, tuple(set(dest_policies))
                    )
                    self.write_data(s_id, curriculum, subject_history)

            # 3) No Transition
            if not (advance_stage or advance_policy):
                current_stage = current_stage.model_copy(deep=True)
                subject_history.add_entry(current_stage, current_policies)
                self.write_data(s_id, curriculum, subject_history)

    def override_subject_status(
        self, s_id: int, override_stage: Stage, override_policies: list[Policy]
    ):
        """
        Override subject (stage, policies) independent of evaluation.
        Stage and Policy objects may be accessed by calling
        Trainer.load_data and looking inside of the returned Curriculum.
        """
        assert (
            s_id in self.subject_ids
        ), f"subject id {s_id} not in self.subject_ids."

        a, b, c = self.load_data(s_id)
        curriculum: Curriculum = a
        subject_history: SubjectHistory = b
        curr_metrics: Metrics = c

        assert (
            override_stage in curriculum.see_stages()
        ), f"override stage {override_stage} not in \
            curriculum stages for subject id {s_id}."

        for o_policy in override_policies:
            assert (
                o_policy in override_stage.see_policies()
            ), f"override policy {o_policy} not in \
            given override stage {override_stage}."

        # Update Stage parameters according to override policies
        updated_params = self._get_net_parameter_update(
            override_stage.get_task_parameters(),
            override_policies,
            curr_metrics
        )
        override_stage = override_stage.model_copy(deep=True)
        override_stage.set_task_parameters(updated_params)
        subject_history.add_entry(override_stage, tuple(override_policies))
        self.write_data(s_id, curriculum, subject_history)
