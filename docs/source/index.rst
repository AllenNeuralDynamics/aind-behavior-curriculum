Welcome to aind-behavior-curriculum!
===========================================

Installation
============

.. code:: bash

   pip install aind-behavior-curriculum

Documentation
=============

Understanding a Curriculum
--------------------------

A **Curriculum** is structured as a graph of training
**Stages**. Each **Stage** is associated with a **Task**,
which is a set of rig parameters. Stages are connected by
**Stage Transitions**, which are directed edges associated with a
trigger condition.

**Stages** and **Stage Transitions** form the nodes and edges of
a **Curriculum** graph, respectively. With this structure alone, a
user can define a basic curriculum with the flexibility of defining skip
connections and regressions. For nodes with multiple ongoing edges,
edges are labelled by priority, set by the user.

|High-Level Curriculum|

   *An example curriculum consisting of purely stages and stage
   transitions. This* **Curriculum** *consists of a skip connection
   between* **Stage** *'StageA* and **Stage** *'Graduated'*.
   **Stage Transitions** *are triggered on a parameter 't2' and the
   skip transition is ordered before the transition going to*
   **Stage** *StageB.*


:math:`~`

This library also supports **Curriculum** **hypergraphs**.

Conceptually, a user may want to change the rig parameters associated
with a stage, but this set of rig parameters would be unnatural to
classify as a new training stage altogether. In this situation, the user
may define a graph of **Policies** and **Policy Transitions**
within a **Stage**. A **Policy**, changes the task parameters of
a **Stage**, as described above. A **Policy Transition** acts
just like a **Stage Transition**, and defines transitions between
**Policies** on a trigger condition. Like **Stage Transitions**,
**Policy Transitions** can connect any two arbitrary
**Policies** and are ordered by priority set by the user.

|Full Curriculum|
   
   *An example* **Curriculum** *consisting of* **Stage** *and*
   **Policy** *graphs. Left: The high level policy graph. Right:
   Internal policy graphs.*


**Policies** are more nuanced than **Stages**.

Yellow **Policies** in the example indicate '**Start Policies**'. To
initialize the rig parameters of a **Stage**, the user must specify
which **Policy/Policies** in the **Stage** policy graph to start
with.

Unlike **Stages**, a mouse can occupy multiple active
**Policies** within a **Stage**. As described later, the
**Trainer** will record the net combination of rig parameters.

:math:`~`

**Any hypergraph is supported!**

Here are some examples of the possibilities. The high-level stage graph
are shown to the left and the inidividual policy graphs are shown to the
right.

|Tree Curriculum|

   *A 'Tree'* **Curriculum**

|Track Curriculum|

   *A 'Track'* **Curriculum**

|Policy Triangle Curriculum|

   *A 'Policy Triangle'* **Curriculum**

|Stage Triangle Curriculum|

   *A 'Stage Triangle'* **Curriculum**

:math:`~`

Understanding the Trainer
-------------------------

The **Trainer** is responsible for recording where a mouse is in its
associated curriculum hypergraph. The **Trainer** contains 4 primary
functions:

1) Registration: This is the entry point where the mice enter
the system. Here, the user provides the **Trainer** with a mouse and
associates the mouse with a curriculum, a start stage, and start
policies as a starting place for evaluation.

2) Evaluation: For each registered mouse, the **Trainer** looks at
   the mouse's current position in its hypergraph curriculum. The
   **Trainer** collects all the current outgoing transitions and
   checks which evaluate to True. The **Trainer** determines the
   updated hypergraph position and associated **Task** parameters
   according to the following simple rules:

   -  **Trainer** takes the outgoing **Stage Transition** with
      the highest priority. If multiple **Stage Transitions**
      evaluate to True, then the **Stage Transition** with the
      highest priority is chosen. Priority is set by the user.
   -  **Trainer** takes the outgoing **Policy Transition** with
      the highest priority. If multiple **Policy Transitions**
      evaluate to True, then the **Policy Transition** with the
      highest priority is chosen. Priority is set by the user.
   -  **Stage Transitions** override **Policy Transitions**. If
      a **Stage Transition** and **Policy Transition** both
      evaluate to True, the **Trainer** jumps directly to the next
      **Stage** .
   -  If no transitions are True, the mouse stays in place.
   -  For multiple active **Policies** that evaluate to True,
      **Trainer** sets the current **Task** parameters to the
      net combination of incident **Policies**.

