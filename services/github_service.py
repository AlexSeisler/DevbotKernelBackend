...
        body = {
            "message": payload.commit_message,
            "content": content_encoded,
            "branch": payload.branch
        }
        if payload.base_sha:
            body["sha"] = payload.base_sha

        r = requests.put(url, headers=self.headers, json=body)
        ...