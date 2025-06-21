# CLI TO RUN PATCH DRY-RUN

import sys
import os
import json
import argparse

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.replicator.dry_run_executor import execute_replication_dry_run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dry-run federation patch preview")
    parser.add_argument("plan_file", help="Path to JSON file containing replication plan")
    args = parser.parse_args()

    with open(args.plan_file) as f:
        plan = json.load(f)

    execute_replication_dry_run(plan)
