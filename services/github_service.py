# FULLY PATCHED GitHubService - No self.owner/repo usage

import os
import requests
import base64
import urllib.parse
from utils.helpers import encode_file_content
from requests.exceptions import RequestException
from dotenv import load_dotenv
import libcst as cst
load_dotenv()
from libcst.metadata import PositionProvider, MetadataWrapper

class GitHubService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.tokens = []

        primary = os.getenv("FEDERATION_GITHUB_TOKEN")
        if primary:
            self.tokens = [primary.strip()]
        else:
            multi = os.getenv("FEDERATION_GITHUB_TOKENS", "")
            self.tokens = [t.strip() for t in multi.split(",") if t.strip()]

        if not self.tokens:
            raise ValueError("No valid GitHub token found in environment.")

        self.current_token_index = 0
        self.token = self.tokens[0]
        self.timeout = 10
        self.headers = self._build_headers(self.token)

    def _build_headers(self, token):
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _rotate_token(self):
        if len(self.tokens) > 1:
            self.current_token_index = (self.current_token_index + 1) % len(self.tokens)
            self.token = self.tokens[self.current_token_index]
            self.headers = self._build_headers(self.token)
            print(f"[GITHUB] Token rotated to index {self.current_token_index}")

    def _request(self, method, url, **kwargs):
        try:
            response = requests.request(method, url, headers=self.headers, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 403:
                if "rate limit" in str(e).lower():
                    print(f"[GITHUB RATE LIMIT] rotating token...")
                    self._rotate_token()
                    return self._request(method, url, **kwargs)
            print(f"[GITHUB API ERROR] {method} {url} failed: {str(e)}")
            raise

    # Replace or extend this method inside GitHubService:

    def get_repo_tree(self, owner, repo, branch, recursive, limit=None, offset=None, path_prefix=None):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive={1 if recursive else 0}"
        tree_data = self._request("GET", url)["tree"]

        if path_prefix:
            tree_data = [item for item in tree_data if item["path"].startswith(path_prefix)]
        if offset is not None and limit is not None:
            tree_data = tree_data[offset:offset+limit]

        return tree_data


    # Replace or extend this method inside GitHubService:

    def get_file(self, owner, repo, file_path, branch, fallback=True, include_meta=False, start_line=1, chunk_size=None):
        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{encoded_path}?ref={branch}"
        print(f"[get_file] 🔍 Request: file_path={file_path}, branch={branch}, start_line={start_line}, chunk_size={chunk_size}, include_meta={include_meta}")

        try:
            file_data = self._request("GET", url)
            size = file_data.get("size", 0)
            print(f"[get_file] 📏 File size: {size} bytes")

            # Use base64-decoded content
            content = base64.b64decode(file_data["content"]).decode("utf-8")
            lines = content.splitlines()
            total_lines = len(lines)

            # DEFAULT FLOW — Enforce 500-line max or chunk_size override
            start_idx = max(start_line - 1, 0)
            limit = chunk_size if chunk_size else 500
            end_idx = min(start_idx + limit, total_lines)

            sliced = "\n".join(lines[start_idx:end_idx])
            more = end_idx < total_lines

            print(f"[get_file] 📦 Slicing {start_line}–{end_idx}, more={more}")
            return {
                "content": sliced,
                "sha": file_data.get("sha"),
                "start_line": start_line,
                "end_line": end_idx,
                "more": more,
                "total_lines": total_lines,
                "encoding": file_data.get("encoding", "utf-8")
            }

        except RequestException as e:
            # Large file fallback
            if "ResponseTooLargeError" in str(e) or "too_large" in str(e).lower():
                print(f"[get_file] 🚨 Triggered fallback due to size — blob fetch")
                content = self.get_large_file_blob(owner, repo, file_path, branch)
                lines = content.splitlines()
                total_lines = len(lines)

                # DEFAULT FLOW — Enforce 500-line max or chunk_size override
                start_idx = max(start_line - 1, 0)
                limit = chunk_size if chunk_size else 500
                end_idx = min(start_idx + limit, total_lines)

                chunk = lines[start_idx:end_idx]
                sliced = "\n".join(chunk)
                more = end_idx < total_lines

                print(f"[get_file] 📦 BLOB slice {start_line}–{end_idx}, more={more}")
                return {
                    "content": sliced,
                    "sha": "blob-only",
                    "start_line": start_line,
                    "end_line": end_idx,
                    "more": more,
                    "total_lines": total_lines,
                    "encoding": "utf-8"
                }

            if fallback and "404" in str(e):
                print(f"⚠️ File {file_path} not found on {branch}, retrying 'main'")
                fallback_url = f"{self.base_url}/repos/{owner}/{repo}/contents/{encoded_path}?ref=main"
                file_data = self._request("GET", fallback_url)
                content = base64.b64decode(file_data["content"]).decode("utf-8")
                return {
                    "content": content,
                    "sha": file_data.get("sha"),
                    "size": file_data.get("size"),
                    "encoding": "utf-8"
                }

            raise



    def get_large_file_blob(self, owner, repo, file_path, branch):
        print(f"[blob] 🔍 Fetching tree for branch: {branch}")
        tree_url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        tree_data = self._request("GET", tree_url)

        blob_entry = next((item for item in tree_data["tree"] if item["path"] == file_path), None)
        if not blob_entry:
            raise ValueError(f"[blob] ❌ File {file_path} not found in branch tree")

        print(f"[blob] 📦 Blob SHA: {blob_entry['sha']}")
        blob_url = f"{self.base_url}/repos/{owner}/{repo}/git/blobs/{blob_entry['sha']}"
        blob_data = self._request("GET", blob_url)

        if blob_data.get("encoding") != "base64":
            raise ValueError(f"[blob] ❌ Unexpected encoding: {blob_data.get('encoding')}")

        decoded = base64.b64decode(blob_data["content"]).decode("utf-8")
        return decoded
    def get_file_chunk(self, owner, repo, file_path, branch, start_line=1, chunk_size=500):
        print(f"[chunk] 🔍 Getting lines {start_line}–{start_line + chunk_size - 1} of {file_path} on {branch}")

        # Use chunk-aware get_file
        result = self.get_file(
            owner, repo, file_path, branch,
            include_meta=False,  # important: do not decode full base64 upfront
            start_line=start_line,
            chunk_size=chunk_size
        )

        # If 'content' is already sliced, use as-is
        return {
            "content": result["content"],
            "start_line": result.get("start_line", start_line),
            "end_line": result.get("end_line", start_line + chunk_size - 1),
            "total_lines": result.get("total_lines", -1),
            "more": result.get("more", False),
            "sha": result.get("sha", None),
            "encoding": result.get("encoding", "utf-8")
        }

    def parse_structure_from_code(code: str) -> list:
        """
        Full structural breakdown of Python code using LibCST.
        Captures classes, functions, imports, assignments, expressions with line numbers.
        Tracks nesting path for classes/functions.
        """
        structure = []

        class StructureVisitor(cst.CSTVisitor):
            METADATA_DEPENDENCIES = (PositionProvider,)

            def __init__(self):
                self.parent_stack = []

            def visit_ClassDef(self, node: cst.ClassDef):
                try:
                    self.parent_stack.append(node.name.value)
                    pos = self.get_metadata(PositionProvider, node)
                    structure.append({
                        "type": "class",
                        "name": node.name.value,
                        "start_line": pos.start.line,
                        "end_line": pos.end.line,
                        "path": list(self.parent_stack)
                    })
                except Exception as e:
                    print(f"[visitor] ⚠️ ClassDef error: {e}")

            def leave_ClassDef(self, node: cst.ClassDef):
                self.parent_stack.pop()

            def visit_FunctionDef(self, node: cst.FunctionDef):
                try:
                    self.parent_stack.append(node.name.value)
                    pos = self.get_metadata(PositionProvider, node)
                    structure.append({
                        "type": "function",
                        "name": node.name.value,
                        "start_line": pos.start.line,
                        "end_line": pos.end.line,
                        "path": list(self.parent_stack)
                    })
                except Exception as e:
                    print(f"[visitor] ⚠️ FunctionDef error: {e}")

            def leave_FunctionDef(self, node: cst.FunctionDef):
                self.parent_stack.pop()

            def visit_Import(self, node: cst.Import):
                try:
                    pos = self.get_metadata(PositionProvider, node)
                    structure.append({
                        "type": "import",
                        "name": None,
                        "start_line": pos.start.line,
                        "end_line": pos.end.line
                    })
                except Exception as e:
                    print(f"[visitor] ⚠️ Import error: {e}")

            def visit_ImportFrom(self, node: cst.ImportFrom):
                try:
                    pos = self.get_metadata(PositionProvider, node)
                    structure.append({
                        "type": "import_from",
                        "name": None,
                        "start_line": pos.start.line,
                        "end_line": pos.end.line
                    })
                except Exception as e:
                    print(f"[visitor] ⚠️ ImportFrom error: {e}")

            def visit_Assign(self, node: cst.Assign):
                try:
                    pos = self.get_metadata(PositionProvider, node)
                    structure.append({
                        "type": "assign",
                        "name": None,
                        "start_line": pos.start.line,
                        "end_line": pos.end.line
                    })
                except Exception as e:
                    print(f"[visitor] ⚠️ Assign error: {e}")

            def visit_Expr(self, node: cst.Expr):
                try:
                    pos = self.get_metadata(PositionProvider, node)
                    structure.append({
                        "type": "expr",
                        "name": None,
                        "start_line": pos.start.line,
                        "end_line": pos.end.line
                    })
                except Exception as e:
                    print(f"[visitor] ⚠️ Expr error: {e}")

        try:
            print(f"[structure-parse] 📦 LibCST scan on {len(code.splitlines())} lines")
            module = cst.parse_module(code)
            wrapper = MetadataWrapper(module)
            wrapper.visit(StructureVisitor())
            print(f"[structure-parse] ✅ Found {len(structure)} structural elements")
        except Exception as e:
            print(f"[structure-parse] ❌ LibCST failure: {e}")
            print(f"[structure-parse] 🔍 Code sample:\n{code[:500]}")
            return []

        return structure

    def parse_structure_for_file(self, owner: str, repo: str, file_path: str, branch: str = "main", update_cache: bool = False):
        print(f"[structure-fetch] 🔍 Fetching file: {file_path} on branch: {branch}")
        code = self.get_large_file_blob(owner, repo, file_path, branch)
        print(f"[structure-fetch] 📏 File length: {len(code.splitlines())} lines")

        structure = []

        class StructureVisitor(cst.CSTVisitor):
            METADATA_DEPENDENCIES = (PositionProvider,)

            def __init__(self):
                self.parent_stack = []

            def visit_ClassDef(self, node: cst.ClassDef):
                try:
                    self.parent_stack.append(node.name.value)
                    pos = self.get_metadata(PositionProvider, node)
                    structure.append({
                        "type": "class",
                        "name": node.name.value,
                        "start_line": pos.start.line,
                        "end_line": pos.end.line,
                        "path": list(self.parent_stack) or [node.name.value]
                    })
                except Exception as e:
                    print(f"[visitor] ⚠️ ClassDef error: {e}")

            def leave_ClassDef(self, node: cst.ClassDef):
                self.parent_stack.pop()

            def visit_FunctionDef(self, node: cst.FunctionDef):
                try:
                    self.parent_stack.append(node.name.value)
                    pos = self.get_metadata(PositionProvider, node)
                    structure.append({
                        "type": "function",
                        "name": node.name.value,
                        "start_line": pos.start.line,
                        "end_line": pos.end.line,
                        "path": list(self.parent_stack) or [node.name.value]
                    })
                except Exception as e:
                    print(f"[visitor] ⚠️ FunctionDef error: {e}")

            def leave_FunctionDef(self, node: cst.FunctionDef):
                self.parent_stack.pop()

        try:
            print(f"[structure-fetch] 🚀 Starting LibCST parse")
            module = cst.parse_module(code)
            wrapper = MetadataWrapper(module)
            wrapper.visit(StructureVisitor())
            # === 🔧 Synthesize anchor regions (BOF, EOF, IMPORTS, TOP) ===
            lines = code.splitlines()
            total_lines = len(lines)

            # BOF: Always line 1
            structure.insert(0, {
                "type": "synthetic",
                "name": "BOF",
                "start_line": 1,
                "end_line": 1
            })

            # EOF: Last line of file
            structure.append({
                "type": "synthetic",
                "name": "EOF",
                "start_line": total_lines,
                "end_line": total_lines
            })

            # IMPORTS
            import_lines = [s["end_line"] for s in structure if s["type"] in ("import", "import_from")]
            if import_lines:
                structure.append({
                    "type": "synthetic",
                    "name": "IMPORTS",
                    "start_line": max(import_lines) + 1,
                    "end_line": max(import_lines) + 1
                })

            # TOP
            body_lines = [s["end_line"] for s in structure if s["type"] in ("class", "function")]
            if body_lines:
                structure.append({
                    "type": "synthetic",
                    "name": "TOP",
                    "start_line": max(body_lines) + 1,
                    "end_line": max(body_lines) + 1
                })
            print(f"[structure-fetch] ✅ Parsed {len(structure)} anchors")
            if update_cache:
                print("[structure-fetch] 💾 Writing anchors to file_structure_cache")
                from services.db.structure_cache_manager import StructureCacheManager
                from datetime import datetime
                from settings import Database

                db = Database()
                structure_manager = StructureCacheManager(db)

                sha = self.get_latest_file_sha(owner, repo, file_path, branch)
                rows = []
                for anchor in structure:
                    rows.append({
                        'repo_id': f"{owner}/{repo}",
                        'branch': branch,
                        'file_path': file_path,
                        'sha': sha,
                        'anchor_path': anchor.get("path", [anchor["name"]]),
                        'anchor_name': anchor["name"],
                        'anchor_type': anchor["type"],
                        'start_line': anchor["start_line"],
                        'end_line': anchor["end_line"],
                        'created_at': datetime.utcnow()
                    })

                conn = db.get_connection()
                try:
                    structure_manager.delete_structure_cache(f"{owner}/{repo}", file_path, branch, sha)
                    structure_manager.insert_structure_rows(rows)
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    db.release_connection(conn)

        except Exception as e:
            print(f"[structure-fetch] ❌ Structure parse error: {e}")
            print(f"[structure-fetch] 🔍 Code snippet:\n{code[:500]}")
            return {
                "file_path": file_path,
                "branch": branch,
                "structure": []
            }
        return {
            "file_path": file_path,
            "branch": branch,
            "structure": structure
        }

    def get_file_history(self, owner, repo, file_path, branch):
        url = f"{self.base_url}/repos/{owner}/{repo}/commits?path={file_path}&sha={branch}"
        return self._request("GET", url)

    def get_branch_sha(self, owner, repo, branch):
        print(f"[DEBUG] get_branch_sha called with: {owner}, {repo}, {branch}")
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        return self._request("GET", url)

    def create_branch(self, owner, repo, new_branch: str, base_branch: str):
        try:
            sha_url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{base_branch}"
            response = requests.get(sha_url, headers=self.headers)
            response.raise_for_status()
            base_sha = response.json()["object"]["sha"]

            url = f"{self.base_url}/repos/{owner}/{repo}/git/refs"
            payload = {
                "ref": f"refs/heads/{new_branch}",
                "sha": base_sha
            }
            post_response = requests.post(url, headers=self.headers, json=payload)
            post_response.raise_for_status()

            return post_response.json()

        except RequestException as e:
            print(f"[❌] create_branch failed: {str(e)}")
            raise

    def multi_file_commit(self, message, files, branch="main"):
        ref_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch}"
        latest_commit_sha = self._request("GET", ref_url)["object"]["sha"]

        commit_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/commits/{latest_commit_sha}"
        base_tree_sha = self._request("GET", commit_url)["tree"]["sha"]

        blobs = []
        for file in files:
            blob_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/blobs"
            blob_resp = self._request("POST", blob_url, json={
                "content": file["content"],
                "encoding": "utf-8"
            })
            blobs.append({
                "path": file["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob_resp["sha"]
            })

        tree_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/trees"
        tree_resp = self._request("POST", tree_url, json={
            "base_tree": base_tree_sha,
            "tree": blobs
        })
        new_tree_sha = tree_resp["sha"]

        commit_create_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/commits"
        commit_create_resp = self._request("POST", commit_create_url, json={
            "message": message,
            "tree": new_tree_sha,
            "parents": [latest_commit_sha]
        })
        new_commit_sha = commit_create_resp["sha"]

        update_ref_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch}"
        self._request("PATCH", update_ref_url, json={"sha": new_commit_sha})

        return {"status": "committed", "commit_sha": new_commit_sha}
    
    def delete_file(self, owner, repo, file_path, message, sha, branch="main"):
        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{encoded_path}"

        body = {
            "message": message,
            "sha": sha,
            "branch": branch
        }

        self._request("DELETE", url, json=body)
        return {"status": "deleted"}

    def create_pull_request(self, owner, repo, source_branch, target_branch, title, body):
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": source_branch,
            "base": target_branch
        }

        print(f"[PR DEBUG] POST to: {url}")
        print(f"[PR PAYLOAD] {payload}")

        return self._request("POST", url, json=payload)

    def get_latest_file_sha(self, owner, repo, file_path: str, branch: str = "main") -> str:
        print(f"[DEBUG] get_latest_file_sha for: {file_path}, branch={branch}")

        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{encoded_path}?ref={branch}"
        r = requests.get(url, headers=self.headers)
        if r.status_code == 200:
            return r.json()["sha"]
        raise Exception(f"Failed to fetch latest SHA: {r.status_code} {r.text}")

    def get_repo_id(self, owner: str, repo: str) -> int:
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        print(f"[DEBUG] Calling GitHub repo: https://api.github.com/repos/{owner}/{repo}")
        print(f"[DEBUG] Headers: {self.headers}")

        if response.status_code != 200:
            raise Exception(f"Failed to fetch repo ID: {response.status_code} {response.text}")
        
        repo_data = response.json()
        if "id" not in repo_data:
            raise Exception(f"GitHub response missing 'id': {repo_data}")
        
        return repo_data["id"]

