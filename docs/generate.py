"""Generate documentation assets (diagrams, JSON, schemas) from the example projects.

Outputs go to ``docs/generated`` which is git-ignored and rebuilt in CI before ``zensical build``.
Requires Graphviz (``dot``) on the PATH. Run from the repository root:

    uv run python docs/generate.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "generated"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

from example_project.curriculum import construct_curriculum  # noqa: E402
from example_project_2 import curriculum as ex2  # noqa: E402

from aind_behavior_curriculum.curriculum_utils import export_diagram, export_json  # noqa: E402


def main() -> None:
    """Render every example curriculum to SVG, JSON and JSON schema."""
    OUT.mkdir(parents=True, exist_ok=True)
    curricula = {"curriculum": construct_curriculum()}
    for fn in (
        ex2.construct_track_curriculum,
        ex2.construct_tree_curriculum,
        ex2.construct_policy_triangle_curriculum,
        ex2.construct_stage_triangle_curriculum,
    ):
        curricula[fn.__name__.removeprefix("construct_")] = fn()
    for name, curr in curricula.items():
        export_diagram(curr, OUT / f"{name}.svg")
        export_json(curr, path=OUT / f"{name}.json")
    print(f"Generated {len(curricula)} curricula in {OUT}")


if __name__ == "__main__":
    main()
