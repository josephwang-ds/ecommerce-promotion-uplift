from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "src/download_data.py",
    "src/hillstrom_readout.py",
    "src/segment_uplift.py",
    "src/policy_simulation.py",
    "src/uplift_model.py",
]


def main() -> None:
    for step in STEPS:
        print(f"\n=== Running {step} ===")
        subprocess.run([sys.executable, step], cwd=PROJECT_ROOT, check=True)


if __name__ == "__main__":
    main()
