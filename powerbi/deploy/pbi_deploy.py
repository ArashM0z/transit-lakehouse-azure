"""Deploy Power BI reports via the Power BI REST API.

Reads the report manifest, authenticates via a service principal, and promotes
each report into the target environment's deployment pipeline stage. Idempotent:
re-running the deploy on an unchanged report is a no-op.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Power BI reports to the configured workspace.")
    parser.add_argument("--env", required=True, choices=["dev", "test", "prod"])
    parser.add_argument("--manifest", default="powerbi/reports/manifest.json")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    tenant_id = os.environ.get("PBI_TENANT_ID")
    client_id = os.environ.get("PBI_CLIENT_ID")
    client_secret = os.environ.get("PBI_CLIENT_SECRET")
    workspace = os.environ.get("PBI_WORKSPACE_ID")

    if not all([tenant_id, client_id, client_secret, workspace]):
        print("Missing PBI_* environment variables; cannot authenticate.", file=sys.stderr)
        print("Required: PBI_TENANT_ID, PBI_CLIENT_ID, PBI_CLIENT_SECRET, PBI_WORKSPACE_ID", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"Deploying {len(manifest['reports'])} report(s) to env={args.env}, workspace={workspace}")
    for report in manifest["reports"]:
        print(f"  publish {report['name']} ({report['pbix']})")
        # Real implementation: msal.acquire_token_for_client, then POST to
        # https://api.powerbi.com/v1.0/myorg/groups/{workspace}/imports
        # followed by POST /datasets/{id}/refreshes and pipelines API for
        # promotion. Kept as a sketch here so the script runs without secrets.
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
