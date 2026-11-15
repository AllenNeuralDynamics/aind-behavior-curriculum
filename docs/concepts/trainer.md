# Trainer

## Trainer and TrainerState

The [`Trainer`][aind_behavior_curriculum.trainer.Trainer] holds the evaluation logic that suggests an update for a curriculum. It evaluates the current [`TrainerState`][aind_behavior_curriculum.trainer.TrainerState] together with a compatible set of [`Metrics`][aind_behavior_curriculum.curriculum.Metrics]. Calling [`evaluate`][aind_behavior_curriculum.trainer.Trainer.evaluate] returns a new `TrainerState` with the updated mouse position and associated `TaskParameters`.

## Evaluation algorithm

1. The trainer takes the outgoing [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] with the highest priority among those evaluating to `True`. Priority is set with [`set_stage_transition_priority`][aind_behavior_curriculum.curriculum.Curriculum.set_stage_transition_priority].
2. It does the same for outgoing [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition]s, using [`set_policy_transition_priority`][aind_behavior_curriculum.curriculum.Stage.set_policy_transition_priority].
3. A stage transition **overrides** policy transitions: if both fire, the mouse jumps straight to the next stage.
4. If no transition is `True`, the mouse stays in place.
5. For multiple active policies that evaluate to `True`, the trainer sets the task parameters to the net combination of the incident policies.

## TrainerServer

!!! warning

    This feature is still under development and is quite thin at the moment.

The [`TrainerServer`][aind_behavior_curriculum.trainer.TrainerServer] wraps a `Trainer` and provides an interface to manage the training of multiple subjects. It currently supports:

Registration
:   The entry point where mice enter the system. You provide a mouse and associate it with a curriculum, a start stage and start policies.

Evaluation
:   For each registered mouse the server looks at its current position in the curriculum, collects the outgoing transitions, checks which are `True`, and determines the updated position and `Task` parameters using the rules above.

Mouse override
:   Manually move a mouse to any position in its curriculum. Future evaluation starts from there, so curricula of "floating stages" and "floating policies" are possible.

Mouse eject
:   Remove a mouse from its curriculum. Its position is recorded as `None` and stays `None` until overridden back onto a curriculum.
