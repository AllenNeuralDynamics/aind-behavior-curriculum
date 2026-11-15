# Examples

Every diagram and JSON export on this page is **generated at build time** from the code in the repository's [`examples/`](https://github.com/AllenNeuralDynamics/aind-behavior-curriculum/tree/main/examples) folder, so it always matches the code shown.

## Example project

A curriculum with tasks, metrics, stage transitions and policy graphs. [:material-github: View on GitHub](https://github.com/AllenNeuralDynamics/aind-behavior-curriculum/blob/main/examples/example_project/curriculum.py){ .md-button }

=== "Diagram"

    ![Example curriculum](../generated/curriculum.svg)

=== "Source"

    ```python title="examples/example_project/curriculum.py"
    --8<-- "examples/example_project/curriculum.py"
    ```

=== "Exported JSON"

    ```json title="curriculum.json"
    --8<-- "docs/generated/curriculum.json"
    ```

## Example project 2: shapes

Four small curricula exercising different graph shapes. [:material-github: View on GitHub](https://github.com/AllenNeuralDynamics/aind-behavior-curriculum/blob/main/examples/example_project_2/curriculum.py){ .md-button }

=== "Track"

    ![Track](../generated/track_curriculum.svg)

=== "Tree"

    ![Tree](../generated/tree_curriculum.svg)

=== "Policy triangle"

    ![Policy triangle](../generated/policy_triangle_curriculum.svg)

=== "Stage triangle"

    ![Stage triangle](../generated/stage_triangle_curriculum.svg)

??? example "Source: `examples/example_project_2/curriculum.py`"

    ```python
    --8<-- "examples/example_project_2/curriculum.py"
    ```

## Trainer

A `TrainerServer` with `load_data` and `write_data` implemented. [:material-github: View on GitHub](https://github.com/AllenNeuralDynamics/aind-behavior-curriculum/blob/main/examples/example_project/trainer.py){ .md-button }

??? example "Source: `examples/example_project/trainer.py`"

    ```python
    --8<-- "examples/example_project/trainer.py"
    ```
