"""
Trainer Test Suite
"""

import unittest

import example_project as ex

from aind_behavior_curriculum import (
    create_empty_stage,
    INIT_STAGE,
    GRADUATED,
    Stage,
    SubjectHistory
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
        stageA = create_empty_stage(Stage(name='StageA', task=taskA))
        stageB = create_empty_stage(Stage(name='StageB', task=taskB))

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
            stage_history=[stageA,
                           stageA,
                           stageB,
                           GRADUATED],
            policy_history=[(INIT_STAGE,),
                            (INIT_STAGE,),
                            (INIT_STAGE,),
                            (INIT_STAGE,)])

        M1 = SubjectHistory(
            stage_history=[stageA,
                           stageB,
                           stageB,
                           GRADUATED],
            policy_history=[(INIT_STAGE,),
                            (INIT_STAGE,),
                            (INIT_STAGE,),
                            (INIT_STAGE,)])

        M2 = SubjectHistory(
            stage_history=[stageA,
                           GRADUATED,
                           GRADUATED,
                           GRADUATED],
            policy_history=[(INIT_STAGE,),
                            (INIT_STAGE,),
                            (INIT_STAGE,),
                            (INIT_STAGE,)])

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
        stageA = Stage(name='StageA', task=taskA)
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
            stage_history=[stageA,
                           stageA,
                           stageAA,
                           stageAAA],
            policy_history=[(INIT_STAGE,),
                            (INIT_STAGE,),
                            (ex.stageA_policyA,),
                            (ex.stageA_policyB,)])

        M1 = SubjectHistory(
            stage_history=[stageA,
                           stageAA,
                           stageAA,
                           stageAAA],
            policy_history=[(INIT_STAGE,),
                            (ex.stageA_policyA,),
                            (ex.stageA_policyA,),
                            (ex.stageA_policyB,)])

        M2 = SubjectHistory(
            stage_history=[stageA,
                           stageAAA,
                           stageAAA,
                           stageAAA],
            policy_history=[(INIT_STAGE,),
                            (ex.stageA_policyB,),
                            (ex.stageA_policyB,),
                            (ex.stageA_policyB,)])

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
            stage_history=[stageA,
                           stageAA,
                           stageB,
                           stageBB,
                           GRADUATED],
            policy_history=[(INIT_STAGE,),
                            (ex.stageA_policyA,),
                            (INIT_STAGE,),
                            (ex.stageB_policyA,),
                            (INIT_STAGE,)])

        M1 = SubjectHistory(
            stage_history=[stageA,
                           stageAAA,
                           stageB,
                           stageBBB,
                           GRADUATED],
            policy_history=[(INIT_STAGE,),
                            (ex.stageA_policyB,),
                            (INIT_STAGE,),
                            (ex.stageB_policyB,),
                            (INIT_STAGE,)])

        M2 = SubjectHistory(
            stage_history=[stageA,
                           stageAAA,
                           GRADUATED,
                           GRADUATED,
                           GRADUATED],
            policy_history=[(INIT_STAGE,),
                            (ex.stageA_policyB,),
                            (INIT_STAGE,),
                            (INIT_STAGE,),
                            (INIT_STAGE,)])

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
            stage_history=[stageA,
                           stageBB,
                           stageAAA,
                           GRADUATED],
            policy_history=[(INIT_STAGE,),
                            (ex.stageB_policyA,),
                            (ex.stageA_policyB,),
                            (INIT_STAGE,)])
        self.assertTrue(ex.MICE_SUBJECT_HISTORY[0] == M0)

        # Reset database
        tr.clear_database()



if __name__ == "__main__":
    unittest.main()
