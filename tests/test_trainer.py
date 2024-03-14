"""
Trainer Test Suite
"""

import unittest

import aind_behavior_curriculum as abc
import examples.example_project as ex


class TrainerTests(unittest.TestCase):

    def test_pure_stage_evaluation(self):
        """
        Tests if multiple trajectories through stages
        are recorded correctly in database.
        """

        # Create Stage-only curriculum
        taskA = ex.TaskA(task_parameters=ex.TaskAParameters())
        taskB = ex.TaskB(task_parameters=ex.TaskBParameters())
        stageA = ex.StageA(task=taskA)
        stageB = ex.StageB(task=taskB)
        stageA.add_policy_transition(abc.INIT_STAGE)  # Floating Policy
        stageB.add_policy_transition(abc.INIT_STAGE)  # Floating Policy

        curr = ex.MyCurriculum(name="My Curriculum", metrics=ex.ExampleMetrics())
        curr.add_stage_transition(stageA, abc.GRADUATED, ex.T2_10())
        curr.add_stage_transition(stageA, stageB, ex.T2_5())
        curr.add_stage_transition(stageB, abc.GRADUATED, ex.T2_10())

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, abc.INIT_STAGE)
        tr.register_subject(1, curr, stageA, abc.INIT_STAGE)
        tr.register_subject(2, curr, stageA, abc.INIT_STAGE)

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
        M0 = [(stageA, abc.INIT_STAGE), (stageA, abc.INIT_STAGE),
              (stageB, abc.INIT_STAGE), (abc.GRADUATED, abc.INIT_STAGE)]
        M1 = [(stageA, abc.INIT_STAGE), (stageB, abc.INIT_STAGE),
              (stageB, abc.INIT_STAGE), (abc.GRADUATED, abc.INIT_STAGE)]
        M2 = [(stageA, abc.INIT_STAGE), (abc.GRADUATED, abc.INIT_STAGE),
              (abc.GRADUATED, abc.INIT_STAGE), (abc.GRADUATED, abc.INIT_STAGE)]
        self.assertTrue(ex.MICE_STAGE_HISTORY[0] == M0)
        self.assertTrue(ex.MICE_STAGE_HISTORY[1] == M1)
        self.assertTrue(ex.MICE_STAGE_HISTORY[2] == M2)

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
        stageA = ex.StageA(task=taskA)
        stageA.add_policy_transition(abc.INIT_STAGE, ex.StageA_PolicyB(), ex.T1_10())
        stageA.add_policy_transition(abc.INIT_STAGE, ex.StageA_PolicyA(), ex.T1_5())
        stageA.add_policy_transition(ex.StageA_PolicyA(), ex.StageA_PolicyB(), ex.T1_10())

        taskAA = ex.TaskA(task_parameters= \
                          ex.StageA_PolicyA(ex.ExampleMetrics(),
                                            ex.TaskAParameters()))
        taskAAA = ex.TaskA(task_parameters= \
                          ex.StageA_PolicyB(ex.ExampleMetrics(),
                                            ex.TaskAParameters()))
        stageAA = ex.StageA(task=taskAA)
        stageAAA = ex.StageA(task=taskAAA)
        curr = ex.MyCurriculum(name="My Curriculum", metrics=ex.ExampleMetrics())
        curr.add_stage_transition(stageA)   # Floating Stage

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, abc.INIT_STAGE)
        tr.register_subject(1, curr, stageA, abc.INIT_STAGE)
        tr.register_subject(2, curr, stageA, abc.INIT_STAGE)

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
        M0 = [(stageA, abc.INIT_STAGE), (stageA, abc.INIT_STAGE),
              (stageAA, ex.StageA_PolicyA()), (stageAAA, ex.StageA_PolicyB())]
        M1 = [(stageA, abc.INIT_STAGE), (stageAA, ex.StageA_PolicyA()),
              (stageAA, ex.StageA_PolicyA()), (stageAAA, ex.StageA_PolicyB())]
        M2 = [(stageA, abc.INIT_STAGE), (stageAAA, ex.StageA_PolicyB()),
              (stageAAA, ex.StageA_PolicyB()), (stageAAA, ex.StageA_PolicyB())]

        self.assertTrue(ex.MICE_STAGE_HISTORY[0] == M0)
        self.assertTrue(ex.MICE_STAGE_HISTORY[1] == M1)
        self.assertTrue(ex.MICE_STAGE_HISTORY[2] == M2)

        # Reset database
        tr.clear_database()

    def test_stage_policy_evaluation(self):
        """
        Tests if multiple trajectories through stages and policies
        are recorded correctly in database.
        """
        taskAA = ex.TaskA(task_parameters= \
                          ex.StageA_PolicyA(ex.ExampleMetrics(),
                                            ex.TaskAParameters()))
        taskAAA = ex.TaskA(task_parameters= \
                          ex.StageA_PolicyB(ex.ExampleMetrics(),
                                            ex.TaskAParameters()))
        taskBB = ex.TaskB(task_parameters= \
                          ex.StageB_PolicyA(ex.ExampleMetrics(),
                                            ex.TaskBParameters()))
        taskBBB = ex.TaskB(task_parameters= \
                          ex.StageB_PolicyB(ex.ExampleMetrics(),
                                            ex.TaskBParameters()))
        stageAA = ex.StageA(task=taskAA)
        stageAAA = ex.StageA(task=taskAAA)
        stageBB = ex.StageB(task=taskBB)
        stageBBB = ex.StageB(task=taskBBB)
        curr = ex.construct_curriculum()
        stageA = curr.stages[0]
        stageB = curr.stages[1]

        # Associate mice with curriculum
        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, abc.INIT_STAGE)
        tr.register_subject(1, curr, stageA, abc.INIT_STAGE)
        tr.register_subject(2, curr, stageA, abc.INIT_STAGE)

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
        M0 = [(stageA, abc.INIT_STAGE), (stageAA, ex.StageA_PolicyA()),
              (stageB, abc.INIT_STAGE), (stageBB, ex.StageB_PolicyA()),
              (abc.GRADUATED, abc.INIT_STAGE)]
        M1 = [(stageA, abc.INIT_STAGE), (stageAAA, ex.StageA_PolicyB()),
              (stageB, abc.INIT_STAGE), (stageBBB, ex.StageB_PolicyB()),
              (abc.GRADUATED, abc.INIT_STAGE)]
        M2 = [(stageA, abc.INIT_STAGE), (stageAAA, ex.StageA_PolicyB()),
              (abc.GRADUATED, abc.INIT_STAGE), (abc.GRADUATED, abc.INIT_STAGE),
              (abc.GRADUATED, abc.INIT_STAGE)]

        self.assertTrue(ex.MICE_STAGE_HISTORY[0] == M0)
        self.assertTrue(ex.MICE_STAGE_HISTORY[1] == M1)
        self.assertTrue(ex.MICE_STAGE_HISTORY[2] == M2)

        # Reset database
        tr.clear_database()

    def test_status_override(self):
        """
        Test if status override
        is recorded correctly in database.
        """

        taskAA = ex.TaskA(task_parameters= \
                          ex.StageA_PolicyA(ex.ExampleMetrics(),
                                            ex.TaskAParameters()))
        taskAAA = ex.TaskA(task_parameters= \
                          ex.StageA_PolicyB(ex.ExampleMetrics(),
                                            ex.TaskAParameters()))
        taskBB = ex.TaskB(task_parameters= \
                          ex.StageB_PolicyA(ex.ExampleMetrics(),
                                            ex.TaskBParameters()))
        taskBBB = ex.TaskB(task_parameters= \
                          ex.StageB_PolicyB(ex.ExampleMetrics(),
                                            ex.TaskBParameters()))
        stageAA = ex.StageA(task=taskAA)
        stageAAA = ex.StageA(task=taskAAA)
        stageBB = ex.StageB(task=taskBB)
        stageBBB = ex.StageB(task=taskBBB)
        curr = ex.construct_curriculum()
        stageA = curr.stages[0]
        stageB = curr.stages[1]

        tr = ex.ExampleTrainer()
        tr.register_subject(0, curr, stageA, abc.INIT_STAGE)

        # Override API
        tr.override_subject_status(0,
                                   override_stage=ex.StageB(),
                                   override_policy=ex.StageB_PolicyA())
        tr.override_subject_status(0,
                                   override_stage=ex.StageA(),
                                   override_policy=ex.StageA_PolicyB())
        tr.override_subject_status(0,
                                   override_stage=abc.GRADUATED,
                                   override_policy=abc.INIT_STAGE)

        # Validate mouse history
        M0 = [(stageA, abc.INIT_STAGE), (stageBB, ex.StageB_PolicyA()),
              (stageAAA, ex.StageA_PolicyB()), (abc.GRADUATED, abc.INIT_STAGE)]
        self.assertTrue(ex.MICE_STAGE_HISTORY[0] == M0)

        # Reset database
        tr.clear_database()