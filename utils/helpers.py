import base64
import hashlib

# ✅ Base64 Encoding Utility (for file commits)
def encode_file_content(content: str) -> str:
    """
    Encode raw string content into Base64 for GitHub API.
    """
    return base64.b64encode(content.encode("utf-8")).decode("utf-8")

# ✅ Optional SHA Utility — content-based SHA calculator (future federation diff engine)
def calculate_sha(content: str) -> str:
    """
    Generate SHA-1 hash of file content as Git uses for blob SHA.
    """
    header = f"blob {len(content)}\0".encode("utf-8")
    store = header + content.encode("utf-8")
    return hashlib.sha1(store).hexdigest()
