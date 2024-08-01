# aind-behavior-curriculum

[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)
![Interrogate](https://img.shields.io/badge/interrogate-100.0%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?logo=codecov)
![Python](https://img.shields.io/badge/python->=3.11-blue?logo=python)

A core problem in mice training is accurately keeping track of each mouse's training stage and accurately setting the corresponding rig parameters. As the number of behavior studies, research assistants, and mice increase, manual tracking and parameter input is prone to human error. This library provides a flexible framework for defining mice curriculum enabling mouse training to be automated.

## Installation
```bash
pip install aind-behavior-curriculum
```

## Documentation

### Understanding a Curriculum

A **``Curriculum``** is structured as a graph of training **``Stages``**.
Each **``Stage``**  is associated with a **``Task``**, which is a set of rig parameters.
Stages are connected by **``Stage Transitions``**, which are directed edges associated with a trigger condition.

**``Stages``** and **``Stage Transitions``** form the nodes and edges of a **``Curriculum``** graph, respectively.
With this structure alone, a user can define a basic curriculum with the flexibility of defining skip connections and regressions. For nodes with multiple ongoing edges, edges are labelled by priority, set by the user.


| ![High-Level Curriculum](./examples/example_project/diagrams/high_level_curr_diagram.png "Title") |
|:--:|
|*An example curriculum consisting of purely stages and stage transitions. This **``Curriculum``** consists of a skip connection between **``Stage``** 'StageA' and **``Stage``** 'Graduated'. **``Stage Transitions``** are triggered on a parameter 't2' and the skip transition is ordered before the transition going to **``Stage``** StageB.* |

$~$

Stages are intended to represent 'checkpoint learning objectives', which wrap independent sets of parameters,
for example, Stage1 = {P1, P2, P3} -> Stage2 = {P4, P5, P6}.

If a curriculum demands changing the same set of parameters,
for example, Stage1 = {P1, P2, P3} -> Stage1' = {P1', P2', P3}, it is a good idea to use PolicyGraphs.

A PolicyGraph is a **parallel programming interface** for changing **``Stage``** parameters.


| ![Full Curriculum](./examples/example_project/diagrams/my_curr_diagram.png "Title") |
|:--:|
|*An example **``Curriculum``** consisting of **``Stage``** and  **``Policy``** graphs. Left: The high level policy graph. Right: Internal policy graphs.* |


| ![Track Curriculum](./examples/example_project_2/diagrams/track_curr_diagram.png "Title") |
|:--:|
|*A 'Train Track' **``Curriculum``*** |

$~$

A PolicyGraph consists of **``Policy``** nodes and **``PolicyTransition``** directed edges.
Policies are user-defined functions that take in the current Stage **``TaskParameters``** and return the updated Stage **``TaskParameters``**.
PolicyTransitions define conditional execution of downstream Policies. Like **``StageTransition``**, **``PolicyTransition``**
can connect any two arbitrary **``Policy``** and are ordered by priority set by the user.
The yellow polices indicate **Start policies**, which are entrypoint(s) into the PolicyGraph specified by the user.
Altogether, Policies and PolicyTransitions may be assembled to form arbitrary execution trees and loops.

Notably, PolicyGraph is executed in parallel (execution is done by the Trainer, discussed later).
A mouse may occupy multiple policies at once and will traverse down all trigger transitions returning True, similar to current in a circuitboard.
While a mouse can only occupy one Stage at a time, a mouse can and will often occupy many active policies.
Intuitively, the current state of Stage parameters is the net parameter change of all active policies.

Parallel execution has the benefit of supporting asynchronous parameter updates, which is a more natural way of defining parameter changes.
Rather than defining how all stage parameters all change as a group, a policy can instead define updates to individual parameters, which asynchronously trigger on different metrics.

A good example of using PolicyGraphs can be demonstrated in the 'Track' curriculum above.

Imagine 'Track Stage' manages two rig parameters, P1 and P2,and these rig parameters update independently from one another
according to different metrics, in this case, metrics m1 and m2 associated with m1_rule and m2_rule respectively.
With parallel execution, the most natural way of implementing this situation is with two tracks as shown, where a mouse can progress asynchronously along each parameter track.
If PolicyGraph was limited to serial execution, implementing this use case would be possible but more clumsy.
m1_rule and m2_rule would have to be combined into a compound policy transition and the left/right policies
would need to be combined into a compound policy with additional conditional logic inside checking if m1_rule or m2_rule was triggered.
With parallel execution, Policies and PolicyTransitions simplify into atomic operations.

Writing to PolicyGraph is easy.
Similar to Curriculum's API for adding, removing, and reordering stages,
Stage comes with a simple API for adding, removing, and reordering policies.
The structure of the high-level graph and the policy graphs can always be seen using **``Curriculum.export_diagram(...)``**.

This library has been rigorously tested, and all combinations of StageGraph and PolicyGraph are supported.
Here are some more examples of the possibilities.
The high-level stage graph are shown to the left and the individual policy graphs are shown to the right.
All diagrams have been generated automatically from examples/example_project and examples/example_project_2.

| ![Tree Curriculum](./examples/example_project_2/diagrams/tree_curr_diagram.png "Title") |
|:--:|
|*A 'Tree' **``Curriculum``*** |

| ![Policy Triangle Curriculum](./examples/example_project_2/diagrams/p_triangle_curr_diagram.png "Title") |
|:--:|
|*A 'Policy Triangle' **``Curriculum``*** |

| ![Stage Triangle Curriculum](./examples/example_project_2/diagrams/s_triangle_curr_diagram.png "Title") |
|:--:|
|*A 'Stage Triangle' **``Curriculum``*** |

$~$

### Understanding the Trainer

The **``Trainer``** is responsible for recording where a mouse is in its associated curriculum hypergraph. The **``Trainer``** contains 4 primary functions:
1) Registration:
	This is the entry point where the mice enter the system.
	Here, the user provides the **``Trainer``** with a mouse and associates the mouse with a curriculum, a start stage, and start policies as a starting place for evaluation.

2) Evaluation:
	For each registered mouse, the **``Trainer``** looks at the mouse's current position in its hypergraph curriculum. The **``Trainer``** collects all the current outgoing transitions and checks which evaluate to True. The **``Trainer``** determines the updated hypergraph position and associated **``Task``** parameters according to the following simple rules:
	- **``Trainer``** takes the outgoing **``Stage Transition``** with the highest priority. If multiple **``Stage Transitions``** evaluate to True, then the **``Stage Transition``** with the highest priority is chosen. Priority is set by the user.
	- **``Trainer``** takes the outgoing **``Policy Transition``** with the highest priority. If multiple **``Policy Transitions``** evaluate to True, then the **``Policy Transition``** with the highest priority is chosen. Priority is set by the user.
	- **``Stage Transitions``** override **``Policy Transitions``**. If a **``Stage Transition``** and **``Policy Transition``** both evaluate to True, the **``Trainer``** jumps directly to the next **``Stage``** .
	- If no transitions are True, the mouse stays in place.
	- For multiple active **``Policies``** that evaluate to True, **``Trainer``** sets the current  **``Task``**  parameters to the net combination of incident **``Policies``**.

