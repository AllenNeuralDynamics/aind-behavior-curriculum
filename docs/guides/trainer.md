# Trainer and persistence

The core functions of the [`Trainer`][aind_behavior_curriculum.trainer.Trainer] are decoupled from any database. To use a [`TrainerServer`][aind_behavior_curriculum.trainer.TrainerServer] in practice, define:

- [`load_data`][aind_behavior_curriculum.trainer.TrainerServer.load_data]
- [`write_data`][aind_behavior_curriculum.trainer.TrainerServer.write_data]

These connect to your own databases for mouse curricula, mouse history and mouse metrics.

??? example "Reference implementation (`examples/example_project/trainer.py`)"

    ```python
    --8<-- "examples/example_project/trainer.py"
    ```

!!! note

    As of 2024-05-09 a metrics database has yet to be defined at AIND, so a production trainer cannot be defined yet.
