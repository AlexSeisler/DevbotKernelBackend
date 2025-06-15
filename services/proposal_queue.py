import uuid

class ProposalQueueManager:
    def __init__(self):
        self.queue = {}

    def submit_proposal(self, proposal):
        proposal_id = str(uuid.uuid4())
        proposal["proposal_id"] = proposal_id
        proposal["status"] = "pending"
        self.queue[proposal_id] = proposal
        return proposal_id

    def list_proposals(self):
        return list(self.queue.values())

    def get_proposal(self, proposal_id):
        return self.queue.get(proposal_id)

    def approve_proposal(self, proposal_id):
        proposal = self.get_proposal(proposal_id)
        if proposal:
            proposal["status"] = "approved"
            return proposal
        else:
            raise Exception("Proposal not found")

    def reject_proposal(self, proposal_id):
        proposal = self.get_proposal(proposal_id)
        if proposal:
            proposal["status"] = "rejected"
            return proposal
        else:
            raise Exception("Proposal not found")

    def remove_proposal(self, proposal_id):
        if proposal_id in self.queue:
            del self.queue[proposal_id]
