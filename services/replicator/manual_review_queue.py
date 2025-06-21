import os
import json
from datetime import datetime

REVIEW_QUEUE_DIR = "queues/manual_review_queue"
os.makedirs(REVIEW_QUEUE_DIR, exist_ok=True)

def submit_to_manual_review_queue(file_path, old_content, new_content, base_sha, error_reason):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"patch_{os.path.basename(file_path).replace('/', '_')}_{timestamp}.json"
    payload = {
        "file_path": file_path,
        "base_sha": base_sha,
        "error_reason": error_reason,
        "old_content": old_content,
        "new_content": new_content
    }
    full_path = os.path.join(REVIEW_QUEUE_DIR, filename)
    with open(full_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"[QUEUE] Patch for {file_path} routed to manual review: {full_path}")
