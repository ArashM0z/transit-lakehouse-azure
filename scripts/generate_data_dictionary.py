"""Generate docs/data_dictionary.md from the dbt manifest.

Run `dbt docs generate` first to refresh the manifest, then this script.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_PATH = Path("dbt/target/manifest.json")
OUTPUT_PATH = Path("docs/data_dictionary.md")


def render() -> str:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"{MANIFEST_PATH} not found. Run dbt docs generate first.")

    manifest: dict[str, Any] = json.loads(MANIFEST_PATH.read_text())
    nodes: dict[str, Any] = manifest["nodes"]

    layers: dict[str, list[Any]] = {"bronze": [], "silver": [], "gold": [], "marts": []}
    for unique_id, node in nodes.items():
        if node["resource_type"] != "model":
            continue
        for layer in layers:
            if f".{layer}." in unique_id:
                layers[layer].append(node)
                break

    lines: list[str] = [
        "# Data dictionary",
        "",
        "*Auto-generated from `dbt/target/manifest.json` by "
        "`scripts/generate_data_dictionary.py`. Do not edit by hand.*",
        "",
    ]
    for layer in ("bronze", "silver", "gold", "marts"):
        if not layers[layer]:
            continue
        lines.append(f"## {layer.title()}")
        lines.append("")
        for node in sorted(layers[layer], key=lambda n: n["name"]):
            lines.append(f"### `{node['name']}`")
            lines.append("")
            description = (node.get("description") or "").strip() or "_no description_"
            lines.append(description)
            lines.append("")
            if node.get("columns"):
                lines.append("| Column | Description | Tests |")
                lines.append("|---|---|---|")
                for col_name, col in node["columns"].items():
                    desc = (col.get("description") or "").replace("\n", " ").strip()
                    tests = ", ".join(
                        t if isinstance(t, str) else next(iter(t)) for t in col.get("tests", [])
                    )
                    lines.append(f"| `{col_name}` | {desc} | {tests} |")
                lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUTPUT_PATH.write_text(render(), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
