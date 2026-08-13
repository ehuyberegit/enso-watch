"""A git native experiment log: one JSON line per forecast run.

data/experiments.jsonl records every scored run (baselines today, models later),
committed alongside the code, so what worked is versioned with no MLflow. Append
only; the reader replays the whole history. Pure and offline.
"""
import json
import os


def log_experiment(path, record):
    """Append one experiment record as a JSON line."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def read_experiments(path):
    """Return every logged experiment, skipping any torn or blank line."""
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out
