# Getting started

## Installation

``` bash
pip install aind-behavior-curriculum
```

## Documentation

### Understanding a Curriculum

A [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum] is structured as a graph of training [`Stage`][aind_behavior_curriculum.curriculum.Stage]. Each [`Stage`][aind_behavior_curriculum.curriculum.Stage] is associated with a [`Task`][aind_behavior_curriculum.task.Task], which defines a set of configuration parameters via [`TaskParameters`][aind_behavior_curriculum.base.AindBehaviorModelExtra]. It is important to note that [`Stage`][aind_behavior_curriculum.curriculum.Stage] wraps an INSTANCE of [`Task`][aind_behavior_curriculum.task.Task], NOT the class itself. In other words, [`Stage`][aind_behavior_curriculum.curriculum.Stage] is a container for a [`Task`][aind_behavior_curriculum.task.Task] that has been instantiated with a respective [`TaskParameters`][aind_behavior_curriculum.base.AindBehaviorModelExtra].

Stages are connected by [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition], which are directed edges associated with a trigger condition.

[`Stage`][aind_behavior_curriculum.curriculum.Stage] and [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] form the nodes and edges of a [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum] graph, respectively. With this structure alone, a user can define a basic curriculum with the flexibility of defining skip connections and regressions. For nodes with multiple ongoing edges, edges are labelled by priority, set by the user.

![High-Level Curriculum](../assets/high_level_curr_diagram.png)

> *An example curriculum consisting of purely stages and stage transitions. This* [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum] *consists of a skip connection between* [`Stage`][aind_behavior_curriculum.curriculum.Stage] *'StageA* and [`Stage`][aind_behavior_curriculum.curriculum.Stage] *'Graduated'*. [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] *are triggered on a parameter 't2' and the skip transition is ordered before the transition going to* [`Stage`][aind_behavior_curriculum.curriculum.Stage] *StageB.*

Stages are intended to represent 'checkpoint learning objectives', which wrap independent sets of parameters, for example, Stage1 = {P1, P2, P3} -> Stage2 = {P4, P5, P6}.

If a curriculum demands changing the same set of parameters, for example, Stage1 = {P1, P2, P3} -> Stage1' = {P1', P2', P3}, it is a good idea to use PolicyGraphs.

A PolicyGraph is a **parallel programming interface** for changing [`Stage`][aind_behavior_curriculum.curriculum.Stage] parameters.

![Full Curriculum](../examples/example_project/assets/curriculum.svg)

> *An example* [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum] *consisting of* [`Stage`][aind_behavior_curriculum.curriculum.Stage] *and* [`Policy`][aind_behavior_curriculum.curriculum.Policy] *graphs. Left: The high level policy graph. Right: Internal policy graphs.*

![Track Curriculum](../examples/example_project_2/assets/track_curriculum.svg)

> *A 'Track'* [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum]

A PolicyGraph consists of [`Policy`][aind_behavior_curriculum.curriculum.Policy] nodes and [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition] directed edges. Policies are user-defined functions that take in the current Stage [`TaskParameters`][aind_behavior_curriculum.base.AindBehaviorModelExtra] and return the updated Stage [`TaskParameters`][aind_behavior_curriculum.base.AindBehaviorModelExtra]. PolicyTransitions define conditional execution of downstream Policies. Like [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition], [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition] can connect any two arbitrary [`Policy`][aind_behavior_curriculum.curriculum.Policy] and are ordered by priority set by the user. The yellow polices indicate **Start policies**, which are entrypoint(s) into the PolicyGraph specified by the user. Altogether, Policies and PolicyTransitions may be assembled to form arbitrary execution trees and loops.

Notably, PolicyGraph is executed in parallel (execution is done by the Trainer, discussed later). A mouse may occupy multiple policies at once and will traverse down all trigger transitions returning True, similar to current in a circuitboard. While a mouse can only occupy one Stage at a time, a mouse can and will often occupy many active policies. Intuitively, the current state of Stage parameters is the net parameter change of all active policies.

Parallel execution has the benefit of supporting asynchronous parameter updates, which is a more natural way of defining parameter changes. Rather than defining how all stage parameters all change as a group, a policy can instead define updates to individual parameters, which asynchronously trigger on different metrics.

A good example of using PolicyGraphs can be demonstrated in the 'Track' curriculum above.

