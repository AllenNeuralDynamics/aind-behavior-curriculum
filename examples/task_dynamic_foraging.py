"""
Example of Task creation
"""

from typing import Literal
from enum import Enum
import json

from pydantic import Field, ValidationInfo, field_validator

import aind_behavior_curriculum as abc


class DynamicForagingSubTask(str, Enum):
    """Foraging tasks"""

    C1B1 = "Coupled Baiting"
    C0B0 = "Uncoupled Without Baiting"
    C1B0 = "Coupled Without Baiting"
    C0B1 = "Uncoupled Baiting"


class AdvancedBlockMode(str, Enum):
    """Modes for advanced block"""

    OFF = "off"
    NOW = "now"
    ONCE = "once"


class AutoWaterMode(str, Enum):
    """Modes for auto water"""

    NATURAL = "Natural"
    BOTH = "Both"
    HIGH_PRO = "High pro"


class DynamicForagingParas(abc.TaskParameters):
    """Training schema for the dynamic foraging GUI.


    This fully defines a set of training parameters
    that could be used in the GUI.
    For simplicity, let's start with a flat structure and use
    exactly the same names as in the GUI.
    """

    # --- Critical training parameters ---
    SubTask: DynamicForagingSubTask = Field(
        ..., title="Subtask of dynamic foraging"
    )

    # Reward probability
    BaseRewardSum: float = Field(
        ..., title="Sum of p_reward", ge=0.0, le=1.0)
    RewardFamily: int = Field(
        ..., title="Reward family", ge=1
    )  # Should be explicit here
    RewardPairsN: int = Field(
        ..., title="Number of pairs", ge=1
    )  # Should be explicit here

    UncoupledReward: str = Field(
        "0.1,0.3,0.7", title="Uncoupled reward"
    )  # For uncoupled tasks only

    # Randomness
    Randomness: str = Field(
        "Exponential", title="Randomness mode"
    )  # Exponential by default

    # Block length
    BlockMin: int = Field(..., title="Block length (min)", ge=1)
    BlockMax: int = Field(..., title="Block length (max)", ge=1)
    BlockBeta: int = Field(..., title="Block length (beta)", ge=0)
    BlockMinReward: int = Field(
        1, title="Minimal rewards in a block to switch", ge=0
    )

    # Delay period
    DelayMin: float = Field(..., title="Delay period (min) ", ge=0.0)
    DelayMax: float = Field(..., title="Delay period (max) ", ge=0.0)
    DelayBeta: float = Field(..., title="Delay period (beta)", ge=0.0)

    # Reward delay
    RewardDelay: float = Field(..., title="Reward delay (sec)", ge=0.0)

    # Auto water
    AutoReward: bool = Field(..., title="Auto reward switch")
    AutoWaterType: AutoWaterMode = Field(
        AutoWaterMode.NATURAL, title="Auto water mode"
    )
    Multiplier: float = Field(
        ..., title="Multiplier for auto reward", ge=0.0, le=1.0
    )
    Unrewarded: int = Field(
        ..., title="Number of unrewarded trials before auto water", ge=0
    )
    Ignored: int = Field(
        ..., title="Number of ignored trials before auto water", ge=0
    )

    # ITI
    ITIMin: float = Field(..., title="ITI (min)", ge=0.0)
    ITIMax: float = Field(..., title="ITI (max)", ge=0.0)
    ITIBeta: float = Field(..., title="ITI (beta)", ge=0.0)
    ITIIncrease: float = Field(
        0.0, title="ITI increase", ge=0.0
    )  # TODO: not implemented in the GUI??

    # Response time
    ResponseTime: float = Field(..., title="Response time", ge=0.0)
    RewardConsumeTime: float = Field(
        ...,
        title="Reward consume time",
        description="Time of the no-lick period before trial end",
        ge=0.0,
    )
    StopIgnores: int = Field(
        ..., title="Number of ignored trials before stop", ge=0
    )

    # Auto block
    AdvancedBlockAuto: AdvancedBlockMode = Field(..., title="Auto block mode")
    SwitchThr: float = Field(
        ..., title="Switch threshold for auto block", ge=0.0, le=1.0
    )
    PointsInARow: int = Field(
        ..., title="Points in a row for auto block", ge=0
    )

    # Auto stop
    MaxTrial: int = Field(..., title="Maximal number of trials", ge=0)
    MaxTime: int = Field(..., title="Maximal session time (min)", ge=0)

    RightValue_volume: float = Field(
        3.0, title="Right reward size (uL)", ge=0.0
    )
    LeftValue_volume: float = Field(3.0, title="Left reward size (uL)", ge=0.0)



class DynamicForagingTask(abc.Task):
    """
    Example Task
    """

    name: Literal["DynamicForaging"] = "DynamicForaging"
    description: str = Field(default="AIND dynamic foraging task")
    version: abc.SemVerAnnotation = abc.__version__
    # ^Use the version of your task repo package!

    task_parameters: DynamicForagingParas = Field(
        ..., description=DynamicForagingParas.__doc__
    )


if __name__ == "__main__":
    # Create task, optionally add parameters
    ex_parameters = DynamicForagingParas(
        SubTask=DynamicForagingSubTask.C1B1,
        # -- Essentials --
        # p_sum = 0.8, p_ratio = [1:0]
        BaseRewardSum=0.8,
        RewardFamily=3,
        RewardPairsN=1,
        # block = [10, 20, 5]
        BlockMin=10,
        BlockMax=20,
        BlockBeta=5,
        BlockMinReward=0,
        # Small ITI at the beginning to better engage the animal
        ITIMin=1,
        ITIMax=7,
        ITIBeta=3,
        # Add a (fixed) small delay period at the beginning
        DelayMin=0.5,
        DelayMax=0.5,
        DelayBeta=0,
        # Reward delay
        RewardDelay=0,
        # -- Within session automation --
        # Auto water
        AutoReward=True,
        AutoWaterType=AutoWaterMode.NATURAL,
        Unrewarded=5,
        Ignored=5,
        Multiplier=0.5,
        # Auto block
        AdvancedBlockAuto=AdvancedBlockMode.NOW,
        SwitchThr=0.5,
        PointsInARow=5,
        # Auto stop; set StopIgnores to a large number at the beginning
        MaxTrial=1000,
        MaxTime=90,
        StopIgnores=20000,
        # -- Miscs --
        ResponseTime=5,
        RewardConsumeTime=3,  # Very long response time at the beginning
        UncoupledReward="",  # Only valid in uncoupled task
    )

    ex_task = DynamicForagingTask(
        version="1.0.0",
        description=("Phase B in Han's slides "
                     "(block = [10, 20, 5], p_sum = 0.8, p_ratio = [1:0])"),
        task_parameters=ex_parameters,
    )
    print(ex_task)

    # Export/Serialize Task Schema:
    with open("examples/task_schema.json", "w") as f:
        json_dict = DynamicForagingTask.model_json_schema()
        json_string = json.dumps(json_dict, indent=4)
        f.write(json_string)

    # Export/Serialize Instance:
    with open("examples/task_instance.json", "w") as f:
        json_dict = ex_task.model_dump()
        json_string = json.dumps(json_dict, indent=4)
        f.write(json_string)

    # Import/De-serialize Instance:
    with open("examples/task_instance.json", "r") as f:
        json_data = f.read()
    task_instance = DynamicForagingTask.model_validate_json(json_data)
    print(task_instance)
