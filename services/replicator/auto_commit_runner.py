import time
import logging
from services.db.proposal_manager import ProposalManager
from services.federation_service import FederationService

logger = logging.getLogger("AutoCommitRunner")


class AutoCommitRunner:

    def __init__(self, poll_interval=30):
        self.manager = ProposalManager()
        self.federation = FederationService()
        self.github = self.federation.github  # 🔧 Inherit GitHub client from federation service
        self.poll_interval = poll_interval

    def run(self):
        while True:
            proposals = self.manager.get_all_proposals()  # ✅ Fixed attribute name
            for patch in proposals:
                try:
                    current_file = self.github.get_file(
                        repo_id=patch["repo_id"],
                        file_path=patch["file_path"],
                        branch=patch["branch"]
                    )
                    current = current_file["content"]

                    # 🧠 Noop check using patched_code
                    if current.strip() == patch.get("patched_code", "").strip():
                        logger.info(f"Skipping noop patch for {patch['file_path']}")
                        continue

                    # 🌀 Commit the patch using full payload
                    result = self.federation.commit_patch(patch)
                    logger.info(f"Committed patch: {patch['file_path']} ➝ {result}")

                except Exception as e:
                    logger.error(f"Failed to commit patch: {e}")
            time.sleep(self.poll_interval)
