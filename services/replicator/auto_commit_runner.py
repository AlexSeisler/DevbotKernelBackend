import time
from services.db.proposal_manager import ProposalManager
from services.federation_service import FederationService

class AutoCommitRunner():

    def __init__(self, poll_interval=30):
        self.manager = ProposalManager()
        self.federation = FederationService()
        self.poll_interval = poll_interval

    def run(self):
        print('[AutoCommitRunner] Loop started')
        while True:
            try:
                pending = self.manager.get_pending_proposals(risk_class_whitelist=['SAFE', 'RENAME', 'MANUAL'])
                for proposal in pending:
                    proposal_id = proposal['proposal_id']
                    patches = proposal.get('patches', [])
                    if not patches or not patches[0].get('updated_content', '').strip():
                        continue
                    try:
                        result = self.federation.commit_patch(proposal_id)
                        print(f'[AutoCommitRunner] ✅ Committed patch: {proposal_id}')
                        self.manager.mark_proposal_committed(proposal_id)
                    except Exception as e:
                        print(f'[AutoCommitRunner] ❌ Failed to commit patch {proposal_id}: {e}')
            except Exception as e:
                print(f'[AutoCommitRunner] ⚠️ Loop error: {e}')
            time.sleep(self.poll_interval)
