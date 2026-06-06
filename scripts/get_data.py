"""Fetch the processed dataset from a private repo at deploy time.

The raw dataset (activity table, GPS tracks, basemaps) is deliberately kept out
of the public code repository. In production it lives in a separate **private**
repo and is pulled here during the build, authenticated with a token supplied
as the ``DATA_TOKEN`` environment variable (a Render/host secret).

Locally the files already exist under ``data/processed/`` (git-ignored), so this
script is a no-op. It is also a no-op — with a clear warning — when no token is
configured, so a misconfigured deploy fails loudly rather than silently.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

DEST = Path("data/processed")
REQUIRED = ["activities.csv", "tracks.csv", "basemaps.npz"]
DATA_REPO = os.environ.get("DATA_REPO", "PTQ-22/stride-data")


def _have_all() -> bool:
    return all((DEST / f).exists() for f in REQUIRED)


def main() -> int:
    if _have_all():
        print("Processed data already present — nothing to fetch.")
        return 0

    token = os.environ.get("DATA_TOKEN")
    if not token:
        print("WARNING: data missing and DATA_TOKEN not set — cannot fetch dataset.",
              file=sys.stderr)
        return 1

    url = f"https://x-access-token:{token}@github.com/{DATA_REPO}.git"
    tmp = Path("_data_tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    print(f"Cloning private data repo {DATA_REPO} …")
    subprocess.run(["git", "clone", "--depth", "1", url, str(tmp)], check=True)

    DEST.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED:
        src = tmp / name
        if src.exists():
            shutil.copy(src, DEST / name)
            print(f"  + {name}")
    shutil.rmtree(tmp)

    if not _have_all():
        print("ERROR: some data files were missing from the data repo.", file=sys.stderr)
        return 1
    print("Dataset ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
