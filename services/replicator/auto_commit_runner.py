import time
import logging
from services.db.proposal_manager import ProposalManager
from services.federation_service import FederationService

logger = logging.getLogger("AutoCommitRunner")

class AutoCommitRunner:

    def __init__(self, poll_interval=30):
        self.manager = ProposalManager()
        self.federation = FederationService()
        self.poll_interval = poll_interval

    def run(self):
        print('[AutoCommitRunner] Loop started')
        while True:
            try:
                pending = self.manager.get_pending_proposals(
                    risk_class_whitelist=['SAFE', 'RENAME', 'MANUAL']
                )
                for proposal in pending:
                    try:
                        proposal_id = proposal.get("proposal_id")
                        patches = proposal.get("patches", [])
                        if not patches or not patches[0].get("updated_content", "").strip():
                            logger.warning(f"Skipping empty patch in proposal {proposal_id}")
                            continue

                        noop = False
                        for patch in patches:
                            try:
                                current = self.federation._get_file_content(
                                    owner="AlexSeisler",
                                    repo="DevbotKernelBackend",
                                    path=patch.get("file_path")
                                )
                                if current.strip() == patch.get("updated_content", "").strip():
                                    logger.info(f"No changes detected in {patch.get('file_path')}, skipping patch {proposal_id}")
                                    self.manager.mark_proposal_committed(proposal_id)
                                    noop = True
                                    break
                            except Exception as e:
                                logger.warning(f"[AutoCommitRunner] Could not fetch live file for noop check: {e}")

                        if noop:
                            continue

                        self.federation.commit_patch(proposal_id)
                        self.manager.mark_proposal_committed(proposal_id)
                    except Exception as e:
                        logger.error(f"[AutoCommitRunner] ❌ Failed to commit patch {proposal_id}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"[AutoCommitRunner] 🚨 Loop error: {e}", exc_info=True)
            time.sleep(self.poll_interval)