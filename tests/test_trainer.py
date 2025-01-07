"""
Trainer Test Suite
"""

import unittest

import example_project as ex
import example_project_2 as ex2

from aind_behavior_curriculum import GRADUATED, Stage, Trainer, TrainerState


class TrainerTests(unittest.TestCase):
    def test_pure_stage_evaluation(self):
        """
        Tests if multiple trajectories through stages
        are recorded correctly in database.
        """

        # Create Stage-only curriculum
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        taskB = ex.TaskB(task_parameters=ex.TaskBParameters())
        stageA = Stage(name="StageA", task=taskA)
        stageB = Stage(name="StageB", task=taskB)

        curr = ex.MyCurriculum(name="My Curriculum")
        curr.add_stage_transition(stageA, GRADUATED, ex.t2_10)
        curr.add_stage_transition(stageA, stageB, ex.t2_5)
        curr.add_stage_transition(stageB, GRADUATED, ex.t2_10)

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA)
        tr.register_subject(1, curr, stageA)
        tr.register_subject(2, curr, stageA)

        # Move mice through curriculum by updating metrics
        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_2=0)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_2=8)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_2=12)
        tr.evaluate_subjects()
        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_2=6)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_2=8)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_2=12)
        tr.evaluate_subjects()
        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_2=12)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_2=12)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_2=12)
        tr.evaluate_subjects()

        trainer = Trainer(curr)
        # Validate mouse histories
        M0 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[]),
            trainer.create_trainer_state(stage=stageA, active_policies=[]),
            trainer.create_trainer_state(stage=stageB, active_policies=[]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
        ]

        M1 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[]),
            trainer.create_trainer_state(stage=stageB, active_policies=[]),
            trainer.create_trainer_state(stage=stageB, active_policies=[]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
        ]

        M2 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
        ]

        self.assertEqual(tr.subject_history[0], M0)
        self.assertEqual(tr.subject_history[1], M1)
        self.assertEqual(tr.subject_history[2], M2)

    def test_pure_policy_evaluation(self):
        """
        Tests if multiple trajectories through policies
        are recorded correctly in database, including
        stage parameter changes by policy updates.
        """

        # Create single-stage curriculum
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = Stage(name="StageA", task=taskA)
        stageA.add_policy_transition(ex.INIT_STAGE, ex.stageA_policyB, ex.t1_10)
        stageA.add_policy_transition(ex.INIT_STAGE, ex.stageA_policyA, ex.t1_5)
        stageA.add_policy_transition(ex.stageA_policyA, ex.stageA_policyB, ex.t1_10)
        stageA.set_start_policies(ex.INIT_STAGE)

        stageAA = stageA.model_copy(deep=True)
        stageAA.set_task_parameters(ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters()))

        stageAAA = stageA.model_copy(deep=True)
        stageAAA.set_task_parameters(ex.stageA_policyB_rule(ex.ExampleMetrics(), ex.TaskAParameters()))

        curr = ex.MyCurriculum(name="My Curriculum")
        curr.add_stage(stageA)

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, ex.INIT_STAGE)
        tr.register_subject(1, curr, stageA, ex.INIT_STAGE)
        tr.register_subject(2, curr, stageA, ex.INIT_STAGE)

        # Move mice through curriculum by updating metrics
        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=0)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_1=8)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_1=12)
        tr.evaluate_subjects()

        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=6)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_1=8)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_1=12)
        tr.evaluate_subjects()

        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=12)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_1=12)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_1=12)
        tr.evaluate_subjects()

        trainer = Trainer(curr)
        # Validate mouse histories
        M0 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageAA, active_policies=[ex.stageA_policyA]),
            trainer.create_trainer_state(stage=stageAA, active_policies=[ex.stageA_policyB]),
        ]

        M1 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageAA, active_policies=[ex.stageA_policyA]),
            trainer.create_trainer_state(stage=stageAA, active_policies=[ex.stageA_policyA]),
            trainer.create_trainer_state(stage=stageAAA, active_policies=[ex.stageA_policyB]),
        ]

        M2 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageAAA, active_policies=[ex.stageA_policyB]),
            trainer.create_trainer_state(stage=stageAAA, active_policies=[ex.stageA_policyB]),
            trainer.create_trainer_state(stage=stageAAA, active_policies=[ex.stageA_policyB]),
        ]

        self.assertEqual(tr.subject_history[0], M0)
        self.assertEqual(tr.subject_history[1], M1)
        self.assertEqual(tr.subject_history[2], M2)

    def test_stage_policy_evaluation(self):
        """
        Tests if multiple trajectories through stages and policies
        are recorded correctly in database.
        """
        curr = ex.construct_curriculum()

        # See stages is ordered arbitrarily
        # StageA and StageB picked out from observation
        stageA = curr.see_stages()[0]
        stageB = curr.see_stages()[2]
        stageA.set_start_policies([ex.INIT_STAGE])
        stageB.set_start_policies([ex.INIT_STAGE])

        stageAA = stageA.model_copy(deep=True)
        stageAA.set_task_parameters(ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters()))
        stageAAA = stageA.model_copy(deep=True)
        stageAAA.set_task_parameters(ex.stageA_policyB_rule(ex.ExampleMetrics(), ex.TaskAParameters()))
        stageBB = stageB.model_copy(deep=True)

        stageBB.set_task_parameters(ex.stageB_policyA_rule(ex.ExampleMetrics(), ex.TaskBParameters()))
        stageBBB = stageB.model_copy(deep=True)
        stageBBB.set_task_parameters(ex.stageB_policyB_rule(ex.ExampleMetrics(), ex.TaskBParameters()))

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA)
        tr.register_subject(1, curr, stageA)
        tr.register_subject(2, curr, stageA)

        # Move mice through curriculum by updating metrics
        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=8)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_1=12)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_1=12)
        tr.evaluate_subjects()

        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_2=8)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_2=8)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_2=12)
        tr.evaluate_subjects()

        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_3=8)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_3=12)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_3=12)
        tr.evaluate_subjects()

        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_2=12)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_2=12)
        ex.MICE_METRICS[2] = ex.ExampleMetrics(theta_3=12)
        tr.evaluate_subjects()

        trainer = Trainer(curr)
        # Validate mouse histories
        M0 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageAA, active_policies=[ex.stageA_policyA]),
            trainer.create_trainer_state(stage=stageB, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageBB, active_policies=[ex.stageB_policyA]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
        ]

        M1 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageAAA, active_policies=[ex.stageA_policyB]),
            trainer.create_trainer_state(stage=stageB, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageBBB, active_policies=[ex.stageB_policyB]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
        ]

        M2 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageAAA, active_policies=[ex.stageA_policyB]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
        ]

        self.assertEqual(tr.subject_history[0], M0)
        self.assertEqual(tr.subject_history[1], M1)
        self.assertEqual(tr.subject_history[2], M2)

    def test_status_override(self):
        """
        Test if status override
        is recorded correctly in database.
        """

        curr = ex.construct_curriculum()

        # See stages is ordered arbitrarily
        # StageA and StageB picked out from observation
        stageA = curr.see_stages()[0]
        stageB = curr.see_stages()[2]

        stageAA = stageA.model_copy(deep=True)
        stageAA.set_task_parameters(ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters()))
        stageAAA = stageA.model_copy(deep=True)
        stageAAA.set_task_parameters(ex.stageA_policyB_rule(ex.ExampleMetrics(), ex.TaskAParameters()))
        stageBB = stageB.model_copy(deep=True)
        stageBB.set_task_parameters(ex.stageB_policyA_rule(ex.ExampleMetrics(), ex.TaskBParameters()))
        stageBBB = stageB.model_copy(deep=True)
        stageBBB.set_task_parameters(ex.stageB_policyB_rule(ex.ExampleMetrics(), ex.TaskBParameters()))

        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, ex.INIT_STAGE)

        # Override API
        tr.override_subject_status(0, override_stage=stageBB, override_policies=ex.stageB_policyA)
        tr.override_subject_status(0, override_stage=stageAAA, override_policies=ex.stageA_policyB)
        tr.override_subject_status(0, override_stage=GRADUATED, override_policies=())
        trainer = Trainer(curr)
        # Validate mouse history
        M0 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageBB, active_policies=[ex.stageB_policyA]),
            trainer.create_trainer_state(stage=stageAAA, active_policies=[ex.stageA_policyB]),
            trainer.create_trainer_state(stage=GRADUATED, active_policies=[]),
        ]

        self.assertEqual(tr.subject_history[0], M0)

    def test_floating_stages(self):
        """
        Test override between in-curriculum floating stages.
        Stages have no transitions, thus SubjectHistory should
        remain static until there is an override.
        """

        # Create Stage-only curriculum
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        taskB = ex.TaskB(task_parameters=ex.TaskBParameters())
        stageA = Stage(name="StageA", task=taskA)
        stageA.set_start_policies(ex.INIT_STAGE, append_non_existing=True)
        stageB = Stage(name="StageB", task=taskB)
        stageB.set_start_policies(ex.INIT_STAGE, append_non_existing=True)

        curr = ex.MyCurriculum(name="My Curriculum")
        curr.add_stage(stageA)
        curr.add_stage(stageB)

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, ex.INIT_STAGE)
        tr.register_subject(1, curr, stageB, ex.INIT_STAGE)

        # Regular evaluation logs same entry
        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=10, theta_2=10)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_1=10, theta_2=10)
        tr.evaluate_subjects()

        # Only way to move mouse is with override
        tr.override_subject_status(0, override_stage=stageB, override_policies=stageB.start_policies)
        tr.override_subject_status(1, override_stage=stageA, override_policies=stageA.start_policies)
        tr.override_subject_status(0, override_stage=stageA, override_policies=stageA.start_policies)
        tr.override_subject_status(1, override_stage=stageB, override_policies=stageB.start_policies)

        trainer = Trainer(curr)
        # Validate mouse history
        M0 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageB, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
        ]

        M1 = [
            trainer.create_trainer_state(stage=stageB, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageB, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageB, active_policies=[ex.INIT_STAGE]),
        ]

        self.assertEqual(tr.subject_history[0], M0)
        self.assertEqual(tr.subject_history[1], M1)

    def test_floating_policies(self):
        """
        Test policy override within a stage.
        Policies have no transitions, thus SubjectHistory should
        remain static until there is an override.
        """

        # Create single-stage curriculum
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = Stage(name="StageA", task=taskA)

        stageA.add_policy(ex.INIT_STAGE)
        stageA.add_policy(ex.stageA_policyA)
        stageA.add_policy(ex.stageA_policyB)
        stageA.set_start_policies(ex.INIT_STAGE)

        stageAA = stageA.model_copy(deep=True)
        stageAA.set_task_parameters(ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters()))
        stageAAA = stageA.model_copy(deep=True)
        stageAAA.set_task_parameters(ex.stageA_policyB_rule(ex.ExampleMetrics(), ex.TaskAParameters()))

        curr = ex.MyCurriculum(name="My Curriculum")
        curr.add_stage(stageA)

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, ex.INIT_STAGE)
        tr.register_subject(1, curr, stageA, ex.INIT_STAGE)

        # Regular evaluation logs same entry
        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=10, theta_2=10)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_1=10, theta_2=10)
        tr.evaluate_subjects()

        # Only way to move mouse is with override
        tr.override_subject_status(0, override_stage=stageA, override_policies=ex.stageA_policyA)
        tr.override_subject_status(1, override_stage=stageA, override_policies=ex.stageA_policyB)
        tr.override_subject_status(0, override_stage=stageA, override_policies=ex.stageA_policyB)
        tr.override_subject_status(1, override_stage=stageA, override_policies=ex.stageA_policyA)

        trainer = Trainer(curr)
        # Validate mouse history
        M0 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.stageA_policyA]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.stageA_policyB]),
        ]

        M1 = [
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.INIT_STAGE]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.stageA_policyB]),
            trainer.create_trainer_state(stage=stageA, active_policies=[ex.stageA_policyA]),
        ]

        self.assertEqual(tr.subject_history[0], M0)
        self.assertEqual(tr.subject_history[1], M1)

    def test_policy_tracks(self):
        """
        Tests multiple active policies along 2 policy tracks.
        Mouse occupies both tracks.
        """

        curr = ex2.construct_track_curriculum()
        track_stage = curr.see_stages()[0]

        # Create checkpoint stages
        dummy_task = ex2.DummyTask(task_parameters=ex2.DummyParameters())
        stage_init = Stage(name="Track Stage", task=dummy_task)
        stage_1 = Stage(name="Track Stage", task=dummy_task)
        stage_2 = Stage(name="Track Stage", task=dummy_task)
        stage_init.set_task_parameters(ex2.DummyParameters(field_1=5, field_2=5))
        stage_1.set_task_parameters(ex2.DummyParameters(field_1=10, field_2=10))
        stage_2.set_task_parameters(ex2.DummyParameters(field_1=15, field_2=15))

        # Associate mice with curriculum
        tr = ex2.ExampleTrainer()
        tr.register_subject(0, curr, track_stage, track_stage.start_policies)

        # Constant mouse metrics
        ex2.MICE_METRICS[0] = ex2.ExampleMetrics2(m1=10, m2=10)
        tr.evaluate_subjects()
        tr.evaluate_subjects()

        trainer = Trainer(curr)

        M0 = [
            trainer.create_trainer_state(
                stage=stage_init,
                active_policies=[
                    ex2.policy_1,
                    ex2.policy_4,
                ],
            ),
            trainer.create_trainer_state(
                stage=stage_1,
                active_policies=[
                    ex2.policy_2,
                    ex2.policy_5,
                ],
            ),
            trainer.create_trainer_state(
                stage=stage_2,
                active_policies=[
                    ex2.policy_3,
                    ex2.policy_6,
                ],
            ),
        ]

        self.assertEqual(tr.subject_history[0], M0)

    def test_policy_tree(self):
        """
        Tests multiple active policies along policy graph
        structured like a tree.
        Policies that transition into a common policy should
        only be logged once in the SubjectHistory.
        """

        curr = ex2.construct_tree_curriculum()
        tree_stage = curr.see_stages()[0]

        # Create checkpoint stages
        dummy_task = ex2.DummyTask(task_parameters=ex2.DummyParameters())
        stage_init = Stage(name="Tree Stage", task=dummy_task)
        stage_1 = Stage(name="Tree Stage", task=dummy_task)
        stage_2 = Stage(name="Tree Stage", task=dummy_task)
        stage_init.set_task_parameters(ex2.DummyParameters(field_1=15, field_2=0))
        stage_1.set_task_parameters(ex2.DummyParameters(field_1=15, field_2=10))
        stage_2.set_task_parameters(ex2.DummyParameters(field_1=15, field_2=15))

        # Associate mice with curriculum
        tr = ex2.ExampleTrainer()
        tr.register_subject(0, curr, tree_stage, tree_stage.start_policies)

        # Constant mouse metrics
        ex2.MICE_METRICS[0] = ex2.ExampleMetrics2(m1=10, m2=0)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        ex2.MICE_METRICS[0] = ex2.ExampleMetrics2(m1=10, m2=10)
        tr.evaluate_subjects()

        trainer = Trainer(curr)
        M0 = [
            trainer.create_trainer_state(
                stage=stage_init,
                active_policies=[
                    ex2.policy_1,
                    ex2.policy_2,
                    ex2.policy_3,
                ],
            ),
            trainer.create_trainer_state(
                stage=stage_1,
                active_policies=[
                    ex2.policy_4,
                    ex2.policy_5,
                ],
            ),
            trainer.create_trainer_state(
                stage=stage_1,
                active_policies=[
                    ex2.policy_4,
                    ex2.policy_5,
                ],
            ),
            trainer.create_trainer_state(stage=stage_2, active_policies=[ex2.policy_6]),
        ]

        self.assertEqual(tr.subject_history[0], M0)

    def test_policy_complete_graph(self):
        """
        Tests policy traversal through a complete graph of 3 policies.
        Policies traverse loop 'clockwise', then 'counterclockwise'.
        """

        curr = ex2.construct_policy_triangle_curriculum()
        triangle_stage = curr.see_stages()[0]

        # Create checkpoint stages
        dummy_task = ex2.DummyTask(task_parameters=ex2.DummyParameters())
        stage_init = Stage(name="Triangle Stage", task=dummy_task)
        stage_1 = Stage(name="Triangle Stage", task=dummy_task)
        stage_2 = Stage(name="Triangle Stage", task=dummy_task)
        stage_3 = Stage(name="Triangle Stage", task=dummy_task)
        stage_4 = Stage(name="Triangle Stage", task=dummy_task)
        stage_5 = Stage(name="Triangle Stage", task=dummy_task)
        stage_6 = Stage(name="Triangle Stage", task=dummy_task)
        stage_init.set_task_parameters(ex2.DummyParameters(field_1=5))
        stage_1.set_task_parameters(ex2.DummyParameters(field_1=10))
        stage_2.set_task_parameters(ex2.DummyParameters(field_1=15))
        stage_3.set_task_parameters(ex2.DummyParameters(field_1=20))
        stage_4.set_task_parameters(ex2.DummyParameters(field_1=25))
        stage_5.set_task_parameters(ex2.DummyParameters(field_1=30))
        stage_6.set_task_parameters(ex2.DummyParameters(field_1=35))

        # Associate mice with curriculum
        tr = ex2.ExampleTrainer()
        tr.register_subject(0, curr, triangle_stage, triangle_stage.start_policies)

        # Constant mouse metrics
        ex2.MICE_METRICS[0] = ex2.ExampleMetrics2(m1=10, m2=0)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        ex2.MICE_METRICS[0] = ex2.ExampleMetrics2(m1=0, m2=0)
        tr.evaluate_subjects()
        ex2.MICE_METRICS[0] = ex2.ExampleMetrics2(m1=0, m2=10)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        tr.evaluate_subjects()

        trainer = Trainer(curr)
        M0 = [
            trainer.create_trainer_state(stage=stage_init, active_policies=[ex2.policy_1]),
            trainer.create_trainer_state(stage=stage_1, active_policies=[ex2.policy_2]),
            trainer.create_trainer_state(stage=stage_2, active_policies=[ex2.policy_3]),
            # Return to start
            trainer.create_trainer_state(stage=stage_3, active_policies=[ex2.policy_1]),
            trainer.create_trainer_state(stage=stage_3, active_policies=[ex2.policy_1]),
            trainer.create_trainer_state(stage=stage_4, active_policies=[ex2.policy_3]),
            trainer.create_trainer_state(stage=stage_5, active_policies=[ex2.policy_2]),
            trainer.create_trainer_state(stage=stage_6, active_policies=[ex2.policy_1]),
        ]

        self.assertEqual(tr.subject_history[0], M0)

    def test_stage_complete_graph(self):
        """
        Tests stage traversal through a complete graph of 3 stages.
        Subject traverses loop 'clockwise', then 'counterclockwise'.
        """

        curr = ex2.construct_stage_triangle_curriculum()

        stage_1, stage_2, stage_3 = curr.see_stages()
        tr = ex2.ExampleTrainer()
        tr.register_subject(0, curr, stage_1, stage_1.start_policies)

        # Constant mouse metrics
        ex2.MICE_METRICS[0] = ex2.ExampleMetrics2(m1=10, m2=0)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        ex2.MICE_METRICS[0] = ex2.ExampleMetrics2(m1=0, m2=0)
        tr.evaluate_subjects()
        ex2.MICE_METRICS[0] = ex2.ExampleMetrics2(m1=0, m2=10)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        tr.evaluate_subjects()

        trainer = Trainer(curr)
        M0 = [
            trainer.create_trainer_state(stage=stage_1, active_policies=[]),
            trainer.create_trainer_state(stage=stage_2, active_policies=[]),
            trainer.create_trainer_state(stage=stage_3, active_policies=[]),
            trainer.create_trainer_state(stage=stage_1, active_policies=[]),  # Return to start
            trainer.create_trainer_state(stage=stage_1, active_policies=[]),
            trainer.create_trainer_state(stage=stage_3, active_policies=[]),
            trainer.create_trainer_state(stage=stage_2, active_policies=[]),
            trainer.create_trainer_state(stage=stage_1, active_policies=[]),
        ]

        self.assertEqual(tr.subject_history[0], M0)

    def test_eject_subject(self):
        """
        Tests if subject can be ejected and
        re-enrolled into curriculum with override.
        """
        curr = ex.construct_curriculum()

        # See stages is ordered arbitrarily
        # StageA and StageB picked out from observation
        stageA = curr.see_stages()[0]
        stageB = curr.see_stages()[2]

        stageAA = stageA.model_copy(deep=True)
        stageAA.set_task_parameters(ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters()))

        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, ex.INIT_STAGE)

        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=8)
        tr.evaluate_subjects()
        tr.eject_subject(0)
        tr.evaluate_subjects()
        tr.override_subject_status(0, override_stage=stageB, override_policies=stageB.start_policies)
        trainer = Trainer(curr)
        # Validate mouse history
        M0 = [
            trainer.create_trainer_state(
                stage=stageA,
                is_on_curriculum=True,
                active_policies=[ex.INIT_STAGE],
            ),
            trainer.create_trainer_state(
                stage=stageAA,
                is_on_curriculum=True,
                active_policies=[ex.stageA_policyA],
            ),
            trainer.create_trainer_state(stage=None, is_on_curriculum=False, active_policies=None),
            trainer.create_trainer_state(stage=None, is_on_curriculum=False, active_policies=None),
            trainer.create_trainer_state(stage=stageB, active_policies=[ex.INIT_STAGE]),
        ]
        self.assertEqual(tr.subject_history[0], M0)

    def test_round_trip_trainer_state(self):
        curr = ex.construct_curriculum()
        stageA = curr.see_stages()[0]

        ts = Trainer(curr).create_trainer_state(stage=stageA, active_policies=[ex.stageA_policyA])

        # Serialize from Child
        instance_json = ts.model_dump_json()
        # Deserialize from Child
        recovered = TrainerState.model_validate_json(instance_json)
        self.assertEqual(ts, recovered)


