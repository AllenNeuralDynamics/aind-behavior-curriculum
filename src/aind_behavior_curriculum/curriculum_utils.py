"""
Useful Placeholders when making Curriculums
"""

import os
import subprocess
from pathlib import Path
from typing import Literal, Optional

from jinja2 import Template
from pydantic import Field

from aind_behavior_curriculum.curriculum import Curriculum, Stage
from aind_behavior_curriculum.task import Task, TaskParameters


class Graduated(Task):
    """
    Utility Final Task.
    """

    name: Literal["Graduated"] = "Graduated"
    task_parameters: TaskParameters = Field(default=TaskParameters(), description="Fill w/ Parameter Defaults")


GRADUATED = Stage(name="GRADUATED", task=Graduated())


def export_diagram(curriculum: Curriculum, path: Optional[os.PathLike] = None) -> str:
    """Renders a curriculum to SVG

    Args:
        curriculum (Curriculum): A curriculum to be rendered
        path (Optional[os.PathLike], optional): An optional path to save the SVG asset to.
        If not path is provided, only the str representation of the SVG will be returned.
        Defaults to None.

    Returns:
        str: A literal string representation of the SVG.
    """

    if path:
        path = Path(path)
        if not path.suffix:
            path = path.with_suffix(".svg")
        elif path.suffix != ".svg":
            raise ValueError("Only svg export is allowed.")

    curriculum.validate_curriculum()

    dot_scripts = [_make_curriculum_dot_script(curriculum)]
    stages = curriculum.see_stages()
    for i, stage in enumerate(stages):
        if not (stage.name == "GRADUATED"):
            dot_scripts.append(_make_stage_dot_script(stages.pop(i)))
    if len(stages) > 0:
        dot_scripts.append(_make_stage_dot_script(stages.pop(-1)))

    final_script = "\n".join(dot_scripts)

    # Run graphviz export
    gvpack_command = ["gvpack", "-u"]
    dot_command = ["dot", "-Tsvg"]
    gvpack_process = subprocess.Popen(
        gvpack_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    dot_process = subprocess.Popen(dot_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    gvpack_output, _ = gvpack_process.communicate(input=final_script.encode())

    dot_process_output, _ = dot_process.communicate(input=gvpack_output.decode())
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(dot_process_output)
    return dot_process_output


def _make_stage_dot_script(s: Stage) -> str:
    """
    Stage to dot script conversion.
    """

    template_string = """
        digraph cluster_{{ stage_id }} {
            labelloc="t";
            label={{ stage_name }};

            // Define nodes with increased font visibility
            node [shape=box, style=filled, fontname=Arial, fontsize=12,
            fillcolor=lightblue, color=black];

            // Define nodes
            {% for n in nodes %}
            {{ n }};
            {% endfor %}

            // Define edges
            {% for edge in edges %}
            {{ edge }};
            {% endfor %}
        }
    """
    template = Template(template_string)
    stage_name = '"' + s.name + '"'

    nodes = []
    for node_id, node in s.graph.nodes.items():
        # Add color to start policies
        if node in s.start_policies:
            node_str = f'{node_id} [label="{node.name}", fillcolor="#FFEA00"]'
        else:
            node_str = f'{node_id} [label="{node.name}"]'
        nodes.append(node_str)

    edges = []
    for start_id, edge_list in s.graph.graph.items():
        for i, (edge, dest_id) in enumerate(edge_list):
            # Use 1-indexing for labels
            i = i + 1

            # Edges must be StageTransition or PolicyTransition
            edge_str = f'{start_id} -> {dest_id} [label="({i}) {edge.name}", minlen=2]'
            edges.append(edge_str)

    stage_dot_script = template.render(
        stage_id="".join(s.name.split()),
        stage_name=stage_name,
        nodes=nodes,
        edges=edges,
    )

    return stage_dot_script


def _make_curriculum_dot_script(c: Curriculum) -> str:
    """
    Curriculum to dot script conversion.
    """

    curr_dot_script = """
        digraph cluster_curriculum {
            color="white";
            label={{ curr_name }};
            fontsize=24;

            node [shape=box, style=filled];
            {% for n in nodes %}
            {{ n }}
            {% endfor %}

            {% for edge in edges %}
            {{ edge }};
            {% endfor %}
        }
    """
    template = Template(curr_dot_script)

    # Add curriculum nodes
    nodes = [f'{node_id} [label="{node.name}"]' for node_id, node in c.graph.nodes.items()]

    # Add curriculum edges
    edges = []
    for start_id, edge_list in c.graph.graph.items():
        for i, (edge, dest_id) in enumerate(edge_list):
            # Use 1-indexing for labels
            i = i + 1

            # Edges must be StageTransition or PolicyTransition
            edge_str = f'{start_id} -> {dest_id} [label="({i}) {edge.name}", minlen=2]'
            edges.append(edge_str)

    curriculum_dot_script = template.render(curr_name='"' + c.name + '"', nodes=nodes, edges=edges)

    return curriculum_dot_script


def export_json(curriculum: Curriculum, path: os.PathLike) -> None:
    """
    Export curriculum json to export path
    """

    path = Path(path)
    if not path.suffix == ".json":
        raise ValueError("Please add .json extension to end of json_path.")

    curriculum.validate_curriculum()

    with open(path, "w", encoding="utf-8") as f:
        print(path)
        f.write(curriculum.model_dump_json(indent=3))
