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
    combined_scores = {}

    # Merge all scoring results
    for score_dict in [
        _score_path(path, subsystem_map),
        _score_filename(filename, subsystem_map),
        _score_imports(imports, subsystem_map),
        _score_decorators(decorators, subsystem_map),
        _score_inline_content(lines, subsystem_map)
    ]:
        for subsystem, score in score_dict.items():
            combined_scores[subsystem] = combined_scores.get(subsystem, 0) + score

    # Sort by score descending
    sorted_subsystems = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    return [sub for sub, _ in sorted_subsystems]