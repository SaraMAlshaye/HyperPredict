"""Run the whole NHANES data-preparation pipeline in order. Stops at the first failure.

    python data_analysis/run_pipeline.py            # uses already-downloaded raw files
    python data_analysis/run_pipeline.py --force    # re-download raw files first
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["download_nhanes.py", "merge_nhanes.py", "preprocessing.py", "eda.py",
         "validate_dataset.py"]


def main() -> None:
    extra = ["--force"] if "--force" in sys.argv[1:] else []
    for step in STEPS:
        print(f"\n===== {step} =====", flush=True)
        args = [sys.executable, str(HERE / step)] + (extra if step == STEPS[0] else [])
        if subprocess.run(args).returncode != 0:
            sys.exit(f"Pipeline stopped: {step} failed.")
    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
