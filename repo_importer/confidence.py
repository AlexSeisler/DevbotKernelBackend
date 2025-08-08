"""
confidence.py — Subsystem tagging scoring logic

This module contains scoring functions that evaluate the likelihood of a file
belonging to a given subsystem, based on path, filename, imports, decorators,
and inline content.

Extracted from the original `tagging_hook.py` for modularization (Phase 3).

Future enhancements:
- Load weights from config or DB for per-project tuning
- Support probabilistic model-based scoring
"""

# Default scoring weights — can be overridden in future
WEIGHT_PATH = 0.25
WEIGHT_FILENAME = 0.20
WEIGHT_IMPORTS = 0.25
WEIGHT_DECORATORS = 0.15
WEIGHT_CONTENT = 0.15

def _score_path(path, subsystem_map):
    scores = {}
    for subsystem, patterns in subsystem_map.get("paths", {}).items():
        for pattern in patterns:
            if pattern.lower() in path.lower():
                scores[subsystem] = scores.get(subsystem, 0) + WEIGHT_PATH
    return scores

def _score_filename(filename, subsystem_map):
    scores = {}
    for subsystem, patterns in subsystem_map.get("filenames", {}).items():
        for pattern in patterns:
            if pattern.lower() in filename.lower():
                scores[subsystem] = scores.get(subsystem, 0) + WEIGHT_FILENAME
    return scores

def _score_imports(imports, subsystem_map):
    scores = {}
    for subsystem, patterns in subsystem_map.get("imports", {}).items():
        for pattern in patterns:
            if any(pattern in imp for imp in imports):
                scores[subsystem] = scores.get(subsystem, 0) + WEIGHT_IMPORTS
    return scores

def _score_decorators(decorators, subsystem_map):
    scores = {}
    for subsystem, patterns in subsystem_map.get("decorators", {}).items():
        for pattern in patterns:
            if any(pattern in dec for dec in decorators):
                scores[subsystem] = scores.get(subsystem, 0) + WEIGHT_DECORATORS
    return scores

def _score_inline_content(lines, subsystem_map):
    scores = {}
    for subsystem, patterns in subsystem_map.get("content", {}).items():
        for pattern in patterns:
            if any(pattern in line for line in lines):
                scores[subsystem] = scores.get(subsystem, 0) + WEIGHT_CONTENT
    return scores

def aggregate_scores(subsystem_map, path, filename, imports, decorators, lines):
    """
    Orchestrate scoring across all heuristics and return a sorted list
    of subsystem candidates based on total score.
    """
    print(f"\n[DEBUG] aggregate_scores called for: {path}")
    print(f"[DEBUG] Filename: {filename}")
    print(f"[DEBUG] Imports: {imports}")
    print(f"[DEBUG] Decorators: {decorators}")
    print(f"[DEBUG] First 5 content lines: {lines[:5]}")

    combined_scores = {}

    # Path rules
    for subsystem, patterns in subsystem_map.get("paths", {}).items():
        for pattern in patterns:
            if pattern.lower() in path.lower():
                combined_scores[subsystem] = combined_scores.get(subsystem, 0) + WEIGHT_PATH
                print(f"[DEBUG] Path match: '{pattern}' for subsystem '{subsystem}' → +{WEIGHT_PATH}")

    # Filename rules
    for subsystem, patterns in subsystem_map.get("filenames", {}).items():
        for pattern in patterns:
            if pattern.lower() in filename.lower():
                combined_scores[subsystem] = combined_scores.get(subsystem, 0) + WEIGHT_FILENAME
                print(f"[DEBUG] Filename match: '{pattern}' for subsystem '{subsystem}' → +{WEIGHT_FILENAME}")

    # Import rules
    for subsystem, patterns in subsystem_map.get("imports", {}).items():
        for pattern in patterns:
            if any(pattern in imp for imp in imports):
                combined_scores[subsystem] = combined_scores.get(subsystem, 0) + WEIGHT_IMPORTS
                print(f"[DEBUG] Import match: '{pattern}' for subsystem '{subsystem}' → +{WEIGHT_IMPORTS}")

    # Decorator rules
    for subsystem, patterns in subsystem_map.get("decorators", {}).items():
        for pattern in patterns:
            if any(pattern in dec for dec in decorators):
                combined_scores[subsystem] = combined_scores.get(subsystem, 0) + WEIGHT_DECORATORS
                print(f"[DEBUG] Decorator match: '{pattern}' for subsystem '{subsystem}' → +{WEIGHT_DECORATORS}")

    # Content rules
    for subsystem, patterns in subsystem_map.get("content", {}).items():
        for pattern in patterns:
            if any(pattern in line for line in lines):
                combined_scores[subsystem] = combined_scores.get(subsystem, 0) + WEIGHT_CONTENT
                print(f"[DEBUG] Content match: '{pattern}' for subsystem '{subsystem}' → +{WEIGHT_CONTENT}")

    print(f"[DEBUG] Final raw scores: {combined_scores}")
    sorted_subsystems = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    print(f"[DEBUG] Sorted subsystems: {sorted_subsystems}")

    return [sub for sub, _ in sorted_subsystems]
