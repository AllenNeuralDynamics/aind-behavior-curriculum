"""
Example of Curriculum creation
"""

from __future__ import annotations
import json
from pydantic import Field
from typing import Literal, Dict, TypeVar
import aind_behavior_vr_foraging as vrf
import aind_behavior_vr_foraging.task_logic as vrf_task_logic
import aind_behavior_curriculum as abc
import demo


TAindVrForagingTask = TypeVar(
    "TAindVrForagingTask", bound="AindVrForagingTask"
)


class AindVrForagingTaskLogic(
    abc.TaskParameters[TAindVrForagingTask]
):
    describedBy: Literal[
        "https://raw.githubusercontent.com/AllenNeuralDynamics/Aind.Behavior.VrForaging/main/src/DataSchemas/aind_vr_foraging_task.json"
    ] = Field(
        "https://raw.githubusercontent.com/AllenNeuralDynamics/Aind.Behavior.VrForaging/main/src/DataSchemas/aind_vr_foraging_task.json"
    )
    schema_version: Literal[vrf_task_logic.__version__] = (
        vrf_task_logic.__version__
    )
    updaters: Dict[str, vrf_task_logic.NumericalUpdater] = Field(
        default_factory=dict, description="List of numerical updaters"
    )
    environment_statistics: vrf_task_logic.EnvironmentStatistics = Field(
        ..., description="Statistics of the environment"
    )
    task_mode_settings: vrf_task_logic.TaskModeSettings = Field(
        vrf_task_logic.ForagingSettings(),
        description="Settings of the task stage",
        validate_default=True,
    )
    operation_control: vrf_task_logic.OperationControl = Field(
        ..., description="Control of the operation"
    )


class AindVrForagingTask(abc.Task):
    name: Literal["AindVrForagingTask"] = "AindVrForagingTask"
    version: Literal[vrf.__version__] = vrf.__version__
    task_parameters: vrf_task_logic.AindVrForagingTaskLogic = Field(
        default=demo.make(), validate_default=True
    )

# --- METRICS ---

class VrForagingMetrics(abc.Metrics[TAindVrForagingTask]):
    number_of_trials: float
    water_consumed: int
    distance_ran: int


# --- STAGES ---
class StageA(abc.Stage[TAindVrForagingTask]):
    name: Literal["StageA"] = "StageA"
    task: TAindVrForagingTask = Field(
        ..., description="Fill with Task Instance"
    )


class StageB(abc.Stage[TAindVrForagingTask]):
    name: Literal["StageB"] = "StageB"
    task: TAindVrForagingTask = Field(
        ..., description="Fill with Task Instance"
    )

# --- POLICIES ---

def UpdateWaterCallable(metrics: VrForagingMetrics, task_params: AindVrForagingTaskLogic) -> AindVrForagingTaskLogic:
    task_params = task_params.model_copy(deep=True)
    if metrics.number_of_trials > 300:
        task_params.environment_statistics.patches[0].reward_specification.reward_function = vrf_task_logic.ConstantFunction(value=metrics.number_of_trials/100)
    return task_params

class UpdateWater(abc.Policy):
    def __call__(
        self,
        metrics: VrForagingMetrics,
        task_params: AindVrForagingTaskLogic,
    ) -> AindVrForagingTaskLogic:

        return UpdateWaterCallable(metrics, task_params)

# todo
# the previous line should be simply:
#UpdateWater = abc.Policy[TAindVrForagingTask](rule=UpdateWaterCallable)

class UpdateThreshold(abc.Policy):
    def __call__(
        self,
        metrics: VrForagingMetrics,
        task_params: AindVrForagingTaskLogic,
    ) -> AindVrForagingTaskLogic:

        task_params = task_params.model_copy(deep=True)
        if metrics.distance_ran > 10:
            task_params.operation_control.position_control.velocity_threshold += (
                -10
            )

        return task_params


# --- STAGE TRANSITIONS ---
class UpdateStageOnReward(abc.StageTransition):
    def __call__(self, metrics: VrForagingMetrics) -> bool:
        return metrics.water_consumed > 1.5


if __name__ == "__main__":
    # Init Stages
    taskA = AindVrForagingTask()
    taskB = AindVrForagingTask()
    stageA = StageA(task=taskA)
    stageB = StageB(task=taskB)

    #stageA.add_policy_transition(start_policy=UpdateThreshold()) # this crashes serialization because of the nullable type
    stageA.add_policy_transition(abc.INIT_STAGE, UpdateThreshold(), UpdateThreshold())

    #  TODO should be possible to have policies without transitions. I would say that the method should be:

    # Construct the Curriculum
    ex_curr = abc.Curriculum(
        #metrics=VrForagingMetrics()
        name = "example_curriculum",
    )  # TODO why do we have metrics here???
    ex_curr.add_stage_transition(stageA, stageB, UpdateStageOnReward())

    # TODO: TEST THIS

    # Export/Serialize Curriculum Instance:
    with open("examples/vr_for.json", "w") as f:
        json_dict = ex_curr.model_dump()
        json_string = json.dumps(json_dict, indent=4)
        f.write(json_string)

    # Import/De-serialize Instance:
    with open("examples/vr_for.json", "r") as f:
        json_data = f.read()
    curriculum_instance = abc.Curriculum.model_validate_json(json_data)
    print(curriculum_instance)
