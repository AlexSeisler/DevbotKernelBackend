import time
from services.db.proposal_manager import ProposalManager
from services.federation_service import FederationService


class AutoCommitRunner:
    def __init__(self, poll_interval=30):
        self.manager = ProposalManager()
        self.federation = FederationService()
        self.poll_interval = poll_interval

    def run(self):
        print("[AutoCommitRunner] Starting auto-commit loop...")
        while True:
            try:
                pending = self.manager.get_pending_proposals(risk_class_whitelist=["SAFE", "RENAME"])
                for proposal in pending:
                    proposal_id = proposal["proposal_id"]
                    print(f"[AutoCommitRunner] Attempting commit for patch ID: {proposal_id}")
                    try:
                        result = self.federation.commit_patch(proposal_id)
                        print(f"[AutoCommitRunner] Patch {proposal_id} committed: {result}")
                        self.manager.mark_proposal_committed(proposal_id)
                    except Exception as e:
                        print(f"[AutoCommitRunner] Patch {proposal_id} failed to commit: {str(e)}")
            except Exception as e:
                print(f"[AutoCommitRunner] Loop error: {str(e)}")

            time.sleep(self.poll_interval)
