# Metrics

[`Metrics`][aind_behavior_curriculum.curriculum.Metrics] used in a curriculum should follow a few principles:

- **Simple and cheap.** Metrics are a collection of variables that trigger a [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] or [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition], for example *time spent in stage*, *distance traveled* or *number of licks*.
- **Computed early.** Calculate them as soon as the data is acquired, ideally at the rig.
- **One entry point.** Keep a single method whose only job is to return the populated model. This makes metrics easier to maintain and avoids pulling in extra dependencies such as plotting libraries.

```python
class MyMetrics(Metrics):
    n_trials: int = 0
    n_licks: int = 0
```
