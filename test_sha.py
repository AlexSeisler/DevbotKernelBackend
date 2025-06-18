# test_sha.py
from services.github_service import GitHubService

gh = GitHubService()  # This should internally use your stored GitHub token
sha = gh.get_branch_sha("main")
print(f"MAIN BRANCH SHA: {sha}")
