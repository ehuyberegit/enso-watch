"""Record a captured fixture into fixtures/MANIFEST.json.

Every fixture capture tool calls record() so a frozen fixture always carries its
provenance: source url, retrieval time, byte size, and sha256. A silent swap or
a corrupted fixture is then caught by its sha256, the same false-by-default
discipline the whole project rests on. Upserts by local_path, keeping existing
entries and a stable sorted order.
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "fixtures", "MANIFEST.json")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record(name, local_path, source_url, retrieved_at_utc, note=None):
    """Upsert one fixture's provenance entry, computing its bytes and sha256."""
    abs_path = os.path.join(ROOT, local_path)
    entry = {
        "name": name,
        "source_url": source_url,
        "local_path": local_path,
        "retrieved_at_utc": retrieved_at_utc,
        "content_bytes": os.path.getsize(abs_path),
        "sha256": _sha256(abs_path),
    }
    if note:
        entry["note"] = note

    with open(MANIFEST, encoding="utf-8") as fh:
        doc = json.load(fh)
    fixtures = [f for f in doc.get("fixtures", []) if f.get("local_path") != local_path]
    fixtures.append(entry)
    fixtures.sort(key=lambda f: f["local_path"])
    doc["fixtures"] = fixtures

    tmp = MANIFEST + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, MANIFEST)
    return entry
