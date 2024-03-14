from abc import abstractmethod

from typing import Optional

import aind_behavior_curriculum as abc


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
    ) -> tuple[
        abc.Curriculum, list[tuple[abc.Stage, abc.Policy]], abc.Metrics
    ]:
        """
        User-defined.
        Loads 3 pieces of data in the following format:
        - subject Curriculum
        - List of (Stage History, Policy) Tuples
        - subject Metrics
        """
        raise NotImplementedError

    @abstractmethod
    def write_data(
        self,
        subject_id: int,
        curriculum: abc.Curriculum,
        history: list[tuple[abc.Stage, abc.Policy]],
    ) -> None:
        """
        User-defined.
        Exports 3 pieces of data to database.
        - subject Id
        - subject Curriculum
        - List of (Stage History, Policy) Tuples

        For Curriculums with no internal policies, insert tacit abc.INIT_STAGE
        """
        raise NotImplementedError


    def register_subject(self,
                         subject_id: int,
                         curriculum: abc.Curriculum,
                         start_stage: abc.Stage,
                         start_policy: Optional[abc.Policy] = abc.INIT_STAGE):
        """
        Adds subject into the Trainer system.
        """

        assert start_stage in curriculum.stages.values(), \
            "Provided start_stage is not in provided curriculum."

        if len(start_stage.policies) > 0:
            assert start_policy in start_stage.policies.values(), \
                "Provided start_policy is not in provided stage_stage."

        assert subject_id not in self.subject_ids, \
            f"Subject_id {subject_id} is already registered."

        self.subject_ids.append(subject_id)
        self.write_data(subject_id,
                        curriculum,
                        history=[(start_stage, start_policy)])

    def evaluate_subject(self):
        """
        Calls user-defined functions to automatically update
        subject stage along curriculum.
        The timestep between evaluate_subject calls is flexible--
        this function will skip subject to the latest stage/policy
        they are applicable for.
        """

        # Two notions of transitions:
        # 1) Stage transition: update stage history with
        #   both stage + policy and execute the policy

        # 2) Policy transition: update stage history with
        #   policy and execute the policy
        for s_id in self.subject_ids:
            a, b, c = self.load_data(s_id)
            curriculum: abc.Curriculum = a
            stage_history: list[tuple[abc.Stage, abc.Policy]] = b
            curr_metrics: abc.Metrics = c

            current_stage, _ = stage_history[-1]
            # 1) Stage Transition
            advance_stage = False
            stage_transitions = curriculum.see_stage_transitions(current_stage)
            for stage_eval, dest_stage in stage_transitions:
                # On first true evaluation, update stage history
                # and publish back to database.
                if stage_eval(curr_metrics):
                    # Trainer.write_data requires that every stage will have an init policy
                    # as stage_history can only store (stage, policy) tuples.
                    dest_policy = dest_stage.see_policies()[0]
                    updated_params = dest_policy(
                        curr_metrics, dest_stage.get_task_parameters()
                    )
                    dest_stage.set_task_parameters(updated_params)
                    stage_history.append(dest_stage, dest_policy)

                    self.write_data(s_id, curriculum, stage_history)
                    advance_stage = True
                    break

            # 2) Policy Transition
            if not advance_stage:
                policy_transitions = current_stage.see_policy_transitions()
                for policy_eval, dest_policy in policy_transitions:
                    # On first true evaluation, update stage history
                    # and publish back to database.
                    if policy_eval(curr_metrics):
                        updated_params = dest_policy(
                            curr_metrics, dest_stage.get_task_parameters()
                        )
                        dest_stage.set_task_parameters(updated_params)
                        stage_history.append(dest_stage, dest_policy)

                        self.write_data(s_id, curriculum, stage_history)

    def override_subject_status(
        self, s_id: int, override_stage: abc.Stage, override_policy: abc.Policy
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
        curriculum: abc.Curriculum = a
        stage_history: list[tuple[abc.Stage, abc.Policy]] = b
        curr_metrics: abc.Metrics = c

        assert (
            override_stage in curriculum.see_stages()
        ), f"override stage {override_stage} not in curriculum stages for subject id {s_id}."

        assert (
            override_policy in override_stage.see_policies()
        ), f"override policy {override_policy} not in given override stage {override_stage}."

        stage_history.append((override_stage, override_policy))
        self.write_data(s_id, curriculum, stage_history)

    def export_visual(self):
        """
        Export visual representation of curriculum to inspect status.
        """

        # TODO

class S(Trainer):
    def __init__(self):
        super().__init__()