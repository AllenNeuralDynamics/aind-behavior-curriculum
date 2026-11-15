# Building a curriculum

For complete working curricula see the [examples](../examples/index.md).

## Tips

- **Focus on one graph at a time.** Define the tasks, stages and stage transitions of the high-level graph first, then the policies, policy transitions and start policies of each stage.
- **Add metrics progressively.** [`Metrics`][aind_behavior_curriculum.curriculum.Metrics] holds every variable that triggers a transition; extend it as needed.
- **Keep transitions simple.** A typical transition triggers on a single metric, which makes it much easier to name.
- **Validate priorities visually.** [`export_diagram`][aind_behavior_curriculum.curriculum_utils.export_diagram] labels edges with their rank. Reorder with [`set_stage_transition_priority`][aind_behavior_curriculum.curriculum.Curriculum.set_stage_transition_priority] and [`set_policy_transition_priority`][aind_behavior_curriculum.curriculum.Stage.set_policy_transition_priority].

## Declarative vs imperative syntax

The library can be used in either style.

=== "Declarative"

    Define tasks and curricula in a function-oriented syntax with
    [`create_task`][aind_behavior_curriculum.task.create_task] and
    [`create_curriculum`][aind_behavior_curriculum.curriculum.create_curriculum].

    ```python
    LickTask = create_task(name="Lick Task", task_parameters=LickParameters)
    MyCurriculum = create_curriculum(name="My Curriculum", version="0.1.0", tasks=(LickTask,))
    ```

=== "Imperative"

    Define `Task` and `Curriculum` objects directly by inheriting from the base classes.

See the `examples` directory in the repository for both styles.

## Sharing curricula at AIND

!!! info "Inside the Allen Institute for Neural Dynamics"

    An internal [repository template](https://github.com/AllenNeuralDynamics/aind-behavior-curriculum-template) automatically uploads a repository's curriculum to a central bucket, so curricula can be accessed across rig computers and reused or modified like GitHub commits.
