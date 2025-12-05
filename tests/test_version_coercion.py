import logging
import unittest
from typing import Literal

from pydantic import Field

from aind_behavior_curriculum.curriculum import Curriculum, create_curriculum
from aind_behavior_curriculum.task import Task

log = logging.getLogger(__name__)


class CurriculumVersionCoercionTestWithLiteral(unittest.TestCase):
    """Tests for version coercion logic in Curriculum models."""

    def setUp(self) -> None:
        class RandomTask(Task):
            name: Literal["RandomTask"] = "RandomTask"
            description: str = "A random task for testing."
            task_parameters: dict[str, str] = Field(default_factory=dict)

        self.task = RandomTask
        self.curr_v1_factory = create_curriculum("TestCurriculum", "1.0.0", [self.task])
        self.curr_v2_factory = create_curriculum("TestCurriculum", "2.0.0", [self.task])

    def test_version_update_forwards_coercion(self):
        CurV1 = self.curr_v1_factory
        CurV2 = self.curr_v2_factory
        v1_instance = CurV1()
        v2_instance = CurV2()
        with self.assertWarns(Warning) as cm:
            v1_as_v2 = CurV2.model_validate_json(v1_instance.model_dump_json())
        warning_msgs = cm.warnings
        self.assertTrue(
            any(
                "Deserialized versioned field 1.0.0, expected 2.0.0." in str(warning.message)
                for warning in warning_msgs
            )
        )
        self.assertEqual(v1_as_v2.version, v2_instance.version)

    def test_version_update_backwards_coercion(self):
        CurV1 = self.curr_v1_factory
        CurV2 = self.curr_v2_factory
        v2_instance = CurV2()
        with self.assertWarns(Warning) as cm:
            v2_as_v1 = CurV1.model_validate_json(v2_instance.model_dump_json())
        warning_msgs = cm.warnings
        self.assertTrue(
            any(
                "Deserialized versioned field 2.0.0, expected 1.0.0." in str(warning.message)
                for warning in warning_msgs
            )
        )
        self.assertEqual(v2_as_v1.version, CurV1().version)


class CurriculumVersionCoercionTestWithoutLiteral(unittest.TestCase):
    """Tests for version coercion logic in Curriculum models."""

    def setUp(self) -> None:
        class RandomTask(Task):
            name: Literal["RandomTask"] = "RandomTask"
            description: str = "A random task for testing."
            task_parameters: dict[str, str] = Field(default_factory=dict)

        class CurriculumV1(Curriculum[RandomTask]):
            version: str = "1.0.0"
            name: str = "TestCurriculumV1"

        class CurriculumV2(Curriculum[RandomTask]):
            version: str = "2.0.0"
            name: str = "TestCurriculumV2"

        self.curr_v1_factory = CurriculumV1
        self.curr_v2_factory = CurriculumV2

    def test_version_update_forwards_coercion(self):
        CurV1 = self.curr_v1_factory
        CurV2 = self.curr_v2_factory
        v1_instance = CurV1()
        v2_instance = CurV2()
        with self.assertWarns(Warning) as cm:
            v1_as_v2 = CurV2.model_validate_json(v1_instance.model_dump_json())
        warning_msgs = cm.warnings
        self.assertTrue(
            any(
                "Deserialized versioned field 1.0.0, expected 2.0.0." in str(warning.message)
                for warning in warning_msgs
            )
        )
        self.assertEqual(v1_as_v2.version, v2_instance.version)

    def test_version_update_backwards_coercion(self):
        CurV1 = self.curr_v1_factory
        CurV2 = self.curr_v2_factory
        v2_instance = CurV2()
        with self.assertWarns(Warning) as cm:
            v2_as_v1 = CurV1.model_validate_json(v2_instance.model_dump_json())
        warning_msgs = cm.warnings
        self.assertTrue(
            any(
                "Deserialized versioned field 2.0.0, expected 1.0.0." in str(warning.message)
                for warning in warning_msgs
            )
        )
        self.assertEqual(v2_as_v1.version, CurV1().version)
