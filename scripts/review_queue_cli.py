# CLI TOOL TO REVIEW & APPROVE PATCHES FROM QUEUE

import os
import json
import argparse
from services.federation_service import FederationService
from models.federation_schemas import CommitPatchRequest

QUEUE_DIR = "queues/manual_review_queue"

def list_queued_patches():
    files = sorted(os.listdir(QUEUE_DIR))
    for idx, fname in enumerate(files):
        print(f"[{idx}] {fname}")


def show_patch(index):
    files = sorted(os.listdir(QUEUE_DIR))
    target = os.path.join(QUEUE_DIR, files[int(index)])
    with open(target) as f:
        patch = json.load(f)
    print(json.dumps(patch, indent=2))


def approve_patch(index, repo_id, branch, commit_message):
    files = sorted(os.listdir(QUEUE_DIR))
    target = os.path.join(QUEUE_DIR, files[int(index)])
    with open(target) as f:
        patch = json.load(f)

    payload = CommitPatchRequest(
        repo_id=repo_id,
        branch=branch,
        file_path=patch["file_path"],
        base_sha=patch["base_sha"],
        updated_content=patch["new_content"],
        commit_message=commit_message
    )

    result = FederationService().commit_patch(payload)
    print("✅ Patch committed:", result)
    os.remove(target)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manual Patch Review CLI")
    parser.add_argument("action", choices=["list", "show", "approve"])
    parser.add_argument("index", nargs="?", help="Index of patch to show or approve")
    parser.add_argument("--repo", help="Target repo ID")
    parser.add_argument("--branch", help="Target branch")
    parser.add_argument("--message", help="Commit message")
    args = parser.parse_args()

    if args.action == "list":
        list_queued_patches()
    elif args.action == "show":
        show_patch(args.index)
    elif args.action == "approve":
        if not (args.repo and args.branch and args.message):
            print("--repo, --branch, and --message are required for approve")
        else:
            approve_patch(args.index, args.repo, args.branch, args.message)