3) Mouse Override:
	This allows the user to update a mouse's position manually to any position in its curriculum. Future evaluation occurs from this new position. Due to this feature, it is possible to design a **``Curriculum``** of 'floating stages' and 'floating policies'.

4) Mouse Eject:
	 This allows the user to remove a mouse from its curriculum entirely. The position of the mouse is recorded as 'None' and stays at 'None' on future evaluation unless the mouse is overrides back onto curriculum.

Every **``Trainer``**  function keeps a record of mouse history in **``SubjectHistory``** which can be referenced or exported for rig automation and further analysis.

$~$

### Building a Curriculum

For examples of how to build a **``Curriculum``**, please reference ``examples/example_project`` and ``examples/example_project_2`` within the project files and their associated diagrams, ``examples/example_project/diagrams`` and ``examples/example_project_2/diagrams``.

Tips for building your own **``Curriculum``**:
- Focus on one graph at a time. Define all the **``Tasks/Stages/Stage Transitions``** associated with the higher level graph, and then move onto defining the **``Policies/Policy Transitions``** associated with each **``Stage``**.

- **``Metrics``** contains all the variables that trigger conditions associated with **``Stage Transitions``** and **``Policy Transitions``**. Progressively add to **``Metrics``** as needed.

- Keep **``Stage Transitions``** and **``Policy Transitions``** simple. A typical transition will only trigger on one metric variable. This makes transitions much easier to name.

-  Validate **``Stage Transition``** and **``Policy Transition``** priority with the ``Curriculum.export_digram(...)`` utility, which labels edges with its rank. Use ``Curriculum.set_stage_transition_priority(...)`` and ``Stage.set_policy_transition_priority(...)`` to reorder priority.


Common mistakes:
- Every **``Stage``** needs a set of start policies, see ``Curriculum.set_start_policies(...)``. If a stage with no policies is desired, use ``curriculum_utils.create_empty_stage(...)``. This is a common pattern for the final stage of a **``Curriculum``**, so the library also offers a prebuilt final stage ``curriculum_utils.GRADUATED``.

- The callables in **``Policy``** and **``Policy Transition/Stage Transition``** have different input signatures. Please reference ``Policy.validate_rule(...)`` and ``PolicyTransition.validate_rule(...)``/``StageTransition.validate_rule(...)``

$~$

### Building a Trainer

The 4 primary functions of the **``Trainer``** described above are decoupled from any database. To use the **``Trainer``** in practice, the user must define ``Trainer.load_data(...)`` and ``Trainer.write_data(...)`` which connect to a user's databases for mice curriculum, mice history, and mice metrics. Please see ``examples/example_project/trainer.py`` for an example.

$~$

### Inside Allen Institute of Neural Dynamics

Allen Institute of Neural Dynamics offers an internal repository template that automatically uploads the repository's curriculum to a central bucket available here: https://github.com/AllenNeuralDynamics/aind-behavior-curriculum-template
This way, curriculums can be accessed across rig computers and reused/modified similar to Github commits.

As of (5/9/2024), a Metrics database has yet to be defined, therefore a Trainer cannot be defined.
