"""
Trainer Test Suite
"""

import unittest

import example_project as ex
import example_project_2 as ex2

from aind_behavior_curriculum import (
    GRADUATED,
    INIT_STAGE,
    Stage,
    SubjectHistory,
    create_empty_stage,
)


class TrainerTests(unittest.TestCase):

    def test_pure_stage_evaluation(self):
        """
        Tests if multiple trajectories through stages
        are recorded correctly in database.
        """

        # Create Stage-only curriculum
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        taskB = ex.TaskB(task_parameters=ex.TaskBParameters())
        stageA = create_empty_stage(Stage(name="StageA", task=taskA))
        stageB = create_empty_stage(Stage(name="StageB", task=taskB))

        curr = ex.MyCurriculum(name="My Curriculum")
        curr.add_stage_transition(stageA, GRADUATED, ex.t2_10)
        curr.add_stage_transition(stageA, stageB, ex.t2_5)
        curr.add_stage_transition(stageB, GRADUATED, ex.t2_10)

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, INIT_STAGE)
        tr.register_subject(1, curr, stageA, INIT_STAGE)
        tr.register_subject(2, curr, stageA, INIT_STAGE)

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

        # Validate mouse histories
        M0 = SubjectHistory(
            stage_history=[stageA, stageA, stageB, GRADUATED],
            policy_history=[
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
            ],
        )

        M1 = SubjectHistory(
            stage_history=[stageA, stageB, stageB, GRADUATED],
            policy_history=[
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
            ],
        )

        M2 = SubjectHistory(
            stage_history=[stageA, GRADUATED, GRADUATED, GRADUATED],
            policy_history=[
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
            ],
        )

        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[1] == M1)
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[2] == M2)

        # Reset database
        tr.clear_database()

    def test_pure_policy_evaluation(self):
        """
        Tests if multiple trajectories through policies
        are recorded correctly in database, including
        stage parameter changes by policy updates.
        """

        # Create single-stage curriculum
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = Stage(name="StageA", task=taskA)
        stageA.add_policy_transition(INIT_STAGE, ex.stageA_policyB, ex.t1_10)
        stageA.add_policy_transition(INIT_STAGE, ex.stageA_policyA, ex.t1_5)
        stageA.add_policy_transition(
            ex.stageA_policyA, ex.stageA_policyB, ex.t1_10
        )
        stageA.set_start_policies(INIT_STAGE)

        stageAA = stageA.model_copy(deep=True)
        stageAA.set_task_parameters(
            ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters())
        )

        stageAAA = stageA.model_copy(deep=True)
        stageAAA.set_task_parameters(
            ex.stageA_policyB_rule(ex.ExampleMetrics(), ex.TaskAParameters())
        )

        curr = ex.MyCurriculum(name="My Curriculum")
        curr.add_stage(stageA)

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, INIT_STAGE)
        tr.register_subject(1, curr, stageA, INIT_STAGE)
        tr.register_subject(2, curr, stageA, INIT_STAGE)

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

        # Validate mouse histories
        M0 = SubjectHistory(
            stage_history=[stageA, stageA, stageAA, stageAAA],
            policy_history=[
                (INIT_STAGE,),
                (INIT_STAGE,),
                (ex.stageA_policyA,),
                (ex.stageA_policyB,),
            ],
        )

        M1 = SubjectHistory(
            stage_history=[stageA, stageAA, stageAA, stageAAA],
            policy_history=[
                (INIT_STAGE,),
                (ex.stageA_policyA,),
                (ex.stageA_policyA,),
                (ex.stageA_policyB,),
            ],
        )

        M2 = SubjectHistory(
            stage_history=[stageA, stageAAA, stageAAA, stageAAA],
            policy_history=[
                (INIT_STAGE,),
                (ex.stageA_policyB,),
                (ex.stageA_policyB,),
                (ex.stageA_policyB,),
            ],
        )

        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[1] == M1)
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[2] == M2)

        # Reset database
        tr.clear_database()

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

        stageAA = stageA.model_copy(deep=True)
        stageAA.set_task_parameters(
            ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters())
        )
        stageAAA = stageA.model_copy(deep=True)
        stageAAA.set_task_parameters(
            ex.stageA_policyB_rule(ex.ExampleMetrics(), ex.TaskAParameters())
        )
        stageBB = stageB.model_copy(deep=True)
        stageBB.set_task_parameters(
            ex.stageB_policyA_rule(ex.ExampleMetrics(), ex.TaskBParameters())
        )
        stageBBB = stageB.model_copy(deep=True)
        stageBBB.set_task_parameters(
            ex.stageB_policyB_rule(ex.ExampleMetrics(), ex.TaskBParameters())
        )

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, INIT_STAGE)
        tr.register_subject(1, curr, stageA, INIT_STAGE)
        tr.register_subject(2, curr, stageA, INIT_STAGE)

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

        # Validate mouse histories
        M0 = SubjectHistory(
            stage_history=[stageA, stageAA, stageB, stageBB, GRADUATED],
            policy_history=[
                (INIT_STAGE,),
                (ex.stageA_policyA,),
                (INIT_STAGE,),
                (ex.stageB_policyA,),
                (INIT_STAGE,),
            ],
        )

        M1 = SubjectHistory(
            stage_history=[stageA, stageAAA, stageB, stageBBB, GRADUATED],
            policy_history=[
                (INIT_STAGE,),
                (ex.stageA_policyB,),
                (INIT_STAGE,),
                (ex.stageB_policyB,),
                (INIT_STAGE,),
            ],
        )

        M2 = SubjectHistory(
            stage_history=[stageA, stageAAA, GRADUATED, GRADUATED, GRADUATED],
            policy_history=[
                (INIT_STAGE,),
                (ex.stageA_policyB,),
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
            ],
        )

        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[1] == M1)
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[2] == M2)

        # Reset database
        tr.clear_database()

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
        stageAA.set_task_parameters(
            ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters())
        )
        stageAAA = stageA.model_copy(deep=True)
        stageAAA.set_task_parameters(
            ex.stageA_policyB_rule(ex.ExampleMetrics(), ex.TaskAParameters())
        )
        stageBB = stageB.model_copy(deep=True)
        stageBB.set_task_parameters(
            ex.stageB_policyA_rule(ex.ExampleMetrics(), ex.TaskBParameters())
        )
        stageBBB = stageB.model_copy(deep=True)
        stageBBB.set_task_parameters(
            ex.stageB_policyB_rule(ex.ExampleMetrics(), ex.TaskBParameters())
        )

        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, INIT_STAGE)

        # Override API
        tr.override_subject_status(
            0, override_stage=stageBB, override_policies=ex.stageB_policyA
        )
        tr.override_subject_status(
            0, override_stage=stageAAA, override_policies=ex.stageA_policyB
        )
        tr.override_subject_status(
            0, override_stage=GRADUATED, override_policies=INIT_STAGE
        )

        # Validate mouse history
        M0 = SubjectHistory(
            stage_history=[stageA, stageBB, stageAAA, GRADUATED],
            policy_history=[
                (INIT_STAGE,),
                (ex.stageB_policyA,),
                (ex.stageA_policyB,),
                (INIT_STAGE,),
            ],
        )
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)

        # Reset database
        tr.clear_database()

    def test_floating_stages(self):
        """
        Test override between in-curriculum floating stages.
        Stages have no transitions, thus SubjectHistory should
        remain static until there is an override.
        """

        # Create Stage-only curriculum
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        taskB = ex.TaskB(task_parameters=ex.TaskBParameters())
        stageA = create_empty_stage(Stage(name="StageA", task=taskA))
        stageB = create_empty_stage(Stage(name="StageB", task=taskB))

        curr = ex.MyCurriculum(name="My Curriculum")
        curr.add_stage(stageA)
        curr.add_stage(stageB)

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, INIT_STAGE)
        tr.register_subject(1, curr, stageB, INIT_STAGE)

        # Regular evaluation logs same entry
        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=10, theta_2=10)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_1=10, theta_2=10)
        tr.evaluate_subjects()

        # Only way to move mouse is with override
        tr.override_subject_status(
            0, override_stage=stageB, override_policies=stageB.start_policies
        )
        tr.override_subject_status(
            1, override_stage=stageA, override_policies=stageA.start_policies
        )
        tr.override_subject_status(
            0, override_stage=stageA, override_policies=stageA.start_policies
        )
        tr.override_subject_status(
            1, override_stage=stageB, override_policies=stageB.start_policies
        )

        # Validate mouse history
        M0 = SubjectHistory(
            stage_history=[stageA, stageA, stageB, stageA],
            policy_history=[
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
            ],
        )

        M1 = SubjectHistory(
            stage_history=[stageB, stageB, stageA, stageB],
            policy_history=[
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
            ],
        )

        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[1] == M1)

        # Reset database
        tr.clear_database()

    def test_floating_policies(self):
        """
        Test policy override within a stage.
        Policies have no transitions, thus SubjectHistory should
        remain static until there is an override.
        """

        # Create single-stage curriculum
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        stageA = Stage(name="StageA", task=taskA)

        stageA.add_policy(INIT_STAGE)
        stageA.add_policy(ex.stageA_policyA)
        stageA.add_policy(ex.stageA_policyB)
        stageA.set_start_policies(INIT_STAGE)

        stageAA = stageA.model_copy(deep=True)
        stageAA.set_task_parameters(
            ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters())
        )
        stageAAA = stageA.model_copy(deep=True)
        stageAAA.set_task_parameters(
            ex.stageA_policyB_rule(ex.ExampleMetrics(), ex.TaskAParameters())
        )

        curr = ex.MyCurriculum(name="My Curriculum")
        curr.add_stage(stageA)

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, INIT_STAGE)
        tr.register_subject(1, curr, stageA, INIT_STAGE)

        # Regular evaluation logs same entry
        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=10, theta_2=10)
        ex.MICE_METRICS[1] = ex.ExampleMetrics(theta_1=10, theta_2=10)
        tr.evaluate_subjects()

        # Only way to move mouse is with override
        tr.override_subject_status(
            0, override_stage=stageA, override_policies=ex.stageA_policyA
        )
        tr.override_subject_status(
            1, override_stage=stageA, override_policies=ex.stageA_policyB
        )
        tr.override_subject_status(
            0, override_stage=stageA, override_policies=ex.stageA_policyB
        )
        tr.override_subject_status(
            1, override_stage=stageA, override_policies=ex.stageA_policyA
        )

        # Validate mouse history
        M0 = SubjectHistory(
            stage_history=[stageA, stageA, stageA, stageA],
            policy_history=[
                (INIT_STAGE,),
                (INIT_STAGE,),
                (ex.stageA_policyA,),
                (ex.stageA_policyB,),
            ],
        )

        M1 = SubjectHistory(
            stage_history=[stageA, stageA, stageA, stageA],
            policy_history=[
                (INIT_STAGE,),
                (INIT_STAGE,),
                (ex.stageA_policyB,),
                (ex.stageA_policyA,),
            ],
        )

        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[1] == M1)

        # Reset database
        tr.clear_database()

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
        stage_init.set_task_parameters(
            ex2.DummyParameters(field_1=5, field_2=5)
        )
        stage_1.set_task_parameters(
            ex2.DummyParameters(field_1=10, field_2=10)
        )
        stage_2.set_task_parameters(
            ex2.DummyParameters(field_1=15, field_2=15)
        )

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, track_stage, track_stage.start_policies)

        # Constant mouse metrics
        ex.MICE_METRICS[0] = ex.ExampleMetrics(m1=10, m2=10)
        tr.evaluate_subjects()
        tr.evaluate_subjects()

        M0 = SubjectHistory(
            stage_history=[stage_init, stage_1, stage_2],
            policy_history=[
                (ex2.policy_1, ex2.policy_4),
                (ex2.policy_2, ex2.policy_5),
                (ex2.policy_3, ex2.policy_6),
            ],
        )

        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)

        # Reset database
        tr.clear_database()

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
        stage_init.set_task_parameters(
            ex2.DummyParameters(field_1=15, field_2=0)
        )
        stage_1.set_task_parameters(
            ex2.DummyParameters(field_1=15, field_2=10)
        )
        stage_2.set_task_parameters(
            ex2.DummyParameters(field_1=15, field_2=15)
        )

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, tree_stage, tree_stage.start_policies)

        # Constant mouse metrics
        ex.MICE_METRICS[0] = ex.ExampleMetrics(m1=10, m2=0)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        ex.MICE_METRICS[0] = ex.ExampleMetrics(m1=10, m2=10)
        tr.evaluate_subjects()

        M0 = SubjectHistory(
            stage_history=[stage_init, stage_1, stage_1, stage_2],
            policy_history=[
                (ex2.policy_1, ex2.policy_2, ex2.policy_3),
                (ex2.policy_4, ex2.policy_5),
                (ex2.policy_4, ex2.policy_5),
                (ex2.policy_6,),
            ],
        )

        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)

        # Reset database
        tr.clear_database()

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
        tr = ex.ExampleTrainer()
        tr.register_subject(
            0, curr, triangle_stage, triangle_stage.start_policies
        )

        # Constant mouse metrics
        ex.MICE_METRICS[0] = ex.ExampleMetrics(m1=10, m2=0)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        ex.MICE_METRICS[0] = ex.ExampleMetrics(m1=0, m2=0)
        tr.evaluate_subjects()
        ex.MICE_METRICS[0] = ex.ExampleMetrics(m1=0, m2=10)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        tr.evaluate_subjects()

        M0 = SubjectHistory(
            stage_history=[
                stage_init,
                stage_1,
                stage_2,
                stage_3,
                stage_3,
                stage_4,
                stage_5,
                stage_6,
            ],
            policy_history=[
                (ex2.policy_1,),
                (ex2.policy_2,),
                (ex2.policy_3,),
                (ex2.policy_1,),  # Return to start
                (ex2.policy_1,),
                (ex2.policy_3,),
                (ex2.policy_2,),
                (ex2.policy_1,),
            ],
        )

        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)

        # Reset database
        tr.clear_database()

    def test_stage_complete_graph(self):
        """
        Tests stage traversal through a complete graph of 3 stages.
        Subject traverses loop 'clockwise', then 'counterclockwise'.
        """

        curr = ex2.construct_stage_triangle_curriculum()

        stage_1, stage_2, stage_3 = curr.see_stages()
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stage_1, stage_1.start_policies)

        # Constant mouse metrics
        ex.MICE_METRICS[0] = ex.ExampleMetrics(m1=10, m2=0)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        ex.MICE_METRICS[0] = ex.ExampleMetrics(m1=0, m2=0)
        tr.evaluate_subjects()
        ex.MICE_METRICS[0] = ex.ExampleMetrics(m1=0, m2=10)
        tr.evaluate_subjects()
        tr.evaluate_subjects()
        tr.evaluate_subjects()

        M0 = SubjectHistory(
            stage_history=[
                stage_1,
                stage_2,
                stage_3,
                stage_1,
                stage_1,
                stage_3,
                stage_2,
                stage_1,
            ],
            policy_history=[
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),  # Return to start
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
                (INIT_STAGE,),
            ],
        )

        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)

        # Reset database
        tr.clear_database()

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
        stageAA.set_task_parameters(
            ex.stageA_policyA_rule(ex.ExampleMetrics(), ex.TaskAParameters())
        )

        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, INIT_STAGE)

        ex.MICE_METRICS[0] = ex.ExampleMetrics(theta_1=8)
        tr.evaluate_subjects()
        tr.eject_subject(0)
        tr.evaluate_subjects()
        tr.override_subject_status(
            0, override_stage=stageB, override_policies=stageB.start_policies
        )

        # Validate mouse history
        M0 = SubjectHistory(
            stage_history=[stageA, stageAA, None, None, stageB],
            policy_history=[
                (INIT_STAGE,),
                (ex.stageA_policyA,),
                None,
                None,
                (INIT_STAGE,),
            ],
        )
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)

        # Reset database
        tr.clear_database()


if __name__ == "__main__":
    unittest.main()
