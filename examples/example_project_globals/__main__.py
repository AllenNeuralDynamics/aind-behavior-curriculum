"""
Demo: two mice with opposite contingencies go through the same curriculum.

Run from the `examples` directory with: python -m example_project_globals
"""

import warnings

from aind_behavior_curriculum import Globals, Trainer

from .curriculum import CounterbalanceGlobals, ShapeReportMetrics, construct_curriculum


def main() -> None:
    curriculum = construct_curriculum()

    # Dry-runs every stage's entry rule against a sample, on top of the usual checks.
    curriculum.validate_curriculum(sample_globals=CounterbalanceGlobals(is_left_circle=True))

    trainer = Trainer(curriculum)
    mice = {
        "mouse_a": trainer.create_enrollment(globals=CounterbalanceGlobals(is_left_circle=True)),
        "mouse_b": trainer.create_enrollment(globals=CounterbalanceGlobals(is_left_circle=False)),
    }

    def show(label: str) -> None:
        print(label)
        for mouse, state in mice.items():
            p = state.stage.task.task_parameters
            print(
                f"  {mouse}: stage={state.stage.name:<9} is_left_circle={p.is_left_circle!s:<5} delay={p.response_delay:.1f}"
            )

    show("Enrolled:")

    # High performance: both mice move to "Withhold". The task resets to that stage's
    # defaults (delay=0.5), but each mouse keeps its own contingency.
    mice = {m: trainer.evaluate(s, ShapeReportMetrics(performance=0.9)) for m, s in mice.items()}
    show("After a stage transition:")

    # Within the stage, policies update the task; the entry rule does not run again.
    for _ in range(2):
        mice = {m: trainer.evaluate(s, ShapeReportMetrics(performance=0.75)) for m, s in mice.items()}
    show("After two sessions in 'Withhold':")

    # Globals are saved with the trainer state. Without the concrete type they load as
    # base Globals (data kept as extra fields) and are re-validated on the next stage entry.
    saved = mice["mouse_b"].model_dump_json()
    restored = trainer.trainer_state_model.model_validate_json(saved)
    print(f"Restored globals: {type(restored.globals).__name__}({restored.globals.model_dump()})")
    print("Restored state equals saved state:", restored == mice["mouse_b"])

    # A subject whose globals do not satisfy every stage's rule is rejected on enrollment.
    try:
        trainer.create_enrollment(globals=Globals())
    except ValueError as e:
        print("Enrollment rejected:", str(e).splitlines()[1])


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main()
