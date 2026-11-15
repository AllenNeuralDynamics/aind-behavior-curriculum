# Policies

A *PolicyGraph* is a **parallel programming interface** for changing [`Stage`][aind_behavior_curriculum.curriculum.Stage] parameters without leaving the stage.

<figure markdown>
![Full curriculum](../generated/curriculum.svg)
<figcaption>
A curriculum of stage and policy graphs. Left: the high-level stage graph. Right: the internal policy graphs.
</figcaption>
</figure>

## Anatomy

A policy graph consists of [`Policy`][aind_behavior_curriculum.curriculum.Policy] nodes and [`PolicyTransition`][aind_behavior_curriculum.curriculum.PolicyTransition] directed edges.

- Policies are user-defined functions that take the current stage `TaskParameters` and return the updated parameters.
- Policy transitions define conditional execution of downstream policies. Like stage transitions they can connect any two policies and are ordered by a user-defined priority.
- The yellow policies are **start policies**, the entrypoints into the graph.

Together they can be assembled into arbitrary execution trees and loops.

## Parallel execution

Policy graphs are executed in parallel by the [Trainer](trainer.md). A mouse may occupy **multiple policies at once** and traverses every transition that returns `True`, similar to current in a circuit board. A mouse can only occupy one stage at a time, but often occupies many active policies. The current state of the stage parameters is the net parameter change of all active policies.

This allows asynchronous parameter updates: rather than defining how all parameters change as a group, a policy can update individual parameters that trigger on different metrics.

## Example: the "Track" curriculum

Imagine a stage that manages two rig parameters, `P1` and `P2`, which update independently according to metrics `m1` and `m2` (through `m1_rule` and `m2_rule`). With parallel execution the natural implementation is two tracks, where the mouse progresses asynchronously along each parameter.

<figure markdown>
![Track curriculum](../generated/track_curriculum.svg)
<figcaption>A "Track" curriculum.</figcaption>
</figure>

??? info "Why not serial execution?"

    With serial-only execution this would still be possible but clumsier: `m1_rule` and `m2_rule` would have to be combined into a compound transition, and the left/right policies into a compound policy with extra conditional logic. With parallel execution, policies and transitions stay atomic.

## More shapes

All combinations of stage graphs and policy graphs are supported. These diagrams are generated automatically from `examples/example_project_2` every time the documentation is built.

=== "Tree"

    ![Tree curriculum](../generated/tree_curriculum.svg)

=== "Policy triangle"

    ![Policy triangle curriculum](../generated/policy_triangle_curriculum.svg)

=== "Stage triangle"

    ![Stage triangle curriculum](../generated/stage_triangle_curriculum.svg)
