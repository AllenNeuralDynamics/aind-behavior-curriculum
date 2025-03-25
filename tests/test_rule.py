"""
Curriculum Test Suite
"""

import unittest

from pydantic import BaseModel, Field

from aind_behavior_curriculum import Metrics, TaskParameters
from aind_behavior_curriculum.curriculum import (
    _NonDeserializableCallable,
    _Rule,
    is_non_deserializable_callable,
    try_materialize_non_deserializable_callable_error,
)


def rule_update(metrics: Metrics, params: TaskParameters) -> TaskParameters:
    return params


def simple_rule(m, p):
    return m + p


def duck_type_rule_update(m, p):
    return p


def not_a_rule_update(metrics: int, params: BaseModel) -> BaseModel:
    return params


class RuleTests(unittest.TestCase):
    def setUp(self):
        class CustomRule(_Rule[[Metrics, TaskParameters], TaskParameters]):
            pass

        class Container(BaseModel):
            this_new_rule: CustomRule = Field(default=CustomRule(rule_update))

        self.container = Container
        self.custom_rule = CustomRule

    def test_rule_instantiation(self):
        self.container(this_new_rule=self.custom_rule(rule_update))

    def test_duck_type_rule_instantiation(self):
        self.container(this_new_rule=self.custom_rule(duck_type_rule_update))

    def test_not_a_rule_instantiation(self):
        with self.assertRaises(TypeError):
            self.container(this_new_rule=self.custom_rule(not_a_rule_update))

    def test_can_serialize_rule(self):
        container = self.container(this_new_rule=self.custom_rule(rule_update))
        container.model_dump()
        container.model_dump_json()

    def test_can_deserialize_rule(self):
        container = self.container(this_new_rule=self.custom_rule(rule_update))
        dump = container.model_dump()
        self.assertEqual(container, container.model_validate(dump))
        json_dump = container.model_dump_json()
        self.assertEqual(container, container.model_validate_json(json_dump))

    def test_can_deserialize_rule_callable(self):
        container = self.container(this_new_rule=self.custom_rule(simple_rule))
        self.assertEqual(container.this_new_rule.invoke(0, 0), 0)

        dump = container.model_dump()
        deser_dump = container.model_validate(dump)
        self.assertEqual(container, deser_dump)
        self.assertEqual(deser_dump.this_new_rule.invoke(0, 0), 0)

        json_dump = container.model_dump_json()
        deser_json = container.model_validate_json(json_dump)
        self.assertEqual(container, deser_json)
        self.assertEqual(deser_dump.this_new_rule.invoke(0, 0), 0)

    def test_is_non_deserializable_callable(self):
        callable_ref = _NonDeserializableCallable("test", Exception("test"))
        with self.assertRaises(RuntimeError):
            callable_ref()
        self.assertFalse(is_non_deserializable_callable(self.custom_rule(rule_update)))
        self.assertTrue(is_non_deserializable_callable(callable_ref))

        self.assertIsInstance(
            try_materialize_non_deserializable_callable_error(callable_ref),
            Exception,
        )
        self.assertIsNone(try_materialize_non_deserializable_callable_error(self.custom_rule(rule_update)))

    def test_can_deserialize_rule_reference(self):
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

    def test_rule_from_callable(self):
        container = self.container(this_new_rule=rule_update)
        dump = container.model_dump()
        json_dump = container.model_dump_json()

        deser = container.model_validate(dump)
        deser_json = container.model_validate_json(json_dump)

        self.assertEqual(container, deser)
        self.assertEqual(container, deser_json)

    def test_rule_from_not_callable(self):
        with self.assertRaises(TypeError):
            _ = self.container(this_new_rule=not_a_rule_update)


if __name__ == "__main__":
    unittest.main()
