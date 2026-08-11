"""Assemble the V0 JSON output: the daily series and the status record.

Every record carries a provenance block, built from the frozen fixture manifest
so the offline product is itself provenance bearing. our_nino34_vs_official is
the gap between our daily computed anomaly and the latest CPC monthly Nino 3.4
control; control_period names the month that control value came from, so the
consumer can see the comparison may lag the observation by up to a month.
"""
import json
import os

from enso_watch.nino34 import nino34_anomaly
from enso_watch.provenance import provenance_block
from enso_watch.status import oni_status

# Per source metadata that the manifest does not carry.
SOURCE_META = {
    "oisst_daily": {"source": "NOAA OISST", "dataset_version": "v2.1"},
    "cpc_oni_status": {"source": "NOAA CPC ONI", "dataset_version": "ascii v6", "status": "published"},
}


def _load_manifest(fixtures_dir):
    with open(os.path.join(fixtures_dir, "MANIFEST.json")) as handle:
        data = json.load(handle)
    return {entry["name"]: entry for entry in data["fixtures"]}


def _oisst_file_status(local_path):
    return "preliminary" if "_preliminary" in os.path.basename(local_path) else "final"


def _latest_control(control_path):
    """Latest CPC control row: its period (YYYY-MM) and Nino 3.4 anomaly.

    Columns: YR MON NINO1+2 ANOM NINO3 ANOM NINO4 ANOM NINO3.4 ANOM (index 9).
    """
    with open(control_path) as handle:
        rows = [r.split() for r in handle if r.strip() and r.split()[0].isdigit()]
    last = rows[-1]
    period = f"{int(last[0]):04d}-{int(last[1]):02d}"
    return period, float(last[9])


def offline_provenance(fixtures_dir):
    """Build the two provenance blocks from the frozen fixture manifest.

    This is the offline path (the emit command and the tests). The live pull
    builds its own provenance blocks from the real download metadata.
    """
    manifest = _load_manifest(fixtures_dir)
    oisst_fx = manifest["oisst_daily"]
    oni_fx = manifest["cpc_oni_status"]
    oisst_provenance = provenance_block(
        source=SOURCE_META["oisst_daily"]["source"],
        dataset_version=SOURCE_META["oisst_daily"]["dataset_version"],
        retrieval_url=oisst_fx["source_url"],
        pull_timestamp=oisst_fx["retrieved_at_utc"],
        status=_oisst_file_status(oisst_fx["local_path"]),
    )
    oni_provenance = provenance_block(
        source=SOURCE_META["cpc_oni_status"]["source"],
        dataset_version=SOURCE_META["cpc_oni_status"]["dataset_version"],
        retrieval_url=oni_fx["source_url"],
        pull_timestamp=oni_fx["retrieved_at_utc"],
        status=SOURCE_META["cpc_oni_status"]["status"],
    )
    return oisst_provenance, oni_provenance


def build_output(oisst_path, climatology_path, oni_path, control_path,
                 oisst_provenance, oni_provenance):
    """Assemble the V0 product. The transform is identical offline or live; only
    the provenance blocks differ by path, and they are passed in already built."""
    daily = nino34_anomaly(oisst_path, climatology_path)
    daily["provenance"] = oisst_provenance

    status = oni_status(oni_path)
    control_period, control_anom = _latest_control(control_path)
    status["our_nino34_vs_official"] = round(daily["nino34_anomaly_c"] - control_anom, 3)
    status["control_period"] = control_period
    status["provenance"] = oni_provenance

    return {"daily_series": [daily], "status": status}