class TrainerStateTests(unittest.TestCase):
    def setUp(self):
        self.curr = ex.construct_curriculum()
        stageA = self.curr.see_stages()[0]
        active_policies = [ex.INIT_STAGE]

        self.state_from_trainer_state = TrainerState(
            curriculum=self.curr,
            stage=stageA,
            active_policies=active_policies,
            is_on_curriculum=True,
        )

        self.trainer = new_trainer = Trainer(curriculum=self.curr)
        self.state_from_trainer = new_trainer.create_trainer_state(
            stage=stageA,
            active_policies=active_policies,
            is_on_curriculum=True,
        )

    def test_trainer_state_is_equal(self):
        # This tests is a bit brittle as it relies on an implementation detail
        # of __eq__ of Stage I also dont think its super useful, so feel free
        # to remove it in the future if it causes problems
        self.assertEqual(self.state_from_trainer_state, self.state_from_trainer)

    def test_trainer_state_dict_is_equal(self):
        dump_from_trainer_state = self.state_from_trainer_state.model_dump()
        dump_from_trainer = self.state_from_trainer.model_dump()
        self.assertEqual(dump_from_trainer, dump_from_trainer_state)
        self.assertEqual(
            self.state_from_trainer_state.model_validate(dump_from_trainer_state),
            self.state_from_trainer.model_validate(dump_from_trainer_state),
        )
        self.assertEqual(
            self.state_from_trainer_state.model_validate(dump_from_trainer),
            self.state_from_trainer.model_validate(dump_from_trainer),
        )

    def test_trainer_state_json_is_equal(self):
        dump_from_trainer_state = self.state_from_trainer_state.model_dump_json()
        dump_from_trainer = self.state_from_trainer.model_dump_json()
        self.assertEqual(dump_from_trainer, dump_from_trainer_state)
        self.assertEqual(
            self.state_from_trainer_state.model_validate_json(dump_from_trainer_state),
            self.state_from_trainer.model_validate_json(dump_from_trainer_state),
        )
        self.assertEqual(
            self.state_from_trainer_state.model_validate_json(dump_from_trainer),
            self.state_from_trainer.model_validate_json(dump_from_trainer),
        )


if __name__ == "__main__":
    unittest.main()
