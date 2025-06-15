from collections import defaultdict

class ArchitecturePatternAnalyzer:
    def analyze_graph(self, graph_data):
        pattern_clusters = defaultdict(list)

        for node in graph_data:
            functional_area = self.infer_function_area(node["name"], node["file_path"])
            pattern_clusters[functional_area].append({
                "repo": node["repo_id"],
                "file_path": node["file_path"],
                "function": node["name"],
                "linked_to": node["cross_linked_to"],
                "notes": node["notes"]
            })

        return dict(pattern_clusters)

    def infer_function_area(self, name, file_path):
        # EXTREMELY simple initial categorizer (GPT agents will refine)
        if "booking" in file_path.lower() or "reserve" in name.lower():
            return "BookingModule"
        elif "user" in file_path.lower() or "auth" in name.lower():
            return "UserAuthModule"
        else:
            return "General"