Imagine 'Track Stage' manages two rig parameters, P1 and P2,and these rig parameters update independently from one another according to different metrics, in this case, metrics m1 and m2 associated with m1_rule and m2_rule respectively. With parallel execution, the most natural way of implementing this situation is with two tracks as shown, where a mouse can progress asynchronously along each parameter track. If PolicyGraph was limited to serial execution, implementing this use case would be possible but more clumsy. m1_rule and m2_rule would have to be combined into a compound policy transition and the left/right policies would need to be combined into a compound policy with additional conditional logic inside checking if m1_rule or m2_rule was triggered. With parallel execution, Policies and PolicyTransitions simplify into atomic operations.

Writing to PolicyGraph is easy. Similar to Curriculum's API for adding, removing, and reordering stages, Stage comes with a simple API for adding, removing, and reordering policies. The structure of the high-level graph and the policy graphs can always be seen using [`export_diagram`][aind_behavior_curriculum.curriculum_utils.export_diagram].

This library has been rigorously tested, and all combinations of StageGraph and PolicyGraph are supported. Here are some more examples of the possibilities. The high-level stage graph are shown to the left and the individual policy graphs are shown to the right. All diagrams have been generated automatically from examples/example_project and examples/example_project_2.

![Tree Curriculum](../examples/example_project_2/assets/tree_curriculum.svg)

> *A 'Tree'* [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum]

![Policy Triangle Curriculum](../examples/example_project_2/assets/policy_triangle_curriculum.svg)

> *A 'Policy Triangle'* [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum]

![Stage Triangle Curriculum](../examples/example_project_2/assets/stage_triangle_curriculum.svg)

> *A 'Stage Triangle'* [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum]

### Understanding the Trainer and TrainerState

The [`Trainer`][aind_behavior_curriculum.trainer.Trainer] holds the evaluation logic to suggest an update for the curriculum.' Conceptually, it achieves this by evaluating the current state of the trainer ([`TrainerState`][aind_behavior_curriculum.trainer.TrainerState]) and a compatible set of [`Metrics`][aind_behavior_curriculum.curriculum.Metrics]. Calling the [`evaluate`][aind_behavior_curriculum.trainer.Trainer.evaluate] method will return a new [`TrainerState`][aind_behavior_curriculum.trainer.TrainerState] with the updated mouse position and associated [`TaskParameters`][aind_behavior_curriculum.base.AindBehaviorModelExtra].

The evaluation algorithm follows the following logic:

> - [`Trainer`][aind_behavior_curriculum.trainer.Trainer] takes the outgoing [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] with the highest priority. If multiple [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] evaluate to True, then the [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] with the highest priority is chosen. Priority is set by the user using [`set_stage_transition_priority`][aind_behavior_curriculum.curriculum.Curriculum.set_stage_transition_priority].
> - [`Trainer`][aind_behavior_curriculum.trainer.Trainer] takes the outgoing [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition] with the highest priority. If multiple [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition] evaluate to True, then the [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition] with the highest priority is chosen. Priority is set by the user using [`set_policy_transition_priority`][aind_behavior_curriculum.curriculum.Stage.set_policy_transition_priority].
> - [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] overrides [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition]. If a [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] and [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition] both evaluate to True, the [`Trainer`][aind_behavior_curriculum.trainer.Trainer] jumps directly to the next [`Stage`][aind_behavior_curriculum.curriculum.Stage].
> - If no transitions are True, the mouse stays in place.
> - For multiple active [`Policy`][aind_behavior_curriculum.curriculum.Policy] that evaluate to True, [`Trainer`][aind_behavior_curriculum.trainer.Trainer] sets the current [`Task`][aind_behavior_curriculum.task.Task] parameters to the net combination of incident [`Policy`][aind_behavior_curriculum.curriculum.Policy].

### Understanding the TrainerServer

!!! warning

    This feature is still under development and it is quite thin at the moment.

The [`TrainerServer`][aind_behavior_curriculum.trainer.TrainerServer] wraps a [`Trainer`][aind_behavior_curriculum.trainer.Trainer] and aims to provide an interface to manage the training of multiple subjects. It currently supports the following features:

1. Registration: This is the entry point where the mice enter the system. Here, the user provides the [`TrainerServer`][aind_behavior_curriculum.trainer.TrainerServer] with a mouse and associates the mouse with a curriculum, a start stage, and start policies as a starting place for evaluation.