3) Mouse Override: This allows the user to update a mouse's position
   manually to any position in its curriculum. Future evaluation occurs
   from this new position. Due to this feature, it is possible to design
   a **Curriculum** of 'floating stages' and 'floating policies'.

4) Mouse Eject: This allows the user to remove a mouse from its
   curriculum entirely. The position of the mouse is recorded as 'None'
   and stays at 'None' on future evaluation unless the mouse is
   overrides back onto curriculum.

Every **Trainer** function keeps a record of mouse history in
**SubjectHistory** which can be referenced or exported for rig
automation and further analysis.

:math:`~`

Building a Curriculum
---------------------

For examples of how to build a **Curriculum**, please reference
examples/example_project and examples/example_project_2 within
the project files and their associated diagrams,
examples/example_project/diagrams and
examples/example_project_2/diagrams.

Tips for building your own **Curriculum**: - Focus on one graph at a
time. Define all the **Tasks/Stages/Stage Transitions** associated
with the higher level graph, and then move onto defining the
**Policies/Policy Transitions** associated with each **Stage**.

-  **Metrics** contains all the variables that trigger conditions
   associated with **Stage Transitions** and
   **Policy Transitions**. Progressively add to **Metrics** as
   needed.

-  Keep **Stage Transitions** and **Policy Transitions** simple.
   A typical transition will only trigger on one metric variable. This
   makes transitions much easier to name.

-  Validate **Stage Transition** and **Policy Transition**
   priority with the Curriculum.export_digram(...) utility, which
   labels edges with its rank. Use
   Curriculum.set_stage_transition_priority(...) and
   Stage.set_policy_transition_priority(...) to reorder priority.

Common mistakes: - Every **Stage** needs a set of start policies,
see Curriculum.set_start_policies(...). If a stage with no policies
is desired, use curriculum_utils.create_empty_stage(...). This is a
common pattern for the final stage of a **Curriculum**, so the
library also offers a prebuilt final stage
curriculum_utils.GRADUATED.

-  The callables in **Policy** and
   **Policy Transition/Stage Transition** have different input
   signatures. Please reference Policy.validate_rule(...) and
   PolicyTransition.validate_rule(...)/StageTransition.validate_rule(...)

:math:`~`

Building a Trainer
------------------

The 4 primary functions of the **Trainer** described above are
decoupled from any database. To use the **Trainer** in practice, the
user must define Trainer.load_data(...) and
Trainer.write_data(...) which connect to a user's databases for mice
curriculum, mice history, and mice metrics. Please see
examples/example_project/trainer.py for an example.

:math:`~`

Inside Allen Institute of Neural Dynamics
-----------------------------------------

Allen Institute of Neural Dynamics offers an internal repository
template that automatically uploads the repository's curriculum to a
central bucket available here:
https://github.com/AllenNeuralDynamics/aind-behavior-curriculum-template
This way, curriculums can be accessed across rig computers and
reused/modified similar to Github commits.

As of (5/9/2024), a Metrics database has yet to be defined, therefore a
Trainer cannot be defined.

.. |High-Level Curriculum| image:: ../../examples/example_project/diagrams/high_level_curr_diagram.png
.. |Full Curriculum| image:: ../../examples/example_project/diagrams/my_curr_diagram.png
.. |Tree Curriculum| image:: ../../examples/example_project_2/diagrams/tree_curr_diagram.png
.. |Track Curriculum| image:: ../../examples/example_project_2/diagrams/track_curr_diagram.png
.. |Policy Triangle Curriculum| image:: ../../examples/example_project_2/diagrams/p_triangle_curr_diagram.png
.. |Stage Triangle Curriculum| image:: ../../examples/example_project_2/diagrams/s_triangle_curr_diagram.png


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
