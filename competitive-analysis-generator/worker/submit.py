#!/usr/bin/env python3
"""Submit a job to the S3 bus (mimics the frontend) and optionally poll for result.

Usage:
  python submit.py --spec job.example.json [--poll]
  python submit.py --status <job_id>
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
import uuid
from pathlib import Path

import bus


def make_job_id(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-") or "analysis"
    return f"{dt.date.today().isoformat()}-{slug}-{uuid.uuid4().hex[:6]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec")
    ap.add_argument("--poll", action="store_true")
    ap.add_argument("--status", metavar="JOB_ID")
    args = ap.parse_args()

    if args.status:
        print(json.dumps(bus.get_status(args.status), indent=2))
        return

    spec = json.loads(Path(args.spec).read_text())
    job_id = make_job_id(spec["topic"])
    bus.submit_job(job_id, spec)
    print(f"submitted job_id = {job_id}")

    if not args.poll:
        return
    while True:
        st = bus.get_status(job_id) or {}
        print(f"  {st.get('state')}/{st.get('stage')} {st.get('percent')}%", file=sys.stderr)
        if st.get("state") in ("complete", "error"):
            break
        time.sleep(8)
    if st.get("state") == "complete":
        rpt = bus.get_report(job_id)
        print(f"\n=== report ({len(rpt or '')} chars) ===\n{(rpt or '')[:800]}")


if __name__ == "__main__":
    main()
