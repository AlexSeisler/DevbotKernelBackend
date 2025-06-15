import json

class TrainingPayloadGenerator:
    def generate_payload(self, pattern_data):
        payloads = []

        for module, examples in pattern_data.items():
            for item in examples:
                prompt = f"Replicate {module} functionality for SaaS kernel.\n"
                prompt += f"Source Repo: {item['repo']}, File: {item['file_path']}\n"
                prompt += f"Function: {item['function']}\nNotes: {item['notes']}\n"

                payload = {
                    "prompt": prompt,
                    "completion": f"Implement {item['function']} into target SaaS Kernel system."
                }
                payloads.append(payload)

        return payloads

    def save_to_jsonl(self, payloads, output_path):
        with open(output_path, 'w') as f:
            for item in payloads:
                f.write(json.dumps(item) + '\n')
