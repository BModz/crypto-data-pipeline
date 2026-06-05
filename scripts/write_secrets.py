"""
Create .dlt/secrets.toml from the GCP_SERVICE_ACCOUNT_KEY environment variable.

This runs inside GitHub Actions before the pipeline, where secrets.toml
cannot be committed to the repo. Locally you already have secrets.toml,
so this script is only needed in CI.
"""
import json
import os
from pathlib import Path

raw = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
if not raw:
    raise EnvironmentError("GCP_SERVICE_ACCOUNT_KEY environment variable is not set")

key = json.loads(raw)

# The private key comes out of JSON with actual newline characters.
# TOML wants them as literal \n escape sequences.
private_key = key["private_key"].replace("\n", "\\n")

Path(".dlt").mkdir(exist_ok=True)
Path(".dlt/secrets.toml").write_text(
    "[destination.bigquery.credentials]\n"
    f'project_id = "{key["project_id"]}"\n'
    f'client_email = "{key["client_email"]}"\n'
    f'private_key = "{private_key}"\n'
)

print("✓ .dlt/secrets.toml written")
