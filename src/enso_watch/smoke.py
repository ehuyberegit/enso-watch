"""The live smoke check: reach the real sources and confirm their shape is
unchanged.

It REPORTS, it never gates the build (it is not part of ./run.sh test). Its exit
code signals a monitor: 0 when every source is reachable and its shape holds, non
zero otherwise, so a scheduled run can shout when a public source drifts.
"""
import datetime
import os
import shutil
import sys
import tempfile

from enso_watch import shape, sources


def _check(label, url, dest, validator):
    line = {"label": label, "url": url}
    try:
        if not sources.url_exists(url):
            line.update(reachable=False, ok=False, detail="unreachable (http error)")
            return line
        path = sources.download(url, dest)
        ok, detail = validator(path)
        line.update(reachable=True, ok=ok, detail=detail)
    except Exception as exc:  # noqa: BLE001  report, never crash the check
        line.update(reachable=False, ok=False, detail=f"error: {exc}")
    return line


def smoke(start_date=None):
    start = start_date or datetime.datetime.utcnow().date()
    workdir = tempfile.mkdtemp(prefix="enso-smoke-")
    results = []
    try:
        try:
            day, oisst_u, status = sources.resolve_latest(start)
        except Exception as exc:  # noqa: BLE001  a transient error is a report, not a crash
            day, oisst_u, status = None, None, None
            results.append({"label": "OISST daily", "reachable": False, "ok": False, "detail": f"resolve error: {exc}"})

        if oisst_u:
            line = _check("OISST daily", oisst_u, os.path.join(workdir, "oisst.nc"), shape.check_oisst_shape)
            line["oisst_status"] = status
            line["oisst_date"] = day.isoformat()
            results.append(line)
        elif day is None and not results:
            results.append({"label": "OISST daily", "reachable": False, "ok": False, "detail": "no recent file"})

        results.append(_check("CPC ONI", sources.ONI_URL, os.path.join(workdir, "oni.txt"), shape.check_oni_columns))
        results.append(_check("CPC control", sources.CONTROL_URL, os.path.join(workdir, "control.txt"), shape.check_control_columns))
        return results
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main():
    results = smoke()
    all_ok = True
    for row in results:
        all_ok = all_ok and bool(row.get("ok"))
        mark = "OK" if row.get("ok") else "XX"
        extra = f" [{row.get('oisst_status')}, {row.get('oisst_date')}]" if row.get("oisst_date") else ""
        print(f"{mark}  {row['label']}{extra}: {row.get('detail')}")
    print("smoke:", "all sources reachable, shape unchanged" if all_ok else "a source is unreachable or drifted")
    print("(this reports, it never gates the build)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
