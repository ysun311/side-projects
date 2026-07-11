#!/usr/bin/env python3
"""
dev container worker daemon. Polls the S3 job bus for new jobs, runs each through
run_job.py (headless claude pipeline), and syncs status.json + 04-report.md back
to S3 so the Posit Connect frontend can show live progress and the final report.

Runs ONE job at a time (each run is heavy: ~5 min, ~$2). Serial is fine for a
prototype; a production worker would parallelize on a container orchestration platform.

Usage:
  python s3_poller.py [--interval 10] [--once] [--runs-dir runs]
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import bus

HERE = Path(__file__).resolve().parent
RUN_JOB = HERE / "run_job.py"


def find_status(workdir: Path):
    hits = glob.glob(str(workdir / "reports" / "*" / "status.json"))
    if not hits:
        return None
    try:
        return json.loads(Path(hits[0]).read_text())
    except (OSError, json.JSONDecodeError):
        return None


def find_report(workdir: Path):
    hits = glob.glob(str(workdir / "reports" / "*" / "04-report.md"))
    return Path(hits[0]) if hits else None


def process(job_id: str, runs_dir: Path):
    print(f"[poller] processing {job_id}", file=sys.stderr)
    spec = bus.fetch_spec(job_id)
    workdir = runs_dir / job_id
    workdir.mkdir(parents=True, exist_ok=True)
    spec_path = workdir / "job.json"
    spec_path.write_text(json.dumps(spec, indent=2))

    bus.push_status(job_id, {"state": "running", "stage": "starting", "percent": 5})

    cmd = [sys.executable, str(RUN_JOB), "--spec", str(spec_path), "--workdir", str(workdir)]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # Sync local status.json -> S3 while the run proceeds.
    last = None
    while proc.poll() is None:
        st = find_status(workdir)
        if st and st != last:
            bus.push_status(job_id, st)
            last = st
            print(f"[poller] {job_id}: {st.get('state')}/{st.get('stage')} {st.get('percent')}%",
                  file=sys.stderr)
        time.sleep(5)

    # Final sync.
    st = find_status(workdir) or {"state": "error", "stage": "unknown",
                                  "error": "no status.json produced"}
    st["exit_code"] = proc.returncode
    bus.push_status(job_id, st)

    report = find_report(workdir)
    if report:
        bus.push_report(job_id, report.read_text())
        print(f"[poller] {job_id}: uploaded report ({report.stat().st_size} bytes)",
              file=sys.stderr)
    else:
        print(f"[poller] {job_id}: NO report produced (state={st.get('state')})",
              file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="S3 job-bus worker daemon")
    ap.add_argument("--interval", type=int, default=10, help="poll interval seconds")
    ap.add_argument("--once", action="store_true", help="process at most one job then exit")
    ap.add_argument("--runs-dir", default=str(HERE / "runs"))
    args = ap.parse_args()

    os.environ.setdefault("IS_SANDBOX", "1")  # belt-and-suspenders for run_job.py
    runs_dir = Path(args.runs_dir).resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)
    print(f"[poller] watching s3://{bus.BUCKET}/{bus.PREFIX}/  runs_dir={runs_dir}",
          file=sys.stderr)

    while True:
        try:
            jobs = bus.open_jobs()
        except Exception as e:  # transient S3 error shouldn't kill the daemon
            print(f"[poller] list error: {e}", file=sys.stderr)
            time.sleep(args.interval)
            continue

        for job_id in jobs:
            if bus.claim(job_id):
                try:
                    process(job_id, runs_dir)
                except Exception as e:
                    print(f"[poller] {job_id} failed: {e}", file=sys.stderr)
                    bus.push_status(job_id, {"state": "error", "stage": "worker",
                                            "percent": 0, "error": str(e)})
                if args.once:
                    return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
