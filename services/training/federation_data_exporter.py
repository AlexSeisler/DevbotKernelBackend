from services.db.federation_graph_manager import FederationGraphManager

class FederationDataExporter:
    def __init__(self):
        self.graph_manager = FederationGraphManager()

    def export_full_graph(self):
        return self.graph_manager.query_graph()
