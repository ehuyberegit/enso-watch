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


def build_output(oisst_path, climatology_path, oni_path, control_path, fixtures_dir):
    manifest = _load_manifest(fixtures_dir)

    daily = nino34_anomaly(oisst_path, climatology_path)
    oisst_fx = manifest["oisst_daily"]
    daily["provenance"] = provenance_block(
        source=SOURCE_META["oisst_daily"]["source"],
        dataset_version=SOURCE_META["oisst_daily"]["dataset_version"],
        retrieval_url=oisst_fx["source_url"],
        pull_timestamp=oisst_fx["retrieved_at_utc"],
        status=_oisst_file_status(oisst_fx["local_path"]),
    )

    status = oni_status(oni_path)
    control_period, control_anom = _latest_control(control_path)
    status["our_nino34_vs_official"] = round(daily["nino34_anomaly_c"] - control_anom, 3)
    status["control_period"] = control_period
    oni_fx = manifest["cpc_oni_status"]
    status["provenance"] = provenance_block(
        source=SOURCE_META["cpc_oni_status"]["source"],
        dataset_version=SOURCE_META["cpc_oni_status"]["dataset_version"],
        retrieval_url=oni_fx["source_url"],
        pull_timestamp=oni_fx["retrieved_at_utc"],
        status=SOURCE_META["cpc_oni_status"]["status"],
    )

    return {"daily_series": [daily], "status": status}
