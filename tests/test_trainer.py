"""
Trainer Test Suite
"""

import unittest

import aind_behavior_curriculum as abc
import example_project as ex


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
      stageA.add_policy(abc.INIT_STAGE)
      stageB.add_policy(abc.INIT_STAGE)

      curr = ex.MyCurriculum(name="My Curriculum")
      curr.add_stage_transition(stageA, abc.GRADUATED, ex.t2_10)
      curr.add_stage_transition(stageA, stageB, ex.t2_5)
      curr.add_stage_transition(stageB, abc.GRADUATED, ex.t2_10)

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
      stageA.add_policy_transition(abc.INIT_STAGE, ex.stageA_policyB, ex.t1_10)
      stageA.add_policy_transition(abc.INIT_STAGE, ex.stageA_policyA, ex.t1_5)
      stageA.add_policy_transition(ex.stageA_policyA, ex.stageA_policyB, ex.t1_10)

      taskAA = ex.TaskA(task_parameters= \
                        ex.stageA_policyA_rule(ex.ExampleMetrics(),
                                                ex.TaskAParameters()))
      taskAAA = ex.TaskA(task_parameters= \
                        ex.stageA_policyB_rule(ex.ExampleMetrics(),
                                                ex.TaskAParameters()))
      stageAA = ex.StageA(task=taskAA)
      stageAAA = ex.StageA(task=taskAAA)
      curr = ex.MyCurriculum(name="My Curriculum")
      curr.add_stage(stageA)

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
            (stageAA, ex.stageA_policyA), (stageAAA, ex.stageA_policyB)]
      M1 = [(stageA, abc.INIT_STAGE), (stageAA, ex.stageA_policyA),
            (stageAA, ex.stageA_policyA), (stageAAA, ex.stageA_policyB)]
      M2 = [(stageA, abc.INIT_STAGE), (stageAAA, ex.stageA_policyB),
            (stageAAA, ex.stageA_policyB), (stageAAA, ex.stageA_policyB)]

      print(ex.MICE_STAGE_HISTORY[0])
      print(M0)

      self.assertTrue(ex.MICE_STAGE_HISTORY[0] == M0)
      self.assertTrue(ex.MICE_STAGE_HISTORY[1] == M1)
      self.assertTrue(ex.MICE_STAGE_HISTORY[2] == M2)

      # Reset database
      tr.clear_database()


if __name__ == "__main__":
    unittest.main()


# Seems like runtime errors are resolved.
# Need to resolve correctness now.
