"""
Work in Progress Curriculum
"""

from collections import defaultdict

class Task:
    """
    Defined in exisiting PR
    """
    pass

class Metric:
    """
    Initalizes a connection to relevant database (referencing some configuration file)
    User extends this with their own metric implementation based on data inside the database.
    """
    pass


class Evaluation:
    """
    Serializable Callable, takes in a list of metrics that is serialized alongside.
    """
    pass


# TODO: De/serialization
class Curriculum:
    def __init__(self) -> None:
        TaskId = int
        # ID tasks on Task.name, a required field.
        # Tasks are allowed to change parameters.
        self.tasks: dict[str, TaskId] = {}
        # Each node references a collection of (edge, destinatation node) associations.
        # The collection is ordered by order of Curriculum API calls.
        self.graph: dict[TaskId, dict[TaskId, Evaluation]] = defaultdict(dict)

    def add_node(self, task: Task):
        self.tasks[task.name] = len(self.tasks)

    def add_connection(self, start_task: str, next_task: str, eval: Evaluation):
        task_id_1 = self.tasks[start_task]
        task_id_2 = self.tasks[next_task]
        self.graph[task_id_1][task_id_2] = eval

    def export_visual(self, ...):
        # Export a visual representation of the curriculum to inspect if it is correct.
        # (See Han's Code)
        pass


def combine_curriculums(curr_1: Curriculum, curr_2: Curriculum) -> Curriculum:
    # Merge Curriculum.tasks.
    # First, make a copy of the curriculums: Curr_A and Curr_B.
    # In the case of a collision (identical task is seen in both curriculums)
    # between Curr_A and Curr_B, assign this task a new id
    # == to len(Curr_A.tasks) + len(Curr_B.tasks) and update
    # the colliding ids in both Curr's.

    # With all collisions resolved, simply merge the two graphs.
    pass


class Principal:
    """
    Initalizes a connection to relevant databases (referencing some configuration file)
    Loads in mouse data and mouse's curriculum.
    Principal has freedom to move mouse in many ways:
        - Proceed with curriculum as normal
        - Move mouse farther ahead or behind in curriculum
        - Remove mouse from curriculum
        - Graduated mouse
    """

    def __init__(self) -> None:
        pass

    def update_mouse_status(self) -> None:
        pass