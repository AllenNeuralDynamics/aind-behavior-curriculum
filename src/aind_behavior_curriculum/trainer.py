"""
Core Trainer primitive.
"""

from abc import abstractmethod

from aind_behavior_curriculum import Curriculum, Metrics, Policy, Stage


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
    ) -> tuple[Curriculum, list[tuple[Stage, Policy]], Metrics]:
        """
        User-defined.
        Loads 3 pieces of data in the following format:
        - subject Curriculum
        - List of (Stage, Policy) tuples recording subject history
        - subject Metrics
        """
        raise NotImplementedError

    @abstractmethod
    def write_data(
        self,
        subject_id: int,
        curriculum: Curriculum,
        history: list[tuple[Stage, Policy]],
    ) -> None:
        """
        User-defined.
        Exports 3 pieces of data to database.
        - subject Id
        - subject Curriculum
        - List of (Stage, Policy) tuples recording subject history

        For Curriculums with no internal policies, insert tacit INIT_STAGE
        """
        raise NotImplementedError

    def register_subject(
        self,
        subject_id: int,
        curriculum: Curriculum,
        start_stage: Stage,
        start_policy: Policy,
    ):
        """
        Adds subject into the Trainer system.
        """

        assert (
            start_stage in curriculum.stages.values()
        ), "Provided start_stage is not in provided curriculum."

        assert (
            start_policy in start_stage.policies.values()
        ), "Provided start_policy is not in provided stage_stage."

        assert (
            subject_id not in self.subject_ids
        ), f"Subject_id {subject_id} is already registered."

        self.subject_ids.append(subject_id)
        self.write_data(
            subject_id, curriculum, history=[(start_stage, start_policy)]
        )

    def evaluate_subjects(self):
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
            stage_history: list[tuple[Stage, Policy]] = b
            curr_metrics: Metrics = c
            current_stage, current_policy = stage_history[-1]

            # 1) Stage Transition
            advance_stage = False
            stage_transitions = curriculum.see_stage_transitions(current_stage)
            for stage_eval, dest_stage in stage_transitions:
                # On first true evaluation, update stage history
                # and publish back to database.
                if stage_eval.rule(curr_metrics):
                    # Trainer.write_data requires that every stage
                    # will have an init policy as stage_history
                    # can only store (stage, policy) tuples.
                    dest_policy = dest_stage.see_policies()[0]

                    updated_params = dest_policy.rule(
                        curr_metrics, dest_stage.get_task_parameters()
                    )
                    dest_stage = dest_stage.model_copy(deep=True)
                    dest_stage.set_task_parameters(updated_params)
                    stage_history.append((dest_stage, dest_policy))

                    self.write_data(s_id, curriculum, stage_history)
                    advance_stage = True
                    break

            # 2) Policy Transition
            advance_policy = False
            if not advance_stage:
                policy_transitions = current_stage.see_policy_transitions(
                    current_policy
                )
                for policy_eval, dest_policy in policy_transitions:
                    # On first true evaluation, update stage history
                    # and publish back to database.
                    if policy_eval.rule(curr_metrics):

                        updated_params = dest_policy.rule(
                            curr_metrics, current_stage.get_task_parameters()
                        )
                        current_stage = current_stage.model_copy(deep=True)
                        current_stage.set_task_parameters(updated_params)
                        stage_history.append((current_stage, dest_policy))

                        self.write_data(s_id, curriculum, stage_history)
                        advance_policy = True
                        break

            # 3) No Transition
            if not (advance_stage or advance_policy):

                current_stage = current_stage.model_copy(deep=True)
                stage_history.append((current_stage, current_policy))
                self.write_data(s_id, curriculum, stage_history)

    def override_subject_status(
        self, s_id: int, override_stage: Stage, override_policy: Policy
    ):
        """
        Override subject (stage, policy) independent of evaluation.
        Stage and Policy objects may be accessed by calling
        Trainer.load_data and looking inside of the returned Curriculum.
        """
        assert (
            s_id in self.subject_ids
        ), f"subject id {s_id} not in self.subject_ids."

        a, b, c = self.load_data(s_id)
        curriculum: Curriculum = a
        stage_history: list[tuple[Stage, Policy]] = b
        curr_metrics: Metrics = c  # noqa: F841

        assert (
            override_stage in curriculum.see_stages()
        ), f"override stage {override_stage} not in \
            curriculum stages for subject id {s_id}."

        assert (
            override_policy in override_stage.see_policies()
        ), f"override policy {override_policy} not in \
           given override stage {override_stage}."

        stage_history.append((override_stage, override_policy))
        self.write_data(s_id, curriculum, stage_history)

    def export_visual(self):
        """
        Export visual representation of curriculum to inspect status.
        """

        # TODO