2)  Evaluation: For each registered mouse, the [`TrainerServer`][aind_behavior_curriculum.trainer.TrainerServer] looks at the mouse's current position in its hypergraph curriculum. The wrapped [`Trainer`][aind_behavior_curriculum.trainer.Trainer] collects all the current outgoing transitions and checks which evaluate to True. The [`Trainer`][aind_behavior_curriculum.trainer.Trainer] determines the updated hypergraph position and associated [`Task`][aind_behavior_curriculum.task.Task] parameters according to the following simple rules:
3)  Mouse Override: This allows the user to update a mouse's position manually to any position in its curriculum. Future evaluation occurs from this new position. Due to this feature, it is possible to design a [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum] of 'floating stages' and 'floating policies'.
4)  Mouse Eject: This allows the user to remove a mouse from its curriculum entirely. The position of the mouse is recorded as 'None' and stays at 'None' on future evaluation unless the mouse is overrides back onto curriculum.

### Building a Curriculum

For examples of how to build a [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum], please reference examples/example_project and examples/example_project_2 within the project files and their associated diagrams, examples/example_project/diagrams and examples/example_project_2/diagrams.

Tips for building your own [`Curriculum`][aind_behavior_curriculum.curriculum.Curriculum]:

- Focus on one graph at a time. Define all the **Tasks/Stages/Stage Transitions** associated with the higher level graph, and then move onto defining the **Policies/Policy Transitions/Start Policies** associated with each [`Stage`][aind_behavior_curriculum.curriculum.Stage].
- [`Metrics`][aind_behavior_curriculum.curriculum.Metrics] contains all the variables that trigger conditions associated with [`Trainer`][aind_behavior_curriculum.trainer.Trainer] and [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition]. Progressively add to [`Metrics`][aind_behavior_curriculum.curriculum.Metrics] as needed.
- Keep [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] and [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition] simple. A typical transition will only trigger on one metric variable. This makes transitions much easier to name.
- Validate [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] and [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition] priority with the [`export_diagram`][aind_behavior_curriculum.curriculum_utils.export_diagram] utility, which labels edges with its rank. Use [`set_stage_transition_priority`][aind_behavior_curriculum.curriculum.Curriculum.set_stage_transition_priority] and [`set_policy_transition_priority`][aind_behavior_curriculum.curriculum.Stage.set_policy_transition_priority] to reorder priority.

### A word on [`Metrics`][aind_behavior_curriculum.curriculum.Metrics]

[`Metrics`][aind_behavior_curriculum.curriculum.Metrics] used in the curriculum should follow the following general principles:

- [`Metrics`][aind_behavior_curriculum.curriculum.Metrics] should be simple and cheap to calculate. A [`Metrics`][aind_behavior_curriculum.curriculum.Metrics] should represent a collection of variables that can be used to trigger a [`StageTransition`][aind_behavior_curriculum.curriculum.StageTransition] or [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition]. For example, a metric could be 'time spent in stage', 'distance traveled', or 'number of licks'.
- [`Metrics`][aind_behavior_curriculum.curriculum.Metrics] should be calculated as soon as the data is acquired, ideally at the rig.
- While the calculation of these metrics will be largely up to the user, we strongly encourage users to maintain a single method that is used to solely return the populated model. This will make it easier to maintain and update the metrics as needed, without incurring in extra dependencies (e.g. plotting libraries, etc.).

### Building a Trainer

The 4 primary functions of the [`Trainer`][aind_behavior_curriculum.trainer.Trainer] described above are decoupled from any database. To use the [`Trainer`][aind_behavior_curriculum.trainer.Trainer] in practice, the user must define [`load_data`][aind_behavior_curriculum.trainer.TrainerServer.load_data] and [`write_data`][aind_behavior_curriculum.trainer.TrainerServer.write_data] which connect to a user's databases for mice curriculum, mice history, and mice metrics. Please see examples/example_project/trainer.py for an example.

### Declarative vs Imperative syntax

The current version of the library is designed to be able to be used in a declarative or imperative manner.

Under the declarative paradigm, the user defines the `Task`(s) and `Curriculum` in a function-oriented syntax using:

- [`create_task`][aind_behavior_curriculum.task.create_task]
- [`create_curriculum`][aind_behavior_curriculum.curriculum.create_curriculum]

Under a more imperative paradigm, the user can define the `Task` and `Curriculum` objects directly by inheriting from these base classes.

For examples, see the `./examples` directory.

### Inside Allen Institute of Neural Dynamics

Allen Institute of Neural Dynamics offers an internal repository template that automatically uploads the repository's curriculum to a central bucket available here: <https://github.com/AllenNeuralDynamics/aind-behavior-curriculum-template> This way, curriculums can be accessed across rig computers and reused/modified similar to Github commits.

As of (5/9/2024), a Metrics database has yet to be defined, therefore a Trainer cannot be defined.
