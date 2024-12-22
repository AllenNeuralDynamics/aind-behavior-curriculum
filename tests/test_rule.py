"""
Curriculum Test Suite
"""

import unittest
from typing import Literal

from pydantic import BaseModel, Field
from aind_behavior_curriculum.curriculum import _Rule, _NonDeserializableCallable, is_non_deserializable_callable, try_materialize_non_deserializable_callable_error
from aind_behavior_curriculum import Metrics, TaskParameters


class RuleTests(unittest.TestCase):

    def setUp(self):

        def rule_update(metrics: Metrics, params: TaskParameters) -> TaskParameters:
            return params

        def duck_type_rule_update(m, p):
            return p

        def not_a_rule_update(metrics: int, params: BaseModel) -> BaseModel:
            return params

        class CustomRule(_Rule[[Metrics, TaskParameters], TaskParameters]):
            pass

        class Container(BaseModel):
            this_new_rule: CustomRule = Field(default=CustomRule(rule_update))

        self.rule_update = rule_update
        self.duck_type_rule_update = duck_type_rule_update
        self.not_a_rule_update = not_a_rule_update
        self.container = Container
        self.custom_rule = CustomRule

    def test_rule_instantiation(self):
        self.container(this_new_rule=self.custom_rule(self.rule_update))

    def test_duck_type_rule_instantiation(self):
        self.container(this_new_rule=self.custom_rule(self.duck_type_rule_update))

    def test_not_a_rule_instantiation(self):
        with self.assertRaises(TypeError):
            self.container(this_new_rule=self.custom_rule(self.not_a_rule_update))


    def test_can_serialize_rule(self):
        container = self.container(this_new_rule=self.custom_rule(self.rule_update))
        container.model_dump()
        container.model_dump_json()

    def test_can_deserialize_rule(self):
        container = self.container(this_new_rule=self.custom_rule(self.rule_update))
        dump = container.model_dump()
        self.assertEqual(dump, container.model_validate(dump))
        json_dump = container.model_dump_json()
        self.assertEqual(json_dump, container.model_validate_json(json_dump))

    def test_is_non_deserializable_callable(self):
        callable_ref = _NonDeserializableCallable("test", Exception("test"))
        with self.assertRaises(RuntimeError):
            callable_ref()
        self.assertFalse(is_non_deserializable_callable(self.custom_rule(self.rule_update)))
        self.assertTrue(is_non_deserializable_callable(callable_ref))

        self.assertIsInstance(try_materialize_non_deserializable_callable_error(callable_ref), Exception)
        self.assertIsNone(try_materialize_non_deserializable_callable_error(self.custom_rule(self.rule_update)))

    def test_can_deserialize_rule(self):
        def rule_update_to_be_deleted(metrics: Metrics, params: TaskParameters) -> TaskParameters:
            return params

        def back_rule_update(metrics: Metrics, params: TaskParameters) -> TaskParameters:
            return params

        container = self.container(this_new_rule=self.custom_rule(rule_update_to_be_deleted))
        dump = container.model_dump()
        json_dump = container.model_dump_json()

        del rule_update_to_be_deleted

        deser = container.model_validate(dump)
        deser_json = container.model_validate_json(json_dump)

        self.assertTrue(is_non_deserializable_callable(deser.this_new_rule.callable))
        self.assertTrue(is_non_deserializable_callable(deser_json.this_new_rule.callable))