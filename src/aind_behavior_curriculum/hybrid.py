# Basically, take the existing stage based and
# add graph of serialized policies inside of it.
# Need add an adj list to Stage made-up of new notions of:
# - 'Policy'
# - 'Policy Transition'

# Some criteria:
# - Policies are a separate serialized obj such that
# one can deserialize any arbitrary curriculum can get it running.
# - Stage Transitions/Rules are also separate serialized obj
# for the same reason as above.

# - Trainer evaluation loop must be modified to
# traverse policy transitions and stage transitions.




# Implementation:
# Turns out, you can use the same serializable callable
# object as defined in stage_based.py for both
# Stage_Transition, Policy, and Policy_Transition with the given
# function signature.
# (TODO: YOU ARE HERE)

# For Policy, pass in the Metrics + stage parameters -> out come the modified stage parameters
# |-- seems reasonable to pass in dict of current stage parameters
#     so long as this fact is documented.
# For Policy Transition, pass in Metrics -> T/F
# For Stage Transition, pass in Metrics -> T/F
# Add optional names to the callables above. This helps
# with graph visualization later.

# Add similar/identical API relating to adj graph
# to Stage as well. I do not think the independent
# CurriculumGraph obj. is necessary with this test below.

# Cool, serialization is the hardest step and this
# should be good to go.

# (Write everything out of stage based)



# Simple test shows that pydantic is syntatic sugar +
# validation over a regular dataclass.
from pydantic import Field, BaseModel

class Test(BaseModel):
    field1: str = Field(default='hi')

    def test_method(self):
        print(self.field1)

t = Test(field1='hello')
t.test_method()



# Lets play with callables.

from typing import Any, Callable

from importlib import import_module
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue
from pydantic import Field, GetJsonSchemaHandler

class Rule:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> Callable:
            return cls._deserialize_callable(value)

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(Callable),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(function=cls._serialize_callable),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())

    @staticmethod
    def _deserialize_callable(value: str | Callable) -> Callable:
        if callable(value):
            return value
        else:
            split = value.rsplit(".", 1)
            if len(split) == 0:
                raise ValueError(
                    "Invalid rule value while attempting to deserialize callable. \
                        Got {value}, expected string in the format 'module.function'}"
                )
            elif len(split) == 1:
                return globals()[split]
            else:
                module = import_module(split[0])
                return getattr(module, split[1])

    @staticmethod
    def _serialize_callable(value: str | Callable) -> Callable:
        if isinstance(value, str):
            value = Rule._deserialize_callable(value)
        return value.__module__ + "." + value.__name__








# Interesting
# I was under the impression that all the function logic will live inside the function.
# This serialization only stores a reference to a function inside an installed package which means:
# - Running the curriculum relies on installing the referenced package of stage/policy transitions (this is okay if all the packages are on pypi)
# - This also couples the curriculum to a python import, which is not langauge agnostic.

# Though, this route is fine-- seems like this project will be purely python and its reasonable to expect the curriculum/tasks/transitions to
# be all defined and installed inside the same package.
# Besides, there is no such thing as language agnostic if we are serializing a python function that can only be run in python anyway-- this
# way of writing this is way more readable should you need to implement Trainer in another programming language.

# So basically try this Rule object above and you are done.