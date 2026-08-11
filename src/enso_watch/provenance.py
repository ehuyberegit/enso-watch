"""Provenance blocks: no number without its source.

Every output record carries a provenance block. A block is complete only when
all required fields are present and non empty. The structural gate refuses any
record with a hole.
"""
REQUIRED_FIELDS = ("source", "dataset_version", "retrieval_url", "pull_timestamp", "status")


def is_complete(block):
    """True when every required field is present and non empty.

    None is a hole, not a value: `str(None)` is truthy, so it is checked for
    identity before any string coercion.
    """
    if not isinstance(block, dict):
        return False
    for field in REQUIRED_FIELDS:
        value = block.get(field)
        if value is None or not str(value).strip():
            return False
    return True


def provenance_block(source, dataset_version, retrieval_url, pull_timestamp, status):
    """Build a validated provenance block, or raise if any field is empty."""
    block = {
        "source": source,
        "dataset_version": dataset_version,
        "retrieval_url": retrieval_url,
        "pull_timestamp": pull_timestamp,
        "status": status,
    }
    if not is_complete(block):
        missing = [
            f for f in REQUIRED_FIELDS
            if block.get(f) is None or not str(block.get(f, "")).strip()
        ]
        raise ValueError(f"incomplete provenance, missing or empty: {missing}")
    return block
