from abc import abstractmethod

import aind_behavior_curriculum as abc


class Trainer:
    """
    Pulls mouse curriculum and history,
    and performs fundamental curriculum evaluation/update.
    """

    @abstractmethod
    def load_data(self,
                  mouse_id: int
                  ) -> tuple[abc.Curriculum,
                             list[tuple[abc.Stage, abc.Policy]],
                             abc.Metrics]:
        """
        User-defined.
        Loads 3 pieces of data in the following format:
        - Mouse Curriculum
        - List of (Stage History, Policy) Tuples
        - Mouse Metrics
        """
        raise NotImplementedError

    @abstractmethod
    def write_data(self,
                   mouse_id: int,
                   curriculum: abc.Curriculum,
                   history: list[tuple[abc.Stage, abc.Policy]],
                   ) -> None:
        """
        User-defined.
        Exports 3 pieces of data to database.
        - Mouse Id
        - Mouse Curriculum
        - List of (Stage History, Policy) Tuples

        For Curriculums with no internal policies, insert tacit abc.INIT_STAGE
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def mouse_ids(self) -> list[int]:
        """
        User-defined.
        Returns list of mouse ids that this Trainer is managing.
        """
        raise NotImplementedError

    def evaluate_mice(self):
        """
        Calls user-defined functions to automatically update
        mouse stage along curriculum.
        The timestep between evaluate_mice calls is flexible--
        this function will skip mice to the latest stage/policy
        they are applicable for.
        """

        # Two notions of transitions:
        # 1) Stage transition: update stage history with
        #   both stage + policy and execute the policy

        # 2) Policy transition: update stage history with
        #   policy and execute the policy
        for m_id in self.mouse_ids:
            a, b, c = self.load_data(m_id)
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
                    updated_params = dest_policy(curr_metrics,
                                                 dest_stage.get_task_parameters())
                    dest_stage.set_task_parameters(updated_params)
                    stage_history.append(dest_stage, dest_policy)

                    self.write_data(m_id, curriculum, stage_history)
                    advance_stage = True
                    break

            # 2) Policy Transition
            if not advance_stage:
                policy_transitions = current_stage.see_policy_transitions()
                for policy_eval, dest_policy in policy_transitions:
                    # On first true evaluation, update stage history
                    # and publish back to database.
                    if policy_eval(curr_metrics):
                        updated_params = dest_policy(curr_metrics,
                                                     dest_stage.get_task_parameters())
                        dest_stage.set_task_parameters(updated_params)
                        stage_history.append(dest_stage, dest_policy)

                        self.write_data(m_id, curriculum, stage_history)

    def override_mouse_status(self,
                              m_id: int,
                              override_stage: abc.Stage,
                              override_policy: abc.Policy):
        """
        Override mouse (stage, policy) independent of evaluation.
        Stage and Policy objects may be accessed by calling
        Trainer.load_data and looking inside of the returned Curriculum.
        """
        assert m_id in self.mouse_ids, \
            f'mouse id {m_id} not in self.mouse_ids.'

        a, b, c = self.load_data(m_id)
        curriculum: abc.Curriculum = a
        stage_history: list[tuple[abc.Stage, abc.Policy]] = b
        curr_metrics: abc.Metrics = c

        assert override_stage in curriculum.see_stages(), \
            f'override stage {override_stage} not in curriculum stages for mouse id {m_id}.'

        assert override_policy in override_stage.see_policies(), \
            f'override policy {override_policy} not in given override stage {override_stage}.'

        stage_history.append((override_stage, override_policy))
        self.write_data(m_id, curriculum, stage_history)

    def export_visual(self):
        """
        Export visual representation of curriculum to inspect status.
        """

        # TODO